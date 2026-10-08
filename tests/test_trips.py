"""Tests for trip CRUD, validation, filtering, and ownership."""

from __future__ import annotations

from tests.helpers import register_user
from tests.test_auth import basic_auth


def create_trip(
    client,
    username: str = "alice",
    password: str = "password123",
    **overrides,
):
    """Create a user and trip for a test."""
    register_user(
        client,
        username,
        password,
    )

    payload = {
        "destination": "Chicago",
        "start_date": "2026-11-10",
        "days": 4,
    }

    payload.update(overrides)

    return client.post(
        "/trips",
        json=payload,
        headers=basic_auth(
            username,
            password,
        ),
    )


def test_create_trip(client) -> None:
    """A valid trip is created."""
    response = create_trip(client)

    assert response.status_code == 201
    assert response.json["destination"] == "Chicago"
    assert response.json["owner_id"] == 1
    assert "created_at" in response.json
    assert "Location" in response.headers


def test_server_controlled_fields_cannot_be_set(
    client,
) -> None:
    """Clients cannot choose server-controlled fields."""
    register_user(client)

    response = client.post(
        "/trips",
        json={
            "destination": "Chicago",
            "start_date": "2026-11-10",
            "days": 4,
            "id": 999,
        },
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    assert response.status_code == 400


def test_list_and_filter_trips(client) -> None:
    """The list endpoint supports destination filtering."""
    create_trip(
        client,
        destination="Chicago",
    )

    register_user(
        client,
        "bob",
        "password123",
    )

    client.post(
        "/trips",
        json={
            "destination": "Denver",
            "start_date": "2026-12-01",
            "days": 3,
        },
        headers=basic_auth(
            "bob",
            "password123",
        ),
    )

    response = client.get(
        "/trips?destination=Chicago",
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["destination"] == "Chicago"


def test_limit_and_offset(client) -> None:
    """The list endpoint supports limit and offset."""
    create_trip(
        client,
        destination="Chicago",
    )

    client.post(
        "/trips",
        json={
            "destination": "Denver",
            "start_date": "2026-12-01",
            "days": 3,
        },
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    response = client.get(
        "/trips?limit=1&offset=1",
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["destination"] == "Denver"


def test_get_trip(client) -> None:
    """A created trip can be retrieved by ID."""
    create_response = create_trip(client)

    trip_id = create_response.json["id"]

    response = client.get(
        f"/trips/{trip_id}",
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    assert response.status_code == 200
    assert response.json["id"] == trip_id


def test_get_missing_trip_returns_404(
    client,
) -> None:
    """A missing trip returns 404."""
    register_user(client)

    response = client.get(
        "/trips/999",
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    assert response.status_code == 404


def test_patch_only_changes_supplied_field(
    client,
) -> None:
    """PATCH changes only the supplied field."""
    create_response = create_trip(client)

    trip_id = create_response.json["id"]

    response = client.patch(
        f"/trips/{trip_id}",
        json={"days": 7},
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    assert response.status_code == 200
    assert response.json["days"] == 7
    assert response.json["destination"] == "Chicago"
    assert response.json["start_date"] == "2026-11-10"


def test_non_owner_cannot_patch(client) -> None:
    """A different user cannot modify a trip."""
    create_response = create_trip(
        client,
        "alice",
        "password123",
    )

    trip_id = create_response.json["id"]

    register_user(
        client,
        "bob",
        "password123",
    )

    response = client.patch(
        f"/trips/{trip_id}",
        json={"days": 7},
        headers=basic_auth(
            "bob",
            "password123",
        ),
    )

    assert response.status_code == 403


def test_non_owner_can_read_trip(client) -> None:
    """Another authenticated user can read a trip."""
    create_response = create_trip(
        client,
        "alice",
        "password123",
    )

    trip_id = create_response.json["id"]

    register_user(
        client,
        "bob",
        "password123",
    )

    response = client.get(
        f"/trips/{trip_id}",
        headers=basic_auth(
            "bob",
            "password123",
        ),
    )

    assert response.status_code == 200


def test_non_owner_cannot_delete(client) -> None:
    """A different user cannot delete a trip."""
    create_response = create_trip(
        client,
        "alice",
        "password123",
    )

    trip_id = create_response.json["id"]

    register_user(
        client,
        "bob",
        "password123",
    )

    response = client.delete(
        f"/trips/{trip_id}",
        headers=basic_auth(
            "bob",
            "password123",
        ),
    )

    assert response.status_code == 403


def test_owner_can_delete(client) -> None:
    """The owner can delete their trip."""
    create_response = create_trip(client)

    trip_id = create_response.json["id"]

    response = client.delete(
        f"/trips/{trip_id}",
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    assert response.status_code == 200

    get_response = client.get(
        f"/trips/{trip_id}",
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    assert get_response.status_code == 404


def test_invalid_trip_values(client) -> None:
    """Invalid trip values return 400."""
    register_user(client)

    headers = basic_auth(
        "alice",
        "password123",
    )

    cases = [
        {
            "destination": "",
            "start_date": "2026-11-10",
            "days": 4,
        },
        {
            "destination": "Chicago",
            "start_date": "not-a-date",
            "days": 4,
        },
        {
            "destination": "Chicago",
            "start_date": "2026-11-10",
            "days": 0,
        },
        {
            "destination": "Chicago",
            "start_date": "2026-11-10",
            "days": "four",
        },
    ]

    for payload in cases:
        response = client.post(
            "/trips",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        assert "message" in response.json


def test_patch_cannot_change_owner(
    client,
) -> None:
    """PATCH rejects server-controlled ownership fields."""
    create_response = create_trip(client)

    trip_id = create_response.json["id"]

    response = client.patch(
        f"/trips/{trip_id}",
        json={"owner_id": 999},
        headers=basic_auth(
            "alice",
            "password123",
        ),
    )

    assert response.status_code == 400


def test_invalid_pagination(client) -> None:
    """Invalid pagination values return 400."""
    register_user(client)

    headers = basic_auth(
        "alice",
        "password123",
    )

    response = client.get(
        "/trips?limit=abc",
        headers=headers,
    )

    assert response.status_code == 400

    response = client.get(
        "/trips?offset=-1",
        headers=headers,
    )

    assert response.status_code == 400