"""Retell custom-tool HTTP webhooks (PRD §7.8)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.deps import get_store
from app.domain.models import TriageSignals
from app.domain.triage import classify_urgency
from app.tools.handlers import (
    ToolValidationError,
    check_availability,
    escalate_emergency,
    flag_priority,
    mock_schedule,
)

router = APIRouter(prefix="/webhooks/retell", tags=["retell"])


def normalize_tool_args(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept flat tool args or Retell envelopes with nested `args`.

    Envelope shapes: ``{"name": "<tool>", "args": {...}}`` or
    ``{"call": {...}, "args": {...}}``. Flat payloads (including a customer
    ``name`` field for booking) pass through unchanged.
    """
    if not isinstance(payload, dict):
        return {}
    nested = payload.get("args")
    if isinstance(nested, dict):
        return dict(nested)
    return dict(payload)


async def _json_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        return {}
    return body if isinstance(body, dict) else {}


@router.post("/escalate_emergency")
async def escalate_emergency_webhook(request: Request) -> Any:
    args = normalize_tool_args(await _json_body(request))
    try:
        return escalate_emergency(args, store=get_store())
    except ToolValidationError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})


@router.post("/flag_priority")
async def flag_priority_webhook(request: Request) -> Any:
    args = normalize_tool_args(await _json_body(request))
    try:
        return flag_priority(args, store=get_store())
    except ToolValidationError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})


@router.post("/mock_schedule")
async def mock_schedule_webhook(request: Request) -> Any:
    args = normalize_tool_args(await _json_body(request))
    try:
        return mock_schedule(args, store=get_store())
    except ToolValidationError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})


@router.post("/check_availability")
async def check_availability_webhook(request: Request) -> Any:
    args = normalize_tool_args(await _json_body(request))
    try:
        return check_availability(args, store=get_store())
    except ToolValidationError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})


@router.post("/classify_urgency")
async def classify_urgency_webhook(request: Request) -> Any:
    args = normalize_tool_args(await _json_body(request))
    try:
        signals = TriageSignals.model_validate(args)
    except Exception as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
    result = classify_urgency(signals)
    return result.model_dump(mode="json")
