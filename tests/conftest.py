"""Pytest defaults — keep tool tests isolated from the on-disk schedule DB."""

from __future__ import annotations

import os

# Force in-memory schedule store for the test process (before app imports settings).
os.environ["SCHEDULE_DB_PATH"] = ""
os.environ.setdefault("APP_ENV", "test")


def pytest_configure() -> None:
    # If deps were imported earlier, reset the cached store.
    try:
        from app.api.deps import get_store

        get_store.cache_clear()
    except Exception:
        pass
