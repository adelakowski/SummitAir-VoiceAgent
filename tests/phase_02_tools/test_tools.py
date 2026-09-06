"""Phase 2 gate: mock tool handlers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.tools.handlers import (
    check_availability,
    escalate_emergency,
    flag_priority,
    mock_schedule,
)
from app.tools.store import InMemoryStore


@pytest.fixture
def store():
    return InMemoryStore()


def test_escalate_emergency_does_not_book(store):
    result = escalate_emergency(
        {
            "call_id": "c1",
            "hazard_summary": "smell of gas near furnace",
            "caller_phone": "+15551212",
        },
        store=store,
    )
    assert result["escalated"] is True
    assert result["action"] == "evacuate_and_call_911"
    assert "911" in result["message"] or "evacuate" in result["message"].lower()
    assert store.list_bookings() == []
    assert len(store.list_escalations()) == 1


def test_flag_priority_returns_emergency_slot(store, monkeypatch):
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
    slot = datetime.fromisoformat(result["emergency_slot"])
    assert 0 < (slot - fixed).total_seconds() <= 4 * 3600


def test_mock_schedule_requires_core_fields(store):
    from app.tools.handlers import ToolValidationError

    with pytest.raises(ToolValidationError):
        mock_schedule(
            {"call_id": "c3", "name": "Pat"},
            store=store,
        )


def test_mock_schedule_creates_confirmation(store):
    result = mock_schedule(
        {
            "call_id": "c4",
            "name": "Pat Lee",
            "address": "12 Pine St",
            "property_type": "residential",
            "availability": "tomorrow morning",
            "urgency": "standard",
        },
        store=store,
    )
    assert "confirmation_id" in result
    assert len(store.list_bookings()) == 1


def test_check_availability_returns_slots(store):
    high = check_availability({"zip_code": "80301", "urgency": "high"}, store=store)
    low = check_availability({"zip_code": "80301", "urgency": "low"}, store=store)
    assert len(high["slots"]) >= 2
    assert len(low["slots"]) >= 2
    assert high["slots"][0] <= low["slots"][0]
