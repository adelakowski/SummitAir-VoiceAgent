"""Phase 4 gate: conversation prompts and guardrails."""

from __future__ import annotations

from pathlib import Path

from app.prompts.loader import load_guardrails, load_script, load_system_prompt


def test_system_prompt_defines_alex_persona():
    text = load_system_prompt()
    assert "Alex" in text
    assert "Summit Air" in text
    assert "one" in text.lower() and "question" in text.lower()


def test_evacuate_gas_script_is_safety_first():
    text = load_script("evacuate_gas")
    lowered = text.lower()
    assert "911" in text or "911" in lowered
    assert "evacuat" in lowered
    # Safety before booking: script should not push scheduling first
    assert "schedule your appointment" not in lowered


def test_priority_empathy_script_exists():
    text = load_script("priority_empathy")
    assert len(text.strip()) > 20


def test_guardrails_json_has_required_keys():
    data = load_guardrails()
    for key in (
        "irrelevant_query_pivot",
        "address_refusal_explanation",
        "competitor_pricing_response",
        "never_do",
    ):
        assert key in data
    assert isinstance(data["never_do"], list)
    assert len(data["never_do"]) >= 1
    pivot = data["competitor_pricing_response"]
    assert "Summit Air" in pivot or "scheduling" in pivot.lower()


def test_prompt_assets_exist_on_disk():
    root = Path(__file__).resolve().parents[2]
    assert (root / "prompts" / "system_alex.md").is_file()
    assert (root / "prompts" / "scripts" / "evacuate_gas.md").is_file()
    assert (root / "prompts" / "guardrails.json").is_file()
