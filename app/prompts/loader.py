"""Load versioned prompt assets from the project `prompts/` directory."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

Locale = Literal["en", "es"]
SUPPORTED_LOCALES: tuple[Locale, ...] = ("en", "es")


def _project_root() -> Path:
    """Resolve the repository root from this file, independent of cwd."""
    # app/prompts/loader.py → parents[0]=prompts, [1]=app, [2]=repo root
    return Path(__file__).resolve().parents[2]


def _prompts_dir(locale: Locale = "en") -> Path:
    root = _project_root() / "prompts"
    if locale == "en":
        return root
    return root / locale


def _normalize_locale(locale: str) -> Locale:
    code = locale.strip().lower().replace("_", "-")
    if code in ("en", "en-us", "en-gb"):
        return "en"
    if code in ("es", "es-419", "es-es", "es-mx", "es-us"):
        return "es"
    raise ValueError(f"Unsupported prompt locale: {locale!r}")


@lru_cache(maxsize=4)
def load_system_prompt(locale: str = "en") -> str:
    """Return Alex's system prompt markdown for the given locale."""
    loc = _normalize_locale(locale)
    path = _prompts_dir(loc) / "system_alex.md"
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=16)
def load_script(key: str, locale: str = "en") -> str:
    """Return a named script from `prompts[/es]/scripts/{key}.md`."""
    loc = _normalize_locale(locale)
    path = _prompts_dir(loc) / "scripts" / f"{key}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Unknown prompt script key: {key!r} ({path})")
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=4)
def load_guardrails(locale: str = "en") -> dict[str, Any]:
    """Return guardrails JSON (pivot phrases and never-do list)."""
    loc = _normalize_locale(locale)
    path = _prompts_dir(loc) / "guardrails.json"
    return json.loads(path.read_text(encoding="utf-8"))
