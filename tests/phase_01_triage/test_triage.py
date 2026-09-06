"""Phase 1 gate: urgency triage classification (PRD §3)."""

from __future__ import annotations

import pytest

from app.domain.models import TriageSignals, UrgencyLevel
from app.domain.triage import classify_urgency


def test_gas_or_co_is_critical_safety():
    result = classify_urgency(TriageSignals(gas_or_co_suspected=True))
    assert result.urgency == UrgencyLevel.CRITICAL_SAFETY
    assert result.recommended_tool == "escalate_emergency"
    assert result.immediate_script_key == "evacuate_gas"


def test_no_heat_winter_vulnerable_is_high_priority():
    result = classify_urgency(
        TriageSignals(no_heat=True, is_winter=True, vulnerable_resident=True)
    )
    assert result.urgency == UrgencyLevel.HIGH_PRIORITY
    assert result.recommended_tool == "flag_priority"
    assert result.immediate_script_key is None


def test_no_ac_summer_vulnerable_is_high_priority():
    result = classify_urgency(
        TriageSignals(no_ac=True, is_summer=True, vulnerable_resident=True)
    )
    assert result.urgency == UrgencyLevel.HIGH_PRIORITY
    assert result.recommended_tool == "flag_priority"


def test_maintenance_is_low_priority():
    result = classify_urgency(TriageSignals(is_maintenance_only=True))
    assert result.urgency == UrgencyLevel.LOW_PRIORITY
    assert result.recommended_tool == "mock_schedule"


def test_standard_break_fix_default():
    result = classify_urgency(TriageSignals(no_heat=True, is_winter=False, vulnerable_resident=False))
    assert result.urgency == UrgencyLevel.STANDARD
    assert result.recommended_tool == "mock_schedule"


def test_critical_safety_outranks_other_signals():
    result = classify_urgency(
        TriageSignals(
            gas_or_co_suspected=True,
            no_heat=True,
            is_winter=True,
            vulnerable_resident=True,
            is_maintenance_only=True,
        )
    )
    assert result.urgency == UrgencyLevel.CRITICAL_SAFETY
    assert result.recommended_tool == "escalate_emergency"


@pytest.mark.parametrize(
    "signals",
    [
        TriageSignals(no_heat=True, is_winter=True, vulnerable_resident=False),
        TriageSignals(no_ac=True, is_summer=True, vulnerable_resident=False),
    ],
)
def test_environmental_without_vulnerability_is_not_high_priority(signals):
    result = classify_urgency(signals)
    assert result.urgency != UrgencyLevel.HIGH_PRIORITY
