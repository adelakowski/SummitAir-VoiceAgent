"""Prompt asset loaders for Alex system prompt, scripts, and guardrails."""

from app.prompts.loader import (
    SUPPORTED_LOCALES,
    load_guardrails,
    load_script,
    load_system_prompt,
)

__all__ = [
    "SUPPORTED_LOCALES",
    "load_guardrails",
    "load_script",
    "load_system_prompt",
]
