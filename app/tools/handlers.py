"""Mock tool handlers — pure Python, no HTTP (PRD §7.7)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.config import settings
from app.tools.store import InMemoryStore

logger = logging.getLogger(__name__)

_DEFAULT_STORE = InMemoryStore()


class ToolValidationError(ValueError):
    """Raised when required tool fields are missing or invalid."""


def _store(store: Optional[InMemoryStore]) -> InMemoryStore:
    return store if store is not None else _DEFAULT_STORE


def escalate_emergency(
    args: dict[str, Any],
    *,
    store: Optional[InMemoryStore] = None,
) -> dict[str, Any]:
    """Life-safety escalation — never books a technician."""
    call_id = args.get("call_id")
    hazard_summary = args.get("hazard_summary")
    if not call_id or not hazard_summary:
        raise ToolValidationError("call_id and hazard_summary are required")

    result = {
        "action": "evacuate_and_call_911",
        "message": (
            "This may be a life-safety emergency. Please evacuate the building "
            "immediately and call 911 and/or your gas company from a safe location. "
            "Do not schedule a technician until you are safe."
        ),
        "escalated": True,
        "call_id": call_id,
        "hazard_summary": hazard_summary,
        "caller_phone": args.get("caller_phone"),
    }
    _store(store).add_escalation(result)
    
    # Send admin notification email asynchronously
    if settings.email_enabled and settings.admin_notification_email:
        try:
            from app.email_service import get_email_service
            email_service = get_email_service()
            call_transcript = args.get("call_transcript")
            asyncio.create_task(
                email_service.send_admin_escalation_notification(
                    settings.admin_notification_email,
                    result,
                    call_transcript,
                )
            )
        except Exception as e:
            logger.error(f"Failed to send escalation email notification: {e}")
    
    return result


def flag_priority(
    args: dict[str, Any],
    *,
    store: Optional[InMemoryStore] = None,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Create a high-priority ticket and offer an emergency slot within 4 hours."""
    call_id = args.get("call_id")
    reason = args.get("reason")
    if not call_id or not reason:
        raise ToolValidationError("call_id and reason are required")

    base = now if now is not None else datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)

    # Mid-window slot within the next 4 hours (deterministic for tests).
    emergency_slot = base + timedelta(hours=2)

    ticket = {
        "priority": "high",
        "call_id": call_id,
        "reason": reason,
        "address": args.get("address"),
        "availability": args.get("availability"),
        "emergency_slot": emergency_slot.isoformat(),
        "ticket_id": f"PRI-{uuid.uuid4().hex[:8].upper()}",
    }
    _store(store).add_priority_ticket(ticket)
    
    # Send admin notification email asynchronously
    if settings.email_enabled and settings.admin_notification_email:
        try:
            from app.email_service import get_email_service
            email_service = get_email_service()
            call_transcript = args.get("call_transcript")
            asyncio.create_task(
                email_service.send_admin_priority_notification(
                    settings.admin_notification_email,
                    ticket,
                    call_transcript,
                )
            )
        except Exception as e:
            logger.error(f"Failed to send priority email notification: {e}")
    
    return ticket


_REQUIRED_SCHEDULE = ("call_id", "name", "address", "property_type", "availability", "urgency")


def mock_schedule(
    args: dict[str, Any],
    *,
    store: Optional[InMemoryStore] = None,
) -> dict[str, Any]:
    """Book a mock appointment; validate required fields."""
    missing = [f for f in _REQUIRED_SCHEDULE if not args.get(f)]
    if missing:
        raise ToolValidationError(f"Missing required fields: {', '.join(missing)}")

    urgency = args["urgency"]
    if urgency not in ("standard", "low"):
        raise ToolValidationError("urgency must be 'standard' or 'low'")

    confirmation_id = f"SA-{uuid.uuid4().hex[:10].upper()}"
    booking = {
        "confirmation_id": confirmation_id,
        "call_id": args["call_id"],
        "name": args["name"],
        "address": args["address"],
        "property_type": args["property_type"],
        "availability": args["availability"],
        "urgency": urgency,
        "window": args["availability"],
    }
    _store(store).add_booking(booking)
    
    # Send admin notification email asynchronously
    if settings.email_enabled and settings.admin_notification_email:
        try:
            from app.email_service import get_email_service
            email_service = get_email_service()
            call_transcript = args.get("call_transcript")
            asyncio.create_task(
                email_service.send_admin_booking_notification(
                    settings.admin_notification_email,
                    booking,
                    call_transcript,
                )
            )
        except Exception as e:
            logger.error(f"Failed to send booking email notification: {e}")
    
    return {
        "confirmation_id": confirmation_id,
        "window": args["availability"],
        "status": "scheduled",
    }


def check_availability(
    args: dict[str, Any],
    *,
    store: Optional[InMemoryStore] = None,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Return 2–3 mock ISO slots; high urgency gets earlier windows."""
    del store  # unused — kept for API symmetry with other handlers
    if not args.get("zip_code") and not args.get("address"):
        raise ToolValidationError("zip_code or address is required")

    base = now if now is not None else datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)

    urgency = (args.get("urgency") or "standard").lower()
    # High urgency: slots starting ~2h out; lower urgency: next-day windows.
    if urgency in ("high", "critical", "emergency"):
        offsets_hours = (2, 4, 6)
    else:
        offsets_hours = (24, 36, 48)

    slots = [(base + timedelta(hours=h)).isoformat() for h in offsets_hours]
    return {
        "slots": slots,
        "zip_code": args.get("zip_code"),
        "address": args.get("address"),
        "urgency": urgency,
    }
