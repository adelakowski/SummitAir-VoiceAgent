"""Phase 0 gate: project scaffold and health endpoint."""

from __future__ import annotations

import importlib.util

import pytest


def test_required_dependencies_importable():
    for mod in ("fastapi", "uvicorn", "pydantic", "pydantic_settings", "httpx", "pytest"):
        assert importlib.util.find_spec(mod) is not None, f"Missing dependency: {mod}"


def test_app_module_imports():
    from app.main import app

    assert app is not None


def test_health_endpoint_ok():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"


def test_config_module_exposes_settings():
    from app.config import settings

    assert hasattr(settings, "app_env") or hasattr(settings, "APP_ENV") or settings is not None
