"""Tests for the weather endpoint."""

from __future__ import annotations

import external_api


def test_weather_get(
    client,
    monkeypatch,
) -> None:
    """GET /weather accepts a city query parameter."""
    def fake_weather(city: str):
        assert city == "Chicago"

        return {
            "city": "Chicago",
            "temperature_f": 50,
            "weather_code": 1,
        }

    monkeypatch.setattr(
        external_api,
        "get_weather_for_city",
        fake_weather,
    )

    response = client.get(
        "/weather?city=Chicago"
    )

    assert response.status_code == 200
    assert response.json["city"] == "Chicago"


def test_weather_post(
    client,
    monkeypatch,
) -> None:
    """POST /weather accepts a JSON city."""
    def fake_weather(city: str):
        assert city == "Denver"

        return {
            "city": "Denver",
            "temperature_f": 45,
            "weather_code": 2,
        }

    monkeypatch.setattr(
        external_api,
        "get_weather_for_city",
        fake_weather,
    )

    response = client.post(
        "/weather",
        json={"city": "Denver"},
    )

    assert response.status_code == 200
    assert response.json["city"] == "Denver"


def test_weather_missing_city(client) -> None:
    """Missing city input returns 400."""
    response = client.get(
        "/weather"
    )

    assert response.status_code == 400


def test_weather_unknown_city(
    client,
    monkeypatch,
) -> None:
    """An unknown city returns 404."""
    def fake_weather(city: str):
        raise LookupError(
            "City not found"
        )

    monkeypatch.setattr(
        external_api,
        "get_weather_for_city",
        fake_weather,
    )

    response = client.get(
        "/weather?city=NotARealCity"
    )

    assert response.status_code == 404