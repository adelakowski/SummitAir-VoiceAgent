"""Phase 3 gate: FastAPI Retell webhook routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_still_ok(client):
    assert client.get("/health").status_code == 200


def test_escalate_emergency_endpoint(client):
    res = client.post(
        "/webhooks/retell/escalate_emergency",
        json={"call_id": "w1", "hazard_summary": "gas smell"},
    )
    assert res.status_code == 200
    assert res.json()["escalated"] is True


def test_flag_priority_endpoint(client):
    res = client.post(
        "/webhooks/retell/flag_priority",
        json={"call_id": "w2", "reason": "no heat elderly"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["priority"] == "high"
    assert "emergency_slot" in body


def test_mock_schedule_endpoint_validation(client):
    res = client.post(
        "/webhooks/retell/mock_schedule",
        json={"call_id": "w3", "name": "Only Name"},
    )
    assert res.status_code == 422


def test_mock_schedule_endpoint_success(client):
    res = client.post(
        "/webhooks/retell/mock_schedule",
        json={
            "call_id": "w4",
            "name": "Pat Lee",
            "address": "12 Pine St",
            "property_type": "residential",
            "availability": "Fri PM",
            "urgency": "low",
        },
    )
    assert res.status_code == 200
    assert "confirmation_id" in res.json()


def test_check_availability_endpoint(client):
    res = client.post(
        "/webhooks/retell/check_availability",
        json={"zip_code": "80301", "urgency": "standard"},
    )
    assert res.status_code == 200
    assert len(res.json()["slots"]) >= 2


def test_classify_urgency_endpoint(client):
    res = client.post(
        "/webhooks/retell/classify_urgency",
        json={"gas_or_co_suspected": True},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["urgency"] in {"CRITICAL_SAFETY", "critical_safety"} or "CRITICAL" in str(
        body["urgency"]
    ).upper()
    assert body["recommended_tool"] == "escalate_emergency"


def test_retell_envelope_args_supported(client):
    res = client.post(
        "/webhooks/retell/flag_priority",
        json={"name": "flag_priority", "args": {"call_id": "env1", "reason": "priority"}},
    )
    assert res.status_code == 200
    assert res.json()["priority"] == "high"
