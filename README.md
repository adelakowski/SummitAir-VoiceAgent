# Summit Air Voice Agent

> **Master file:** [`PRD.md`](PRD.md) — product requirements **and** full phase-gated agent prompts (§7).  
> **Live status:** [`PROGRESS.txt`](PROGRESS.txt)

Inbound HVAC dispatch voice agent for Summit Air (Retell AI + FastAPI webhooks).

## Phase status

| Phase | Name | Status |
| --- | --- | --- |
| 0 | Scaffold | DONE |
| 1–7 | Remaining | NOT_STARTED |

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8080
pytest tests/phase_00_scaffold/ -v
```
