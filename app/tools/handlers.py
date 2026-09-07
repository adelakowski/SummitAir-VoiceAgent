"""Tool handlers — triage actions + technician schedule booking."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from app.config import settings
from app.tools import schedule as sched
from app.tools.store import InMemoryStore, SqliteStore

logger = logging.getLogger(__name__)

Store = Union[InMemoryStore, SqliteStore]

_DEFAULT_STORE: Store = InMemoryStore()


class ToolValidationError(ValueError):
    """Raised when required tool fields are missing or invalid."""


def _store(store: Optional[Store]) -> Store:
    return store if store is not None else _DEFAULT_STORE


def _notify_admin(send_coro_factory, *, label: str) -> None:
    """Fire-and-forget admin email when enabled; never break the booking path."""
    if not (settings.email_enabled and settings.admin_notification_email):
        return
    coro = None
    try:
        from app.email_service import get_email_service

        email_service = get_email_service()
        coro = send_coro_factory(email_service)
        asyncio.create_task(coro)
    except Exception as exc:
        if coro is not None:
            coro.close()
        logger.error("Failed to send %s email notification: %s", label, exc)


def escalate_emergency(
    args: dict[str, Any],
    *,
    store: Optional[Store] = None,
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

    _notify_admin(
        lambda svc: svc.send_admin_escalation_notification(
            settings.admin_notification_email,
            result,
            args.get("call_transcript"),
        ),
        label="escalation",
    )

    return result


def flag_priority(
    args: dict[str, Any],
    *,
    store: Optional[Store] = None,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """High-priority ticket: lock soonest open tech slot (emergency windows)."""
    call_id = args.get("call_id")
    reason = args.get("reason")
    if not call_id or not reason:
        raise ToolValidationError("call_id and reason are required")

    base = now if now is not None else datetime.now(timezone.utc)
    s = _store(store)
    booked = s.list_booked_tech_slots()

    # Prefer soonest open slot within ~4 hours; otherwise next open emergency window.
    horizon = base.astimezone(sched.SCHEDULE_TZ) + timedelta(hours=4)
    slot: Optional[sched.TimeSlot] = None
    technician: Optional[str] = None
    for opt in sched.open_slots(
        now=base, booked=booked, urgency="high", limit=8, days_ahead=3
    ):
        start = sched.try_parse_slot_start(opt["start"], now=base)
        if start is None:
            continue
        tech = sched.pick_technician(opt["technicians"])
        if not tech:
            continue
        slot = sched.make_slot(start)
        technician = tech
        if start <= horizon:
            break

    if slot is None or technician is None:
        try:
            slot, technician = sched.resolve_booking_slot(
                now=base,
                booked=booked,
                availability=args.get("availability") or "",
                slot_start=args.get("slot_start"),
                urgency="high",
            )
        except ValueError as exc:
            raise ToolValidationError(str(exc)) from exc

    confirmation_id = f"SA-{uuid.uuid4().hex[:10].upper()}"
    ticket_id = f"PRI-{uuid.uuid4().hex[:8].upper()}"
    spoken = sched.format_spoken_confirmation(
        technician=technician,
        slot=slot,
        confirmation_id=confirmation_id,
    )

    ticket = {
        "priority": "high",
        "call_id": call_id,
        "reason": reason,
        "address": args.get("address"),
        "availability": args.get("availability"),
        "emergency_slot": slot.start_iso,
        "slot_start": slot.start_iso,
        "slot_end": slot.end_iso,
        "technician": technician,
        "confirmation_id": confirmation_id,
        "ticket_id": ticket_id,
        "spoken_confirmation": spoken,
        "window": slot.start_iso,
        "name": args.get("name") or "priority caller",
        "property_type": args.get("property_type") or "residential",
        "urgency": "high",
    }

    try:
        s.add_booking(ticket)
    except ValueError as exc:
        raise ToolValidationError(str(exc)) from exc
    s.add_priority_ticket(ticket)

    _notify_admin(
        lambda svc: svc.send_admin_priority_notification(
            settings.admin_notification_email,
            ticket,
            args.get("call_transcript"),
        ),
        label="priority",
    )

    return ticket


_REQUIRED_SCHEDULE = (
    "call_id",
    "name",
    "address",
    "property_type",
    "availability",
    "urgency",
)


def mock_schedule(
    args: dict[str, Any],
    *,
    store: Optional[Store] = None,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Book an appointment with John, Paul, or George; lock their slot."""
    missing = [f for f in _REQUIRED_SCHEDULE if not args.get(f)]
    if missing:
        raise ToolValidationError(f"Missing required fields: {', '.join(missing)}")

    urgency = args["urgency"]
    if urgency not in ("standard", "low"):
        raise ToolValidationError("urgency must be 'standard' or 'low'")

    base = now if now is not None else datetime.now(timezone.utc)
    s = _store(store)
    booked = s.list_booked_tech_slots()

    try:
        slot, technician = sched.resolve_booking_slot(
            now=base,
            booked=booked,
            availability=args["availability"],
            slot_start=args.get("slot_start"),
            urgency=urgency,
        )
    except ValueError as exc:
        raise ToolValidationError(str(exc)) from exc

    confirmation_id = f"SA-{uuid.uuid4().hex[:10].upper()}"
    spoken = sched.format_spoken_confirmation(
        technician=technician,
        slot=slot,
        confirmation_id=confirmation_id,
    )

    booking = {
        "confirmation_id": confirmation_id,
        "call_id": args["call_id"],
        "name": args["name"],
        "address": args["address"],
        "property_type": args["property_type"],
        "availability": args["availability"],
        "urgency": urgency,
        "technician": technician,
        "slot_start": slot.start_iso,
        "slot_end": slot.end_iso,
        "window": slot.start_iso,
        "spoken_confirmation": spoken,
        "priority": urgency,
    }

    try:
        s.add_booking(booking)
    except ValueError as exc:
        raise ToolValidationError(str(exc)) from exc

    _notify_admin(
        lambda svc: svc.send_admin_booking_notification(
            settings.admin_notification_email,
            booking,
            args.get("call_transcript"),
        ),
        label="booking",
    )

    return {
        "confirmation_id": confirmation_id,
        "window": slot.start_iso,
        "slot_start": slot.start_iso,
        "slot_end": slot.end_iso,
        "technician": technician,
        "spoken_confirmation": spoken,
        "status": "scheduled",
    }


def check_availability(
    args: dict[str, Any],
    *,
    store: Optional[Store] = None,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Return open 2-hour slots where at least one of John/Paul/George is free."""
    if not args.get("zip_code") and not args.get("address"):
        raise ToolValidationError("zip_code or address is required")

    base = now if now is not None else datetime.now(timezone.utc)
    urgency = (args.get("urgency") or "standard").lower()
    booked = _store(store).list_booked_tech_slots()
    options = sched.open_slots(now=base, booked=booked, urgency=urgency, limit=3)

    return {
        "slots": [o["start"] for o in options],
        "options": options,
        "technicians": list(sched.TECHNICIANS),
        "slot_hours": sched.SLOT_HOURS,
        "zip_code": args.get("zip_code"),
        "address": args.get("address"),
        "urgency": urgency,
    }
