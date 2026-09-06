"""Deterministic urgency classification (PRD §3). Highest matching rule wins."""

from __future__ import annotations

from app.domain.models import TriageResult, TriageSignals, UrgencyLevel


def classify_urgency(signals: TriageSignals) -> TriageResult:
    """Classify caller urgency from structured triage signals.

    Priority order:
    1. Gas / CO → CRITICAL_SAFETY
    2. Extreme temp + vulnerable (seasonal) → HIGH_PRIORITY
    3. Maintenance only → LOW_PRIORITY
    4. Else → STANDARD
    """
    if signals.gas_or_co_suspected:
        return TriageResult(
            urgency=UrgencyLevel.CRITICAL_SAFETY,
            reason="Gas smell or carbon monoxide suspected; evacuate and escalate.",
            recommended_tool="escalate_emergency",
            immediate_script_key="evacuate_gas",
        )

    heat_vulnerable = (
        signals.no_heat and signals.is_winter and signals.vulnerable_resident
    )
    ac_vulnerable = (
        signals.no_ac and signals.is_summer and signals.vulnerable_resident
    )
    if heat_vulnerable or ac_vulnerable:
        if heat_vulnerable:
            reason = "No heat in winter with a vulnerable resident."
        else:
            reason = "No AC in summer with a vulnerable resident."
        return TriageResult(
            urgency=UrgencyLevel.HIGH_PRIORITY,
            reason=reason,
            recommended_tool="flag_priority",
            immediate_script_key=None,
        )

    if signals.is_maintenance_only:
        return TriageResult(
            urgency=UrgencyLevel.LOW_PRIORITY,
            reason="Routine maintenance request.",
            recommended_tool="mock_schedule",
            immediate_script_key=None,
        )

    return TriageResult(
        urgency=UrgencyLevel.STANDARD,
        reason="Standard break/fix or service request.",
        recommended_tool="mock_schedule",
        immediate_script_key=None,
    )
