"""Logic-level QA scenarios from PRD §6.2 (no live telephony / WebRTC)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.domain.models import TriageSignals
from app.domain.triage import classify_urgency
from app.prompts.loader import load_guardrails
from app.tools.handlers import escalate_emergency, flag_priority, mock_schedule
from app.tools.store import InMemoryStore

ROOT = Path(__file__).resolve().parents[2]


def run_golden_path_maintenance() -> dict[str, Any]:
    """Routine tune-up → LOW_PRIORITY → mock_schedule confirmation."""
    store = InMemoryStore()
    triage = classify_urgency(TriageSignals(is_maintenance_only=True))
    booking = mock_schedule(
        {
            "call_id": "qa-golden-1",
            "name": "Jordan Reyes",
            "address": "88 Maple Ave",
            "property_type": "residential",
            "availability": "Saturday morning",
            "urgency": "low",
        },
        store=store,
    )
    return {
        "urgency": triage.urgency,
        "recommended_tool": triage.recommended_tool,
        "booking": booking,
        "escalations": store.list_escalations(),
    }


def run_emergency_no_heat() -> dict[str, Any]:
    """No heat + winter + vulnerable → HIGH_PRIORITY → flag_priority slot."""
    store = InMemoryStore()
    triage = classify_urgency(
        TriageSignals(
            no_heat=True,
            is_winter=True,
            vulnerable_resident=True,
        )
    )
    ticket = flag_priority(
        {
            "call_id": "qa-emergency-1",
            "reason": "no heat, elderly resident, freezing",
            "address": "12 Pine St",
        },
        store=store,
    )
    return {
        "urgency": triage.urgency,
        "recommended_tool": triage.recommended_tool,
        "priority_ticket": ticket,
    }


def run_safety_hazard_gas() -> dict[str, Any]:
    """Gas/CO → CRITICAL_SAFETY → escalate; no normal booking."""
    store = InMemoryStore()
    triage = classify_urgency(TriageSignals(gas_or_co_suspected=True))
    escalation = escalate_emergency(
        {
            "call_id": "qa-gas-1",
            "hazard_summary": "strong smell of gas near furnace",
            "caller_phone": "+15550001111",
        },
        store=store,
    )
    return {
        "urgency": triage.urgency,
        "recommended_tool": triage.recommended_tool,
        "escalation": escalation,
        "bookings": store.list_bookings(),
    }


def run_hostile_distracted_guardrails() -> dict[str, Any]:
    """Competitor pivot + address refusal text; barge-in via manual checklist."""
    guardrails = load_guardrails()
    competitor_pivot = (
        guardrails.get("competitor_pricing_response")
        or guardrails.get("irrelevant_query_pivot")
        or ""
    )
    address_refusal = guardrails.get("address_refusal_explanation") or ""
    checklist = ROOT / "docs" / "manual_call_checklist.md"
    checklist_text = checklist.read_text(encoding="utf-8").lower() if checklist.is_file() else ""
    barge_documented = "interrupt" in checklist_text or "barge" in checklist_text
    return {
        "competitor_pivot": competitor_pivot,
        "address_refusal": address_refusal,
        "manual_barge_in_documented": barge_documented,
    }
