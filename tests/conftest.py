"""Shared pytest fixtures for the Travel Planner API."""

from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    """Create a test client using a temporary SQLite database."""
    app = create_app(
        db_path=tmp_path / "test.db"
    )

    app.testing = True

    with app.test_client() as test_client:
        yield test_client