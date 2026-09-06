"""Shared FastAPI dependencies for Retell webhooks."""

from __future__ import annotations

from functools import lru_cache
from typing import Union

from app.config import settings
from app.tools.store import InMemoryStore, SqliteStore, create_store

Store = Union[InMemoryStore, SqliteStore]


@lru_cache(maxsize=1)
def get_store() -> Store:
    """Process-wide booking store (SQLite when SCHEDULE_DB_PATH is set)."""
    path = (settings.schedule_db_path or "").strip()
    return create_store(path or None)
