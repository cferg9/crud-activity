"""Client functions for the Open-Meteo external APIs."""

from __future__ import annotations

from typing import Any

import requests


GEOCODING_API_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)

FORECAST_API_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

REQUEST_TIMEOUT_SECONDS = 10


class ExternalAPIError(Exception):
    """Raised when an external weather API request fails."""


def get_location(
    city: str,
) -> dict[str, Any]:
    """Look up a city with Open-Meteo's geocoding API."""
    try:
        response = requests.get(
            GEOCODING_API_URL,
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
        raise ExternalAPIError(
            "Could not contact the geocoding service"
        ) from exc

    results = data.get(
        "results",
        [],
    )

    if not results:
        raise LookupError(
            "City not found"
        )

    return results[0]


def get_current_weather(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """Get current weather for coordinates."""
    try:
        response = requests.get(
            FORECAST_API_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "weather_code"
                ),
                "temperature_unit": "fahrenheit",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
        raise ExternalAPIError(
            "Could not contact the weather service"
        ) from exc


def get_weather_for_city(city: str) -> dict[str, Any]:
    """Get current weather information for a city."""
    location = get_location(city)

    weather = get_current_weather(
        location["latitude"],
        location["longitude"],
    )

    current = weather["current"]

    return {
        "city": location["name"],
        "country": location.get("country"),
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "temperature_f": current.get("temperature_2m"),
        "weather_code": current.get("weather_code"),
        "time": current.get("time"),
    }