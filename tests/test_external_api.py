"""Tests for the Open-Meteo HTTP client functions."""

from __future__ import annotations

from cs188_a3 import external_api


class FakeResponse:
    """Fake requests response used to test our API client."""

    def __init__(self, data: dict):
        self.data = data

    def raise_for_status(self) -> None:
        """Pretend the HTTP response was successful."""

    def json(self) -> dict:
        """Return the fake JSON response."""
        return self.data


def test_get_location_uses_geocoding_endpoint(
    monkeypatch,
) -> None:
    """The geocoding client sends the city as a parameter."""
    calls = []

    def fake_get(
        url,
        params,
        timeout,
    ):
        calls.append(
            (
                url,
                params,
                timeout,
            )
        )

        return FakeResponse(
            {
                "results": [
                    {
                        "name": "Chicago",
                        "latitude": 41.88,
                        "longitude": -87.63,
                    }
                ]
            }
        )

    monkeypatch.setattr(
        external_api.requests,
        "get",
        fake_get,
    )

    result = external_api.get_location(
        "Chicago"
    )

    assert result["name"] == "Chicago"

    assert (
        calls[0][0]
        == external_api.GEOCODING_API_URL
    )

    assert (
        calls[0][1]["name"]
        == "Chicago"
    )


def test_get_current_weather_uses_forecast_endpoint(
    monkeypatch,
) -> None:
    """The forecast client sends latitude and longitude."""
    calls = []

    def fake_get(
        url,
        params,
        timeout,
    ):
        calls.append(
            (
                url,
                params,
                timeout,
            )
        )

        return FakeResponse(
            {
                "current": {
                    "temperature_2m": 52.0,
                    "weather_code": 3,
                    "time": "2026-10-08T09:00",
                }
            }
        )

    monkeypatch.setattr(
        external_api.requests,
        "get",
        fake_get,
    )

    result = external_api.get_current_weather(
        41.88,
        -87.63,
    )

    assert (
        result["current"]["temperature_2m"]
        == 52.0
    )

    assert (
        calls[0][0]
        == external_api.FORECAST_API_URL
    )

    assert (
        calls[0][1]["latitude"]
        == 41.88
    )

    assert (
        calls[0][1]["longitude"]
        == -87.63
    )