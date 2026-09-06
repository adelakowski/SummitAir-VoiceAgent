"""Triage domain enums and models (PRD §3)."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class UrgencyLevel(str, Enum):
    CRITICAL_SAFETY = "CRITICAL_SAFETY"
    HIGH_PRIORITY = "HIGH_PRIORITY"
    STANDARD = "STANDARD"
    LOW_PRIORITY = "LOW_PRIORITY"


RecommendedTool = Literal["escalate_emergency", "flag_priority", "mock_schedule"]


class TriageSignals(BaseModel):
    """Observable call signals used for deterministic urgency classification."""

    gas_or_co_suspected: bool = False
    no_heat: bool = False
    no_ac: bool = False
    vulnerable_resident: bool = False
    is_winter: bool = False
    is_summer: bool = False
    is_maintenance_only: bool = False
    caller_notes: Optional[str] = None


class TriageResult(BaseModel):
    """Outcome of `classify_urgency`."""

    urgency: UrgencyLevel
    reason: str
    recommended_tool: RecommendedTool
    immediate_script_key: Optional[str] = Field(
        default=None,
        description="Key for an immediate safety script, e.g. evacuate_gas.",
    )
