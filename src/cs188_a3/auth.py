"""Authentication helpers for the Travel Planner API."""
from __future__ import annotations
from functools import wraps
from typing import Callable


from . import services
from flask import Response, g, request
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    """Hash a user's password before storing it."""
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Check whether a password matches its stored hash."""
    return check_password_hash(password_hash, password)


def auth_required(function: Callable) -> Callable:
    """Require valid HTTP Basic Authentication."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        authorization = request.authorization

        if authorization is None:
            return Response(
                '{"message": "Authentication required."}',
                status=401,
                content_type="application/json",
                headers={"WWW-Authenticate": 'Basic realm="Travel Planner API"'},
            )

        user = services.get_user_by_username(
            g.db,
            authorization.username,
        )

        if user is None or not verify_password(
            user["password_hash"],
            authorization.password,
        ):
            return Response(
                '{"message": "Invalid username or password."}',
                status=401,
                content_type="application/json",
                headers={"WWW-Authenticate": 'Basic realm="Travel Planner API"'},
            )

        g.user_id = user["id"]
        g.username = user["username"]

        return function(*args, **kwargs)

    return wrapper