"""Authentication helpers for the Travel Planner API."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import g, request
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from services import get_user_by_username


def hash_password(password: str) -> str:
    """Create a secure password hash."""
    return generate_password_hash(password)


def verify_password(
    password_hash: str,
    password: str,
) -> bool:
    """Check a password against a stored hash."""
    return check_password_hash(
        password_hash,
        password,
    )


def auth_required(
    function: Callable[..., Any],
) -> Callable[..., Any]:
    """Require valid HTTP Basic Authentication."""
    @wraps(function)
    def wrapper(
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        credentials = request.authorization

        if (
            credentials is None
            or not credentials.username
            or credentials.password is None
        ):
            return {
                "message": "Authentication required"
            }, 401

        user = get_user_by_username(
            g.db,
            credentials.username,
        )

        if (
            user is None
            or not verify_password(
                user["password_hash"],
                credentials.password,
            )
        ):
            return {
                "message": "Invalid username or password"
            }, 401

        g.user_id = user["id"]
        g.username = user["username"]

        return function(
            *args,
            **kwargs,
        )

    return wrapper