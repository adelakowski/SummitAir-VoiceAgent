"""Shared FastAPI dependencies for Retell webhooks."""

from __future__ import annotations

from functools import lru_cache

from app.tools.store import InMemoryStore


@lru_cache(maxsize=1)
def get_store() -> InMemoryStore:
    """Process-wide in-memory store for mock bookings/escalations."""
    return InMemoryStore()
