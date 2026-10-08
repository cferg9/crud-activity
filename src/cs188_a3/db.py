"""Database helpers for the Travel Planner API."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination TEXT NOT NULL,
    start_date TEXT NOT NULL,
    days INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection configured to return rows by name."""
    connection = sqlite3.connect(str(db_path))

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def initialize_database(db_path: str | Path) -> None:
    """Create all required database tables."""
    connection = connect(db_path)

    try:
        connection.executescript(SCHEMA)
        connection.commit()

    finally:
        connection.close()


def row_to_dict(
    row: sqlite3.Row | None,
) -> dict[str, Any] | None:
    """Convert a SQLite row into a regular dictionary."""
    if row is None:
        return None

    return dict(row)