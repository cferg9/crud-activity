"""Input validation helpers for API requests."""

from __future__ import annotations

from datetime import date
from typing import Any

from flask import Request


class ValidationError(Exception):
    """Raised when request data is invalid."""


def json_object(
    request: Request,
) -> dict[str, Any]:
    """Read a request body and require a JSON object."""
    if not request.is_json:
        raise ValidationError(
            "Request body must be JSON"
        )

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):
        raise ValidationError(
            "JSON body must be an object"
        )

    return data


def validate_username(
    username: Any,
) -> str:
    """Validate and return a username."""
    if not isinstance(username, str):
        raise ValidationError(
            "username must be a string"
        )

    username = username.strip()

    if not username:
        raise ValidationError(
            "username cannot be blank"
        )

    if len(username) < 3 or len(username) > 30:
        raise ValidationError(
            "username must be between 3 and 30 characters"
        )

    return username


def validate_password(
    password: Any,
) -> str:
    """Validate and return a password."""
    if not isinstance(password, str):
        raise ValidationError(
            "password must be a string"
        )

    if len(password) < 8 or len(password) > 100:
        raise ValidationError(
            "password must be between 8 and 100 characters"
        )

    return password


def validate_destination(
    destination: Any,
) -> str:
    """Validate and return a trip destination."""
    if not isinstance(destination, str):
        raise ValidationError(
            "destination must be a string"
        )

    destination = destination.strip()

    if not destination:
        raise ValidationError(
            "destination cannot be blank"
        )

    if len(destination) > 100:
        raise ValidationError(
            "destination must be 100 characters or fewer"
        )

    return destination


def validate_start_date(
    start_date: Any,
) -> str:
    """Validate an ISO-format trip start date."""
    if not isinstance(start_date, str):
        raise ValidationError(
            "start_date must be a string in YYYY-MM-DD format"
        )

    try:
        parsed = date.fromisoformat(
            start_date
        )

    except ValueError as exc:
        raise ValidationError(
            "start_date must be a valid date in YYYY-MM-DD format"
        ) from exc

    return parsed.isoformat()


def validate_days(
    days: Any,
) -> int:
    """Validate the number of trip days."""
    if (
        isinstance(days, bool)
        or not isinstance(days, int)
    ):
        raise ValidationError(
            "days must be an integer between 1 and 30"
        )

    if days < 1 or days > 30:
        raise ValidationError(
            "days must be an integer between 1 and 30"
        )

    return days


def validate_trip_create(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Validate all fields required to create a trip."""
    allowed = {
        "destination",
        "start_date",
        "days",
    }

    unknown = set(data) - allowed

    if unknown:
        names = ", ".join(
            sorted(unknown)
        )

        raise ValidationError(
            f"Unrecognized field(s): {names}"
        )

    required = allowed - set(data)

    if required:
        names = ", ".join(
            sorted(required)
        )

        raise ValidationError(
            f"Missing required field(s): {names}"
        )

    return {
        "destination": validate_destination(
            data["destination"]
        ),
        "start_date": validate_start_date(
            data["start_date"]
        ),
        "days": validate_days(
            data["days"]
        ),
    }


def validate_trip_patch(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Validate fields supplied for a partial trip update."""
    allowed = {
        "destination",
        "start_date",
        "days",
    }

    server_fields = {
        "id",
        "owner_id",
        "created_at",
    }

    if not data:
        raise ValidationError(
            "PATCH body cannot be empty"
        )

    supplied_server_fields = (
        set(data) & server_fields
    )

    if supplied_server_fields:
        names = ", ".join(
            sorted(supplied_server_fields)
        )

        raise ValidationError(
            "Server-controlled field(s) "
            f"cannot be changed: {names}"
        )

    unknown = set(data) - allowed

    if unknown:
        names = ", ".join(
            sorted(unknown)
        )

        raise ValidationError(
            f"Unrecognized field(s): {names}"
        )

    changes: dict[str, Any] = {}

    if "destination" in data:
        changes["destination"] = (
            validate_destination(
                data["destination"]
            )
        )

    if "start_date" in data:
        changes["start_date"] = (
            validate_start_date(
                data["start_date"]
            )
        )

    if "days" in data:
        changes["days"] = validate_days(
            data["days"]
        )

    return changes


def validate_positive_query_int(
    value: str | None,
    field_name: str,
    default: int,
) -> int:
    """Validate a non-negative integer query parameter."""
    if value is None:
        return default

    try:
        number = int(value)

    except ValueError as exc:
        raise ValidationError(
            f"{field_name} must be an integer"
        ) from exc

    if number < 0:
        raise ValidationError(
            f"{field_name} cannot be negative"
        )

    return number


def validate_limit(
    value: str | None,
) -> int:
    """Validate the list endpoint limit."""
    limit = validate_positive_query_int(
        value,
        "limit",
        50,
    )

    if limit > 100:
        raise ValidationError(
            "limit cannot be greater than 100"
        )

    return limit


def validate_trip_id(
    trip_id: int,
) -> int:
    """Validate a trip ID from a URL."""
    if trip_id <= 0:
        raise ValidationError(
            "id must be a positive integer"
        )

    return trip_id


def validate_city(
    city: Any,
) -> str:
    """Validate a city name for the weather endpoint."""
    if not isinstance(city, str):
        raise ValidationError(
            "city must be a string"
        )

    city = city.strip()

    if not city:
        raise ValidationError(
            "city cannot be blank"
        )

    if len(city) > 100:
        raise ValidationError(
            "city must be 100 characters or fewer"
        )

    return city