"""Service-layer functions for the Travel Planner API."""

from __future__ import annotations

import sqlite3
from typing import Any


class NotFound(Exception):
    """Raised when a requested resource does not exist."""


class Forbidden(Exception):
    """Raised when a user cannot modify a resource."""


def create_user(
    connection: sqlite3.Connection,
    username: str,
    password_hash: str,
) -> dict[str, Any]:
    """Create a user and return public user information."""
    cursor = connection.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (?, ?)
        """,
        (username, password_hash),
    )

    connection.commit()

    return {
        "id": cursor.lastrowid,
        "username": username,
    }


def get_user_by_username(
    connection: sqlite3.Connection,
    username: str,
) -> dict[str, Any] | None:
    """Return a user by username."""
    row = connection.execute(
        """
        SELECT id, username, password_hash
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_user_by_id(
    connection: sqlite3.Connection,
    user_id: int,
) -> dict[str, Any] | None:
    """Return a user by ID."""
    row = connection.execute(
        """
        SELECT id, username
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def create_trip(
    connection: sqlite3.Connection,
    owner_id: int,
    destination: str,
    start_date: str,
    days: int,
    created_at: str,
) -> dict[str, Any]:
    """Create a trip owned by the specified user."""
    cursor = connection.execute(
        """
        INSERT INTO trips
            (destination, start_date, days, owner_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            destination,
            start_date,
            days,
            owner_id,
            created_at,
        ),
    )

    connection.commit()

    return get_trip(
        connection,
        cursor.lastrowid,
    )


def get_trip(
    connection: sqlite3.Connection,
    trip_id: int,
) -> dict[str, Any]:
    """Return one trip or raise NotFound."""
    row = connection.execute(
        """
        SELECT
            id,
            destination,
            start_date,
            days,
            owner_id,
            created_at
        FROM trips
        WHERE id = ?
        """,
        (trip_id,),
    ).fetchone()

    if row is None:
        raise NotFound

    return dict(row)


def list_trips(
    connection: sqlite3.Connection,
    destination: str | None,
    start_date: str | None,
    limit: int,
    offset: int,
) -> list[dict]:
    """Return trips matching optional filters."""

    query = """
        SELECT id, destination, start_date, days, owner_id, created_at
        FROM trips
        WHERE 1 = 1
    """

    parameters = []

    if destination:
        query += " AND LOWER(destination) = LOWER(?)"
        parameters.append(destination)

    if start_date:
        query += " AND start_date = ?"
        parameters.append(start_date)

    query += " ORDER BY id LIMIT ? OFFSET ?"

    parameters.extend([limit, offset])

    rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]


def update_trip(
    connection: sqlite3.Connection,
    user_id: int,
    trip_id: int,
    changes: dict[str, Any],
) -> dict[str, Any]:
    """Update supplied trip fields after checking ownership."""
    trip = get_trip(
        connection,
        trip_id,
    )

    if trip["owner_id"] != user_id:
        raise Forbidden

    assignments: list[str] = []
    values: list[Any] = []

    if "destination" in changes:
        assignments.append(
            "destination = ?"
        )
        values.append(
            changes["destination"]
        )

    if "start_date" in changes:
        assignments.append(
            "start_date = ?"
        )
        values.append(
            changes["start_date"]
        )

    if "days" in changes:
        assignments.append(
            "days = ?"
        )
        values.append(
            changes["days"]
        )

    if assignments:
        values.append(trip_id)

        sql = (
            "UPDATE trips SET "
            + ", ".join(assignments)
            + " WHERE id = ?"
        )

        connection.execute(
            sql,
            values,
        )

        connection.commit()

    return get_trip(
        connection,
        trip_id,
    )


def delete_trip(
    connection: sqlite3.Connection,
    user_id: int,
    trip_id: int,
) -> None:
    """Delete a trip after checking ownership."""
    trip = get_trip(
        connection,
        trip_id,
    )

    if trip["owner_id"] != user_id:
        raise Forbidden

    connection.execute(
        "DELETE FROM trips WHERE id = ?",
        (trip_id,),
    )

    connection.commit()