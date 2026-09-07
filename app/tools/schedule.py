"""Technician schedule: John, Paul, George — shared hours, 2-hour slots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, Sequence
from zoneinfo import ZoneInfo

# Summit Air demo crew (same roster for every zone).
TECHNICIANS: tuple[str, ...] = ("John", "Paul", "George")

# Shared working hours (America/Denver) — Mon–Sat inclusive.
SCHEDULE_TZ = ZoneInfo("America/Denver")
WORK_DAYS = frozenset({0, 1, 2, 3, 4, 5})  # Mon–Sat
WORK_START_HOUR = 8
WORK_END_HOUR = 18  # last slot starts at 16:00
SLOT_HOURS = 2


@dataclass(frozen=True)
class TimeSlot:
    start: datetime
    end: datetime

    @property
    def start_iso(self) -> str:
        return self.start.isoformat()

    @property
    def end_iso(self) -> str:
        return self.end.isoformat()


def _as_denver(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(SCHEDULE_TZ)


def iter_slot_starts(
    *,
    now: datetime,
    days_ahead: int = 14,
) -> Iterable[datetime]:
    """Yield valid slot starts from the next open window through ``days_ahead``."""
    local_now = _as_denver(now)
    # Snap to next slot boundary at/after now.
    cursor = local_now.replace(minute=0, second=0, microsecond=0)
    if cursor.hour % SLOT_HOURS != 0:
        cursor += timedelta(hours=SLOT_HOURS - (cursor.hour % SLOT_HOURS))
    if cursor <= local_now:
        cursor += timedelta(hours=SLOT_HOURS)

    end_limit = local_now + timedelta(days=days_ahead)
    while cursor < end_limit:
        if (
            cursor.weekday() in WORK_DAYS
            and WORK_START_HOUR <= cursor.hour < WORK_END_HOUR
            and cursor.hour % SLOT_HOURS == 0
        ):
            yield cursor
        cursor += timedelta(hours=SLOT_HOURS)


def make_slot(start: datetime) -> TimeSlot:
    start = _as_denver(start)
    return TimeSlot(start=start, end=start + timedelta(hours=SLOT_HOURS))


def free_technicians_for_slot(
    slot_start_iso: str,
    booked: Sequence[tuple[str, str]],
    *,
    technicians: Sequence[str] = TECHNICIANS,
) -> list[str]:
    """Return technicians not already booked at ``slot_start_iso``."""
    taken = {tech for tech, start in booked if start == slot_start_iso}
    return [t for t in technicians if t not in taken]


def pick_technician(
    free: Sequence[str],
    *,
    technicians: Sequence[str] = TECHNICIANS,
) -> Optional[str]:
    """Prefer roster order (John → Paul → George) among free techs."""
    for name in technicians:
        if name in free:
            return name
    return None


def _preference_hours(availability: str) -> Optional[set[int]]:
    text = availability.lower()
    if "morning" in text:
        return {8, 10}
    if "afternoon" in text or "evening" in text:
        return {12, 14, 16}
    return None


def try_parse_slot_start(value: str, *, now: datetime) -> Optional[datetime]:
    """Parse an ISO timestamp; return None if not a datetime."""
    text = value.strip()
    if not text:
        return None
    # Plain preference phrases are not ISO.
    if any(ch.isalpha() for ch in text) and "T" not in text and "+" not in text:
        # Allow "2026-01-15 10:00:00+00:00" style without T
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        return _as_denver(parsed)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _as_denver(parsed)


def open_slots(
    *,
    now: datetime,
    booked: Sequence[tuple[str, str]],
    urgency: str = "standard",
    limit: int = 3,
    days_ahead: int = 14,
) -> list[dict]:
    """
    Return up to ``limit`` open slots where at least one technician is free.

    High/emergency urgency prefers the soonest windows; standard/low can start
    from the next calendar day if there is still capacity today for emergencies only.
    """
    urgency_l = urgency.lower()
    high = urgency_l in {"high", "critical", "emergency", "priority"}
    local_now = _as_denver(now)
    options: list[dict] = []

    for start in iter_slot_starts(now=now, days_ahead=days_ahead):
        if not high and start.date() <= local_now.date():
            # Standard/low: offer from tomorrow onward when possible.
            continue
        slot = make_slot(start)
        free = free_technicians_for_slot(slot.start_iso, booked)
        if not free:
            continue
        options.append(
            {
                "start": slot.start_iso,
                "end": slot.end_iso,
                "technicians": free,
            }
        )
        if len(options) >= limit:
            break

    # If standard filter yielded nothing (e.g. late Saturday), fall back to any open.
    if not options:
        for start in iter_slot_starts(now=now, days_ahead=days_ahead):
            slot = make_slot(start)
            free = free_technicians_for_slot(slot.start_iso, booked)
            if not free:
                continue
            options.append(
                {
                    "start": slot.start_iso,
                    "end": slot.end_iso,
                    "technicians": free,
                }
            )
            if len(options) >= limit:
                break

    return options


def resolve_booking_slot(
    *,
    now: datetime,
    booked: Sequence[tuple[str, str]],
    availability: str,
    slot_start: Optional[str] = None,
    urgency: str = "standard",
    require_requested_slot: bool = False,
) -> tuple[TimeSlot, str]:
    """
    Choose a free slot + technician.

    Prefer explicit ``slot_start`` (from check_availability); else parse
    ``availability`` as ISO; else match morning/afternoon preference; else next open.

    If ``require_requested_slot`` is true and the requested slot has no free tech,
    raise ValueError instead of falling back.
    """
    requested: Optional[datetime] = None
    if slot_start:
        requested = try_parse_slot_start(slot_start, now=now)
    if requested is None:
        requested = try_parse_slot_start(availability, now=now)

    if requested is not None:
        snapped = requested.replace(minute=0, second=0, microsecond=0)
        if snapped.hour % SLOT_HOURS:
            snapped -= timedelta(hours=snapped.hour % SLOT_HOURS)
        slot = make_slot(snapped)
        free = free_technicians_for_slot(slot.start_iso, booked)
        tech = pick_technician(free)
        if tech:
            return slot, tech
        if require_requested_slot or slot_start:
            raise ValueError(
                f"No technician free at {slot.start_iso}. Offer another slot from check_availability."
            )

    pref_hours = _preference_hours(availability)
    search_starts: list[datetime] = []
    seen: set[str] = set()

    for start in iter_slot_starts(now=now, days_ahead=14):
        if pref_hours is not None and start.hour not in pref_hours:
            continue
        key = start.isoformat()
        if key not in seen:
            seen.add(key)
            search_starts.append(start)

    for start in iter_slot_starts(now=now, days_ahead=14):
        key = start.isoformat()
        if key not in seen:
            seen.add(key)
            search_starts.append(start)

    for start in search_starts:
        if start.weekday() not in WORK_DAYS:
            continue
        if not (WORK_START_HOUR <= start.hour < WORK_END_HOUR):
            continue
        slot = make_slot(start)
        free = free_technicians_for_slot(slot.start_iso, booked)
        tech = pick_technician(free)
        if tech:
            return slot, tech

    raise ValueError("No open technician slots in the next two weeks")


def format_spoken_confirmation(
    *,
    technician: str,
    slot: TimeSlot,
    confirmation_id: str,
) -> str:
    """Voice-friendly confirmation line for Alex."""
    local = slot.start.astimezone(SCHEDULE_TZ)
    day = local.strftime("%A")
    # 2pm style without leading zero
    hour = local.strftime("%I").lstrip("0") or "0"
    minute = local.minute
    if minute == 0:
        when = f"{day} at {hour}{local.strftime('%p').lower()}"
    else:
        when = f"{day} at {hour}:{minute:02d}{local.strftime('%p').lower()}"
    return f"{technician} will visit {when} — confirmation {confirmation_id}"
