"""Reusable test helpers."""

from __future__ import annotations


def register_user(
    client,
    username: str = "alice",
    password: str = "password123",
) -> tuple[str, str]:
    """Register a user and return credentials."""
    response = client.post(
        "/register",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 201

    return username, password