# Deployment — Summit Air Voice Agent



## Why Retell + Cloud Run



PRD §2 trade-off: a 24-hour FDE prototype prioritizes ultra-low latency, natural turn-taking, and barge-in over building a custom WebRTC/WebSocket voice stack. **Retell AI** owns telephony (Twilio), STT/TTS, endpointing, and interruption handling. This repo ships a thin **FastAPI** webhook service that executes triage and mock booking tools.



**Google Cloud Run** hosts that webhook with minimal ops: containerize, deploy, scale to zero. No always-on VM for a prototype traffic profile.



## Mock booking



`mock_schedule` and `check_availability` are in-memory mocks (see `app/tools/`). They prove the call flow and confirmation UX without ServiceTitan or a live technician calendar (deferred to V2). Priority and emergency paths use `flag_priority` / `escalate_emergency` and never treat gas/CO as a normal booking.



## Environment variables



| Variable | Purpose |

| --- | --- |

| `APP_ENV` | `development` / `production` |

| `LOG_LEVEL` | e.g. `INFO`, `DEBUG` |

| `WEBHOOK_BASE_URL` | Public origin Retell calls (no trailing slash), e.g. `https://….run.app` |

| `RETELL_API_KEY` | Retell dashboard/API only — never bake into the image |

| `PORT` | Cloud Run injects this; Dockerfile defaults to `8080` |



Copy `.env.example` locally. Do not commit `.env`.



## Deploy



```bash

# Bash

export GCP_PROJECT_ID=your-project

export WEBHOOK_BASE_URL=https://YOUR_SERVICE_URL   # set after first deploy if needed

./scripts/deploy_cloud_run.sh

```



```powershell

# PowerShell

$env:GCP_PROJECT_ID = "your-project"

.\scripts\deploy_cloud_run.ps1

```



Scripts run `gcloud builds submit` then `gcloud run deploy` with `--port=8080`.



## CI/CD (GitHub Actions)



Workflow: [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml)



| Trigger | Jobs |
| --- | --- |
| Pull request / push to `main` | **Test** (`pytest tests/`) + **Docker build** (no push) |
| Push to `main` only | **Deploy Cloud Run** (skipped until GCP is configured) |



### Required GitHub configuration for deploy



Set **one** auth method plus the project id:



| Name | Type | Purpose |
| --- | --- | --- |
| `GCP_PROJECT_ID` | variable or secret | GCP project |
| `GCP_SA_KEY` | secret | JSON key for a deploy SA (simple prototype path) |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` + `GCP_SERVICE_ACCOUNT` | secrets | Preferred WIF auth (no long-lived key) |



Optional variables/secrets: `GCP_REGION` (default `us-central1`), `CLOUD_RUN_SERVICE` (default `summit-air-voice-agent`), `ALLOW_UNAUTHENTICATED` (default `true`), `WEBHOOK_BASE_URL`.



SA needs permission to run Cloud Build, push to GCR/Artifact Registry, and deploy Cloud Run.



### Auth trade-off for Retell webhooks



- **Unauthenticated (`--allow-unauthenticated`)**: simplest for demos — Retell can POST tool calls immediately. Acceptable for a short-lived interview prototype.

- **Authenticated**: prefer for anything beyond demo — Cloud Run IAM, API gateway, or request signing. Retell must be able to present credentials; document the chosen scheme in the operator checklist (`retell/BEGIN.md`).



## Local smoke



```bash

uvicorn app.main:app --reload --port 8080

curl http://127.0.0.1:8080/health

```



After Cloud Run is live, point Retell tool URLs at `{WEBHOOK_BASE_URL}/webhooks/retell/*` (see `retell/tools.json`).


