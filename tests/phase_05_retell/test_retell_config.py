"""Phase 5 gate: Retell agent/tools configuration artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from app.retell.validate_config import validate_agent_config

ROOT = Path(__file__).resolve().parents[2]
RETELL = ROOT / "retell"


def test_agent_config_file_exists_and_names_alex():
    path = RETELL / "agent_config.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    blob = json.dumps(data).lower()
    assert "alex" in blob
    assert "summit" in blob
    assert data.get("beginning_message") or data.get("begin_message") or data.get(
        "general_prompt"
    )


def test_agent_config_supports_english_and_spanish():
    data = json.loads((RETELL / "agent_config.json").read_text(encoding="utf-8"))
    language = data.get("language")
    if isinstance(language, str):
        languages = [language]
    else:
        languages = list(language or [])
    assert "en-US" in languages
    assert "es-419" in languages or "es-ES" in languages
    begin = str(data.get("beginning_message") or "")
    assert "español" in begin.lower() or "spanish" in begin.lower()


def test_tools_json_lists_all_five_tools():
    path = RETELL / "tools.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    tools = data if isinstance(data, list) else data.get("tools", [])
    names = {t["name"] for t in tools}
    expected = {
        "escalate_emergency",
        "flag_priority",
        "mock_schedule",
        "check_availability",
        "classify_urgency",
    }
    assert expected.issubset(names)


def test_tool_urls_point_at_webhook_paths():
    data = json.loads((RETELL / "tools.json").read_text(encoding="utf-8"))
    tools = data if isinstance(data, list) else data.get("tools", [])
    for tool in tools:
        url = tool.get("url") or tool.get("webhook_url") or ""
        assert f"/webhooks/retell/{tool['name']}" in url.replace("{{WEBHOOK_BASE_URL}}", "")


def test_validate_agent_config_returns_no_errors():
    errors = validate_agent_config(RETELL / "agent_config.json")
    assert errors == []


def test_operator_begin_doc_exists():
    begin = RETELL / "BEGIN.md"
    assert begin.is_file()
    text = begin.read_text(encoding="utf-8").lower()
    assert "twilio" in text
    assert "retell" in text
    assert "webhook" in text
