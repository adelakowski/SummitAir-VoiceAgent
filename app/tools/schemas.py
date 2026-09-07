"""Pydantic schemas for mock tool inputs (shared by handlers and webhooks)."""



from __future__ import annotations



from typing import Literal, Optional



from pydantic import BaseModel, Field





class EscalateEmergencyInput(BaseModel):

    call_id: str

    hazard_summary: str

    caller_phone: Optional[str] = None





class FlagPriorityInput(BaseModel):

    call_id: str

    reason: str

    address: Optional[str] = None

    availability: Optional[str] = None





class MockScheduleInput(BaseModel):

    call_id: str

    name: str

    address: str

    property_type: str

    availability: str

    urgency: Literal["standard", "low"]

    slot_start: Optional[str] = None





class CheckAvailabilityInput(BaseModel):

    urgency: str = "standard"

    zip_code: Optional[str] = None

    address: Optional[str] = None





class ClassifyUrgencyInput(BaseModel):

    gas_or_co_suspected: bool = False

    no_heat: bool = False

    no_ac: bool = False

    vulnerable_resident: bool = False

    is_winter: bool = False

    is_summer: bool = False

    is_maintenance_only: bool = False

    caller_notes: Optional[str] = Field(default=None)

