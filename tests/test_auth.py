"""Tests for registration and authentication."""

from __future__ import annotations

import base64

import pytest

from tests.helpers import register_user


def basic_auth(
    username: str,
    password: str,
) -> dict[str, str]:
    """Create an HTTP Basic Authentication header."""
    token = base64.b64encode(
        f"{username}:{password}".encode()
    ).decode()

    return {
        "Authorization": f"Basic {token}"
    }


def test_register_success(client) -> None:
    """A valid registration creates a user."""
    response = client.post(
        "/register",
        json={
            "username": "alice",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    assert response.json["username"] == "alice"
    assert "Location" in response.headers


def test_duplicate_username(client) -> None:
    """A username cannot be registered twice."""
    register_user(client)

    response = client.post(
        "/register",
        json={
            "username": "alice",
            "password": "password123",
        },
    )

    assert response.status_code == 409
    assert "already" in response.json["message"]


@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "ab",
            "password": "password123",
        },
        {
            "username": "alice",
            "password": "short",
        },
        {
            "username": "   ",
            "password": "password123",
        },
        {
            "username": "alice",
            "password": "   ",
        },
    ],
)
def test_invalid_registration(
    client,
    payload,
) -> None:
    """Invalid registration data returns 400."""
    response = client.post(
        "/register",
        json=payload,
    )

    assert response.status_code == 400
    assert "message" in response.json


def test_authentication_required(client) -> None:
    """Trip endpoints require authentication."""
    response = client.get("/trips")

    assert response.status_code == 401


def test_wrong_password_returns_401(client) -> None:
    """Incorrect credentials return 401."""
    register_user(client)

    response = client.get(
        "/trips",
        headers=basic_auth(
            "alice",
            "wrongpassword",
        ),
    )

    assert response.status_code == 401