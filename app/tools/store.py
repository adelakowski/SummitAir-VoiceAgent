"""In-memory store for mock bookings, priority tickets, and escalations."""

from __future__ import annotations

from copy import deepcopy
from threading import Lock
from typing import Any


class InMemoryStore:
    """Process-local store shared by tool handlers (tests inject fresh instances)."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._bookings: list[dict[str, Any]] = []
        self._escalations: list[dict[str, Any]] = []
        self._priority_tickets: list[dict[str, Any]] = []

    def add_booking(self, booking: dict[str, Any]) -> None:
        with self._lock:
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
