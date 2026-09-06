"""Phase 7 gate: QA scenarios from PRD §6.2 (logic-level)."""

from __future__ import annotations

from pathlib import Path

from app.domain.models import TriageSignals, UrgencyLevel
from app.qa.scenarios import (
    run_emergency_no_heat,
    run_golden_path_maintenance,
    run_hostile_distracted_guardrails,
    run_safety_hazard_gas,
)


ROOT = Path(__file__).resolve().parents[2]


def test_golden_path_maintenance():
    outcome = run_golden_path_maintenance()
    assert outcome["urgency"] == UrgencyLevel.LOW_PRIORITY
    assert outcome["booking"]["confirmation_id"]
    assert outcome["escalations"] == []


def test_emergency_no_heat_vulnerable():
    outcome = run_emergency_no_heat()
    assert outcome["urgency"] == UrgencyLevel.HIGH_PRIORITY
    assert outcome["priority_ticket"]["priority"] == "high"
    assert "emergency_slot" in outcome["priority_ticket"]


def test_safety_hazard_gas():
    outcome = run_safety_hazard_gas()
    assert outcome["urgency"] == UrgencyLevel.CRITICAL_SAFETY
    assert outcome["escalation"]["escalated"] is True
    msg = outcome["escalation"]["message"].lower()
    assert "911" in msg or "evacuat" in msg
    assert outcome["bookings"] == []


def test_hostile_distracted_guardrails_standin():
    outcome = run_hostile_distracted_guardrails()
    assert "Summit Air" in outcome["competitor_pivot"] or "scheduling" in outcome[
        "competitor_pivot"
    ].lower()
    assert len(outcome["address_refusal"]) > 10
    assert outcome["manual_barge_in_documented"] is True


def test_manual_call_checklist_exists():
    path = ROOT / "docs" / "manual_call_checklist.md"
    text = path.read_text(encoding="utf-8").lower()
    for needle in ("golden path", "emergency", "gas", "interrupt"):
        assert needle in text


def test_triage_signals_used_by_scenarios_are_importable():
    # sanity: scenarios module aligned with domain models
    assert TriageSignals(is_maintenance_only=True)
