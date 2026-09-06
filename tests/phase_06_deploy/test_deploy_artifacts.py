"""Phase 6 gate: Docker and Cloud Run deploy artifacts (static)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_runs_uvicorn_on_8080():
    docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "uvicorn" in docker
    assert "8080" in docker
    assert "app.main:app" in docker.replace(" ", "")


def test_dockerignore_excludes_venv_and_git():
    text = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert ".git" in text
    assert ".venv" in text or "venv" in text


def test_deploy_script_uses_gcloud_run():
    candidates = [
        ROOT / "scripts" / "deploy_cloud_run.sh",
        ROOT / "scripts" / "deploy_cloud_run.ps1",
    ]
    existing = [p for p in candidates if p.is_file()]
    assert existing, "Expected scripts/deploy_cloud_run.sh or .ps1"
    body = "\n".join(p.read_text(encoding="utf-8") for p in existing)
    assert "gcloud" in body
    assert "run" in body
    assert "deploy" in body


def test_deployment_doc_covers_tradeoffs_and_env():
    doc = (ROOT / "docs" / "deployment.md").read_text(encoding="utf-8").lower()
    assert "cloud run" in doc
    assert "retell" in doc
    assert "webhook" in doc
    assert "app_env" in doc or "log_level" in doc or "environment" in doc


def test_github_actions_ci_cd_workflow_exists():
    workflow = ROOT / ".github" / "workflows" / "ci-cd.yml"
    assert workflow.is_file(), "Expected .github/workflows/ci-cd.yml"
    body = workflow.read_text(encoding="utf-8").lower()
    assert "pytest" in body
    assert "docker" in body
    assert "cloud run" in body or "run deploy" in body
