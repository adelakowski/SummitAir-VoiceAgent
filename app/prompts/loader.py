"""Load versioned prompt assets from the project `prompts/` directory."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    """Resolve the repository root from this file, independent of cwd."""
    # app/prompts/loader.py → parents[0]=prompts, [1]=app, [2]=repo root
    return Path(__file__).resolve().parents[2]


def _prompts_dir() -> Path:
    return _project_root() / "prompts"


@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    """Return Alex's system prompt markdown."""
    path = _prompts_dir() / "system_alex.md"
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=8)
def load_script(key: str) -> str:
    """Return a named script from `prompts/scripts/{key}.md`."""
    path = _prompts_dir() / "scripts" / f"{key}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Unknown prompt script key: {key!r} ({path})")
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_guardrails() -> dict[str, Any]:
    """Return guardrails JSON (pivot phrases and never-do list)."""
    path = _prompts_dir() / "guardrails.json"
    return json.loads(path.read_text(encoding="utf-8"))
