"""Flask REST API for a simple travel planner."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, g, request, url_for
from flask_restful import Api, Resource

import external_api
import services
from auth import auth_required, hash_password
from db import connect, initialize_database
from validation import (
    ValidationError,
    json_object,
    validate_city,
    validate_limit,
    validate_positive_query_int,
    validate_trip_create,
    validate_trip_id,
    validate_trip_patch,
    validate_password,
    validate_username,
)


DEFAULT_DATABASE = Path(__file__).with_name("travel.db")


def create_app(db_path: str | Path = DEFAULT_DATABASE) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["DATABASE"] = str(db_path)
    api = Api(app)

    initialize_database(app.config["DATABASE"])

    @app.before_request
    def open_database() -> None:
        """Open the SQLite connection for the current request."""
        g.db = connect(app.config["DATABASE"])

    @app.teardown_request
    def close_database(exception: BaseException | None) -> None:
        """Close the SQLite connection after the current request."""
        connection = g.pop("db", None)

        if connection is not None:
            connection.close()

    @app.errorhandler(404)
    def handle_404(error: Any) -> tuple[dict[str, str], int]:
        """Return JSON for resources and routes that do not exist."""
        return {"message": "Resource not found"}, 404

    @app.errorhandler(405)
    def handle_405(error: Any) -> tuple[dict[str, str], int]:
        """Return JSON when an HTTP method is not supported."""
        return {"message": "HTTP method not allowed"}, 405

    @app.errorhandler(500)
    def handle_500(error: Any) -> tuple[dict[str, str], int]:
        """Return a JSON response for unexpected server errors."""
        return {"message": "Internal server error"}, 500

    class Register(Resource):
        """HTTP resource for registering users."""

        def post(
            self,
        ) -> tuple[dict[str, Any], int] | tuple[
            dict[str, Any], int, dict[str, str]
        ]:
            """Register a new user."""
            try:
                data = json_object(request)

                unknown = set(data) - {"username", "password"}

                if unknown:
                    names = ", ".join(sorted(unknown))
                    raise ValidationError(
                        f"Unrecognized field(s): {names}"
                    )

                if "username" not in data or "password" not in data:
                    raise ValidationError(
                        "username and password are required"
                    )

                username = validate_username(data["username"])
                password = validate_password(data["password"])

            except ValidationError as exc:
                return {"message": str(exc)}, 400

            try:
                user = services.create_user(
                    g.db,
                    username,
                    hash_password(password),
                )

            except sqlite3.IntegrityError:
                return {
                    "message": "Username is already registered"
                }, 409

            location = url_for(
                "user_registration",
                _external=True,
            )

            return user, 201, {"Location": location}

    class TripList(Resource):
        """HTTP resource for listing and creating trips."""

        @auth_required
        def get(
            self,
        ) -> tuple[list[dict[str, Any]], int] | tuple[
            dict[str, str], int
        ]:
            """List trips with optional filtering and pagination."""
            try:
                destination = request.args.get("destination")

                if destination is not None:
                    destination = validate_city(destination)

                limit = validate_limit(
                    request.args.get("limit")
                )

                offset = validate_positive_query_int(
                    request.args.get("offset"),
                    "offset",
                    0,
                )

            except ValidationError as exc:
                return {"message": str(exc)}, 400

            trips = services.list_trips(
                g.db,
                destination,
                limit,
                offset,
            )

            return trips, 200

        @auth_required
        def post(
            self,
        ) -> tuple[dict[str, Any], int, dict[str, str]] | tuple[
            dict[str, str], int
        ]:
            """Create a new trip owned by the authenticated user."""
            try:
                data = json_object(request)
                trip_data = validate_trip_create(data)

            except ValidationError as exc:
                return {"message": str(exc)}, 400

            created_at = datetime.now(timezone.utc).isoformat()

            trip = services.create_trip(
                g.db,
                g.user_id,
                trip_data["destination"],
                trip_data["start_date"],
                trip_data["days"],
                created_at,
            )

            location = url_for(
                "trip_detail",
                trip_id=trip["id"],
                _external=True,
            )

            return trip, 201, {"Location": location}

    class TripDetail(Resource):
        """HTTP resource for one trip."""

        @auth_required
        def get(
            self,
            trip_id: int,
        ) -> tuple[dict[str, Any], int]:
            """Return one trip by ID."""
            try:
                validate_trip_id(trip_id)
                trip = services.get_trip(g.db, trip_id)

            except ValidationError as exc:
                return {"message": str(exc)}, 400

            except services.NotFound:
                return {"message": "Trip not found"}, 404

            return trip, 200

        @auth_required
        def patch(
            self,
            trip_id: int,
        ) -> tuple[dict[str, Any], int]:
            """Update only the fields supplied in the request body."""
            try:
                validate_trip_id(trip_id)

                data = json_object(request)

                changes = validate_trip_patch(data)

                trip = services.update_trip(
                    g.db,
                    g.user_id,
                    trip_id,
                    changes,
                )

            except ValidationError as exc:
                return {"message": str(exc)}, 400

            except services.NotFound:
                return {"message": "Trip not found"}, 404

            except services.Forbidden:
                return {
                    "message": "You do not own this trip"
                }, 403

            return trip, 200

        @auth_required
        def delete(
            self,
            trip_id: int,
        ) -> tuple[dict[str, str], int]:
            """Delete a trip owned by the authenticated user."""
            try:
                validate_trip_id(trip_id)

                services.delete_trip(
                    g.db,
                    g.user_id,
                    trip_id,
                )

            except ValidationError as exc:
                return {"message": str(exc)}, 400

            except services.NotFound:
                return {"message": "Trip not found"}, 404

            except services.Forbidden:
                return {
                    "message": "You do not own this trip"
                }, 403

            return {"message": "Trip deleted"}, 200

    class Weather(Resource):
        """HTTP resource that uses two Open-Meteo endpoints."""

        def get(self) -> tuple[dict[str, Any], int]:
            """Get current weather using a city query parameter."""
            try:
                city = validate_city(
                    request.args.get("city")
                )

            except ValidationError as exc:
                return {"message": str(exc)}, 400

            return self._get_weather(city)

        def post(self) -> tuple[dict[str, Any], int]:
            """Get current weather using a JSON city field."""
            try:
                data = json_object(request)

                if set(data) != {"city"}:
                    unknown = set(data) - {"city"}

                    if unknown:
                        names = ", ".join(sorted(unknown))

                        raise ValidationError(
                            f"Unrecognized field(s): {names}"
                        )

                    raise ValidationError("city is required")

                city = validate_city(data["city"])

            except ValidationError as exc:
                return {"message": str(exc)}, 400

            return self._get_weather(city)

        @staticmethod
        def _get_weather(
            city: str,
        ) -> tuple[dict[str, Any], int]:
            """Call the external services and handle failures."""
            try:
                weather = external_api.get_weather_for_city(
                    city
                )

            except LookupError:
                return {"message": "City not found"}, 404

            except external_api.ExternalAPIError as exc:
                return {"message": str(exc)}, 502

            return weather, 200

    api.add_resource(
        Register,
        "/register",
        endpoint="user_registration",
    )

    api.add_resource(
        TripList,
        "/trips",
        endpoint="trip_list",
    )

    api.add_resource(
        TripDetail,
        "/trips/<int:trip_id>",
        endpoint="trip_detail",
    )

    api.add_resource(
        Weather,
        "/weather",
        endpoint="weather",
    )

    return app


def main() -> None:
    """Start the API over HTTPS using the required certificate files."""
    app = create_app()

    certificate = Path(__file__).with_name(
        "MyCertificate.crt"
    )

    private_key = Path(__file__).with_name(
        "MyCertificate.key"
    )

    if not certificate.exists() or not private_key.exists():
        raise FileNotFoundError(
            "MyCertificate.crt and MyCertificate.key "
            "must be in the project directory."
        )

    app.run(
        host="0.0.0.0",
        port=5000,
        ssl_context=(
            str(certificate),
            str(private_key),
        ),
    )


if __name__ == "__main__":
    main()