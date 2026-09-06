"""Validate Retell agent config artifacts (static, no network)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union


def validate_agent_config(path: Union[str, Path]) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors: list[str] = []
    p = Path(path)
    if not p.is_file():
        return [f"agent config not found: {p}"]

    try:
        data: Any = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    if not isinstance(data, dict):
        return ["agent config root must be a JSON object"]

    name = str(data.get("agent_name") or data.get("name") or "")
    if "alex" not in name.lower() and "alex" not in json.dumps(data).lower():
        errors.append("agent config must reference Alex")

    begin = (
        data.get("beginning_message")
        or data.get("begin_message")
        or data.get("general_prompt")
    )
    if not begin or not str(begin).strip():
        errors.append("beginning_message / begin_message / general_prompt is required")

    blob = json.dumps(data).lower()
    if "summit" not in blob:
        errors.append("agent config must mention Summit Air")

    return errors
