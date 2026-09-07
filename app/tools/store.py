"""Booking store — in-memory (tests) or SQLite (runtime persistence)."""

from __future__ import annotations

import sqlite3
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any, Optional, Protocol, Sequence


class BookingStore(Protocol):
    def add_booking(self, booking: dict[str, Any]) -> None: ...

    def add_escalation(self, escalation: dict[str, Any]) -> None: ...

    def add_priority_ticket(self, ticket: dict[str, Any]) -> None: ...

    def list_bookings(self) -> list[dict[str, Any]]: ...

    def list_escalations(self) -> list[dict[str, Any]]: ...

    def list_priority_tickets(self) -> list[dict[str, Any]]: ...

    def list_booked_tech_slots(self) -> list[tuple[str, str]]: ...


class InMemoryStore:
    """Process-local store shared by tool handlers (tests inject fresh instances)."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._bookings: list[dict[str, Any]] = []
        self._escalations: list[dict[str, Any]] = []
        self._priority_tickets: list[dict[str, Any]] = []

    def add_booking(self, booking: dict[str, Any]) -> None:
        with self._lock:
            tech = booking.get("technician")
            start = booking.get("slot_start")
            if tech and start:
                for existing in self._bookings:
                    if existing.get("technician") == tech and existing.get("slot_start") == start:
                        raise ValueError(f"Slot already booked for {tech} at {start}")
            self._bookings.append(deepcopy(booking))

    def add_escalation(self, escalation: dict[str, Any]) -> None:
        with self._lock:
            self._escalations.append(deepcopy(escalation))

    def add_priority_ticket(self, ticket: dict[str, Any]) -> None:
        with self._lock:
            self._priority_tickets.append(deepcopy(ticket))

    def list_bookings(self) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(self._bookings)

    def list_escalations(self) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(self._escalations)

    def list_priority_tickets(self) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(self._priority_tickets)

    def list_booked_tech_slots(self) -> list[tuple[str, str]]:
        with self._lock:
            out: list[tuple[str, str]] = []
            for b in self._bookings:
                tech = b.get("technician")
                start = b.get("slot_start")
                if tech and start:
                    out.append((str(tech), str(start)))
            return out


_SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    confirmation_id TEXT PRIMARY KEY,
    call_id TEXT,
    name TEXT,
    address TEXT,
    property_type TEXT,
    availability TEXT,
    urgency TEXT,
    technician TEXT NOT NULL,
    slot_start TEXT NOT NULL,
    slot_end TEXT NOT NULL,
    priority TEXT,
    window TEXT,
    spoken_confirmation TEXT,
    ticket_id TEXT,
    reason TEXT,
    payload_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_bookings_tech_slot
    ON bookings(technician, slot_start);

CREATE TABLE IF NOT EXISTS escalations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS priority_tickets (
    ticket_id TEXT PRIMARY KEY,
    call_id TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


class SqliteStore:
    """SQLite-backed schedule store (John/Paul/George slot locks survive restarts)."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.executescript(_SCHEMA)
                conn.commit()

    def add_booking(self, booking: dict[str, Any]) -> None:
        import json

        with self._lock:
            with self._connect() as conn:
                try:
                    conn.execute(
                        """
                        INSERT INTO bookings (
                            confirmation_id, call_id, name, address, property_type,
                            availability, urgency, technician, slot_start, slot_end,
                            priority, window, spoken_confirmation, ticket_id, reason,
                            payload_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            booking.get("confirmation_id"),
                            booking.get("call_id"),
                            booking.get("name"),
                            booking.get("address"),
                            booking.get("property_type"),
                            booking.get("availability"),
                            booking.get("urgency"),
                            booking["technician"],
                            booking["slot_start"],
                            booking.get("slot_end"),
                            booking.get("priority"),
                            booking.get("window"),
                            booking.get("spoken_confirmation"),
                            booking.get("ticket_id"),
                            booking.get("reason"),
                            json.dumps(booking),
                        ),
                    )
                    conn.commit()
                except sqlite3.IntegrityError as exc:
                    raise ValueError(
                        f"Slot already booked for {booking.get('technician')} "
                        f"at {booking.get('slot_start')}"
                    ) from exc

    def add_escalation(self, escalation: dict[str, Any]) -> None:
        import json

        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO escalations (call_id, payload_json) VALUES (?, ?)",
                    (escalation.get("call_id"), json.dumps(escalation)),
                )
                conn.commit()

    def add_priority_ticket(self, ticket: dict[str, Any]) -> None:
        import json

        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO priority_tickets (ticket_id, call_id, payload_json)
                    VALUES (?, ?, ?)
                    """,
                    (ticket.get("ticket_id"), ticket.get("call_id"), json.dumps(ticket)),
                )
                conn.commit()

    def list_bookings(self) -> list[dict[str, Any]]:
        import json

        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT payload_json FROM bookings ORDER BY slot_start"
                ).fetchall()
        return [json.loads(r["payload_json"]) for r in rows]

    def list_escalations(self) -> list[dict[str, Any]]:
        import json

        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT payload_json FROM escalations ORDER BY id"
                ).fetchall()
        return [json.loads(r["payload_json"]) for r in rows]

    def list_priority_tickets(self) -> list[dict[str, Any]]:
        import json

        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT payload_json FROM priority_tickets ORDER BY created_at"
                ).fetchall()
        return [json.loads(r["payload_json"]) for r in rows]

    def list_booked_tech_slots(self) -> list[tuple[str, str]]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT technician, slot_start FROM bookings"
                ).fetchall()
        return [(str(r["technician"]), str(r["slot_start"])) for r in rows]


def create_store(db_path: Optional[str] = None) -> InMemoryStore | SqliteStore:
    """Factory: empty path → in-memory; otherwise SQLite file."""
    if not db_path:
        return InMemoryStore()
    return SqliteStore(db_path)
