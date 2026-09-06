# Summit Air Inbound Voice Agent



Forward Deployed Engineering (FDE) prototype for **Revin**: an inbound HVAC voice agent that triages Summit Air callers, handles life-safety escalation, prioritizes vulnerable residents, and mock-books standard jobs — with ultra-low latency and barge-in via **Retell AI**, backed by a **FastAPI** webhook on **Cloud Run**.



> **Master file:** [`PRD.md`](PRD.md) — product requirements **and** full phase-gated agent prompts (§7).  

> **Live status:** [`PROGRESS.txt`](PROGRESS.txt) — **READY FOR REVIEW**.



## Status



| Phase | Name | Status |

| --- | --- | --- |

| 0 | Scaffold | DONE |

| 1 | Triage classification | DONE |

| 2 | Mock tool handlers | DONE |

| 3 | Retell HTTP webhooks | DONE |

| 4 | Conversation prompts | DONE |

| 5 | Retell + telephony config | DONE |

| 6 | Docker / Cloud Run | DONE |

| 7 | QA scenarios + delivery | DONE |



## What This Is



Alex answers Summit Air inbound HVAC calls during seasonal volume spikes: classify urgency, escalate gas/CO, prioritize no-heat/no-AC with vulnerable residents, and mock-book routine jobs. Speaks English and Spanish (`en-US` + `es-419`). V1 deliberately skips ServiceTitan and live calendars (PRD §2).



## Architecture



```text

Caller → Twilio → Retell AI (STT/TTS/endpointing/barge-in)

                      │ custom LLM tool calls

                      ▼

              FastAPI on Cloud Run  /webhooks/retell/*

                 classify_urgency · flag_priority · mock_schedule

                 escalate_emergency · check_availability

```



- **Retell** owns voice quality and interruptions; this repo owns deterministic triage + mock tools.

- **Cloud Run** serves webhooks serverless; see [`docs/deployment.md`](docs/deployment.md).



## FDE Trade-offs



| Chose | Deferred |

| --- | --- |

| Retell orchestration (latency + barge-in) | Custom WebRTC / WS event loops |

| In-memory mock booking | ServiceTitan / live tech calendar |

| Deterministic `classify_urgency` rules | LLM-only triage without tests |

| Unauth Cloud Run OK for demo | Production IAM / signed webhooks |



## Quickstart



```bash

python -m venv .venv

# Windows: .venv\Scripts\activate

# macOS/Linux: source .venv/bin/activate



pip install -r requirements-dev.txt

cp .env.example .env



uvicorn app.main:app --reload --port 8080

# GET http://127.0.0.1:8080/health → {"status":"ok"}

```



## Tests



```bash

pip install -r requirements-dev.txt

pytest tests/phase_07_qa_delivery/ -v

pytest tests/ -v

```



Logic scenarios live in `app/qa/scenarios.py` (golden path, emergency, gas, guardrails). Live barge-in is manual only — do not fake WebRTC in unit tests.



## CI/CD



GitHub Actions (`.github/workflows/ci-cd.yml`): on every PR/push to `main`, run the full pytest suite and a Docker image build. On push to `main`, deploy to Cloud Run when `GCP_PROJECT_ID` and GCP auth secrets are set (see [`docs/deployment.md`](docs/deployment.md)).



## How to Demo



1. Deploy webhooks (`scripts/deploy_cloud_run.ps1` or `.sh`) and set `WEBHOOK_BASE_URL`.

2. Follow [`retell/BEGIN.md`](retell/BEGIN.md) — Twilio number → Retell agent `summit-air-alex` → tool URLs.

3. Run [`docs/manual_call_checklist.md`](docs/manual_call_checklist.md): golden path, emergency, gas/CO, interrupt/hostile.

4. Optional: `pytest tests/phase_07_qa_delivery/ -v` for the logic harness.



## Persona



**Alex** — Summit Air dispatch assistant (English + Spanish; prompts in `prompts/` and `prompts/es/`; PRD §5).


