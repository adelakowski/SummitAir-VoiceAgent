"""Technician schedule: open slots, assignment, and SQLite locking."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.tools.handlers import (
    ToolValidationError,
    check_availability,
    flag_priority,
    mock_schedule,
)
from app.tools.schedule import TECHNICIANS, format_spoken_confirmation, make_slot
from app.tools.store import InMemoryStore, SqliteStore


@pytest.fixture
def store():
    return InMemoryStore()


def test_check_availability_lists_free_technicians(store):
    fixed = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    result = check_availability(
        {"zip_code": "80301", "urgency": "high"},
        store=store,
        now=fixed,
    )
    assert len(result["slots"]) >= 2
    assert result["technicians"] == list(TECHNICIANS)
    assert result["options"][0]["technicians"]
    assert "John" in result["options"][0]["technicians"]


def test_mock_schedule_assigns_technician_and_locks_slot(store):
    fixed = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    avail = check_availability(
        {"zip_code": "80301", "urgency": "standard"},
        store=store,
        now=fixed,
    )
    slot_start = avail["slots"][0]
    first = mock_schedule(
        {
            "call_id": "c1",
            "name": "Pat Lee",
            "address": "12 Pine St",
            "property_type": "residential",
            "availability": "tomorrow morning",
            "urgency": "standard",
            "slot_start": slot_start,
        },
        store=store,
        now=fixed,
    )
    assert first["technician"] in TECHNICIANS
    assert first["slot_start"] == slot_start
    assert first["technician"] in first["spoken_confirmation"]
    assert first["confirmation_id"] in first["spoken_confirmation"]

    # Fill remaining techs on the same slot
    for i, _ in enumerate(TECHNICIANS[1:], start=2):
        mock_schedule(
            {
                "call_id": f"c{i}",
                "name": f"Caller {i}",
                "address": "12 Pine St",
                "property_type": "residential",
                "availability": slot_start,
                "urgency": "standard",
                "slot_start": slot_start,
            },
            store=store,
            now=fixed,
        )

    with pytest.raises(ToolValidationError):
        mock_schedule(
            {
                "call_id": "c-full",
                "name": "No Room",
                "address": "12 Pine St",
                "property_type": "residential",
                "availability": slot_start,
                "urgency": "standard",
                "slot_start": slot_start,
            },
            store=store,
            now=fixed,
        )


def test_flag_priority_books_technician(store):
    fixed = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    result = flag_priority(
        {
            "call_id": "c2",
            "reason": "no heat, elderly resident",
            "address": "12 Pine St",
        },
        store=store,
        now=fixed,
    )
    assert result["priority"] == "high"
    assert result["technician"] in TECHNICIANS
    slot = datetime.fromisoformat(result["emergency_slot"])
    assert slot.tzinfo is not None
    assert len(store.list_bookings()) == 1


def test_sqlite_store_persists_across_instances(tmp_path: Path):
    db = tmp_path / "schedule.db"
    store_a = SqliteStore(db)
    fixed = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
    booked = mock_schedule(
        {
            "call_id": "persist-1",
            "name": "Sam",
            "address": "1 Main",
            "property_type": "residential",
            "availability": "tomorrow morning",
            "urgency": "low",
        },
        store=store_a,
        now=fixed,
    )
    store_b = SqliteStore(db)
    assert len(store_b.list_bookings()) == 1
    assert store_b.list_bookings()[0]["technician"] == booked["technician"]
    slots = store_b.list_booked_tech_slots()
    assert (booked["technician"], booked["slot_start"]) in slots


def test_spoken_confirmation_format():
    slot = make_slot(datetime(2026, 1, 15, 21, 0, 0, tzinfo=timezone.utc))  # 14:00 Denver
    text = format_spoken_confirmation(
        technician="Paul",
        slot=slot,
        confirmation_id="SA-ABC",
    )
    assert "Paul will visit" in text
    assert "SA-ABC" in text
