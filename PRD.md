# Product Requirements Document (PRD): Summit Air Inbound Voice Agent

> **Master file.** Product intent, architecture, delivery QA, and the full phase-gated multi-agent implementation plan live here.  
> Live status only: [`PROGRESS.txt`](PROGRESS.txt). Interviewer overview: [`README.md`](README.md). Gate tests: `tests/phase_XX_*/`.

---

## 1. Executive Summary

Summit Air requires an automated inbound voice agent to triage customer calls during seasonal HVAC volume spikes. The agent must successfully classify caller intent, identify urgent life-safety or environmental hazards (e.g., gas leaks, extreme temperatures with vulnerable residents), collect necessary booking parameters, and route the customer accordingly.

As a Forward Deployed Engineering deliverable for Revin, this implementation prioritizes ultra-low latency, natural conversational dynamics, and robust interruption handling over complex external integrations.

---

## 2. Scope & Trade-offs (FDE Judgment)

Given the 24-hour turnaround, the architecture leverages an opinionated voice AI orchestration layer to guarantee conversation quality, avoiding the time sink of manually tuning WebRTC and WebSocket event loops.

### In-Scope (Prototype)

- Telephony provisioning
- Speech-to-Text (STT) / Text-to-Speech (TTS) pipeline
- Prompt-driven state machine
- Urgency classification
- Mock booking webhook
- Real-time interruption handling (barge-in)

### Out-of-Scope (Deferred to V2)

- Deep Field Service Management (FSM) integration (e.g., ServiceTitan)
- Real-time technician calendar polling
- Multi-lingual routing

---

## 3. Core Call Flows & Triage Logic

The agent navigates callers through a dynamic state machine, utilizing custom tool calls to classify and route based on perceived urgency.

| Hazard / Condition | Classification | Agent Action |
| --- | --- | --- |
| Gas Smell / Carbon Monoxide | Critical Safety | Immediately advise caller to evacuate and call 911/gas company. Disconnect or route to emergency human dispatcher. |
| No Heat (Winter) + Elderly/Medical | High Priority | Bypass standard booking; execute `flag_priority` tool; offer next available emergency slot. |
| No AC (Summer) + Medical Need | High Priority | Bypass standard booking; execute `flag_priority` tool; offer next available emergency slot. |
| Standard Break/Fix | Standard | Collect property type, address, name, availability; execute `mock_schedule` tool. |
| Routine Maintenance | Low Priority | Collect property type, address, name, availability; execute `mock_schedule` tool. |

---

## 4. System Architecture

To achieve sub-500ms latency and natural turn-taking, the system relies on Retell AI for telephony and orchestration, integrated with a lightweight backend for state and tool execution.

```text
Caller ──► Twilio number ──► Retell AI (STT/TTS/endpointing/barge-in)
                                   │
                                   │ custom LLM tool calls
                                   ▼
                           FastAPI on Cloud Run
                           /webhooks/retell/*
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
             classify_urgency  flag_priority  mock_schedule
             escalate_emergency              check_availability
```

- **Voice Orchestration Layer (Retell AI):** Handles SIP/Telephony (via Twilio number), endpointing, STT, and TTS. Crucially, Retell provides first-class "barge-in" and overlap detection out of the box, allowing the agent to stop speaking and listen when the user goes off-script or interrupts.
- **LLM Engine:** GPT-4o or Claude 3.5 Sonnet, configured as a custom LLM via Retell to execute strict JSON-schema tool calling for data extraction.
- **Backend Webhook:** FastAPI application to process Retell's custom tool calls (e.g., `check_availability`, `book_appointment`, `escalate_emergency`).
- **Deployment:** Containerized via Docker and deployed on Google Cloud Run for fast, serverless webhook handling without infrastructure overhead.

---

## 5. Prompting & Conversation Strategy

To ensure the agent feels like a "good experience" rather than a "robot reading a form," the system prompt enforces specific behavioral guidelines optimized for Retell's engine.

- **Persona:** "Alex," a helpful dispatch assistant for Summit Air. Empathetic, concise, and professional. Speaks English and Spanish (Latin America); matches the caller's language (`en-US` + `es-419` in Retell).
- **Pacing & Extraction:** Ask one logical question at a time. Acknowledge caller distress (e.g., "I'm so sorry your heat is out, let's get this fixed.") before moving to data collection.

### Handling the Unexpected (Off-Script Guardrails)

- **Interruptions:** Leverages Retell's native endpointing. If the caller interrupts with an address correction, the LLM context window updates instantly without dropping the thread.
- **Irrelevant Queries:** If the user asks about competitor pricing, the agent politely pivots: "I'm just the scheduling assistant for Summit Air, but I can definitely help get a technician out to look at your system. Were you needing a repair or just maintenance?"
- **Refusal to Provide Info:** If the user refuses to give an address, explain the necessity: "I completely understand, but to see which technician is in your zone, I just need a general zip code or street."

---

## 6. Delivery & Testing Plan

### 6.1 Deliverables Checklist

- [ ] **Provisioned Phone Number:** Twilio number routed through Retell AI's dashboard.
- [ ] **Repository:** Clean GitHub repo containing the FastAPI webhook code and Dockerfile.
- [ ] **README:** Clear instructions on the Cloud Run architecture, how the mock booking webhook works, and an outline of the expected FDE trade-offs made.

### 6.2 Pre-Submission Quality Assurance

- **The "Golden Path" Test:** Call and act as a standard residential customer needing a tune-up.
- **The "Emergency" Test:** Call and state there is no heat, you are 80 years old, and it is freezing. Verify the LLM triggers the `flag_priority` webhook.
- **The "Safety Hazard" Test:** Call and mention a strong smell of gas near the furnace. Verify immediate life-safety script execution.
- **The "Hostile/Distracted" Test (The Evaluator Test):** Interrupt the bot mid-sentence, ask an off-topic question, and mumble an address. Verify Retell's overlap detection catches the interruption and the agent recovers gracefully.

---

## 7. Phase-Gated Multi-Agent Implementation

Work is split into **gated phases**. Each phase has:

1. An **agent prompt** in this document (copy the whole phase subsection into a new agent session)
2. **Acceptance criteria** and owned files
3. **Unit tests** under `tests/phase_XX_*` that must pass before dependent phases start

**Rules**

- Agents must **not** edit files outside their phase ownership unless the prompt says otherwise.
- When a phase completes, update `PROGRESS.txt` and refresh the Status table in `README.md`.
- Do **not** start a dependent phase until that phase’s gate tests are green.
- Thin pointers under `phases/phase_XX_*/PROMPT.md` exist only for convenience — **this PRD is authoritative** if anything conflicts.

### 7.0 Dependency Graph

```text
Phase 0  Scaffold
    │
    ├──────────────┬──────────────────┐
    ▼              ▼                  ▼
Phase 1        Phase 4            Phase 6*
Triage         Conversation        Docker /
Classification Prompts & Guardrails Cloud Run prep
    │              │                  │
    ▼              │                  │
Phase 2            │                  │
Tool Handlers      │                  │
    │              │                  │
    ▼              │                  │
Phase 3 ◄──────────┘                  │
FastAPI Webhooks                      │
    │                                 │
    ├─────────────────────────────────┘
    ▼
Phase 5  Retell Agent + Telephony Config
    │
    ▼
Phase 7  QA Scenario Harness + Delivery Polish
```

\* Phase 6 can start after Phase 0 (Dockerfile skeleton) but must re-validate after Phase 3 (real app entrypoint).

### 7.1 Parallel Tracks (after Phase 0)

| Track A (backend logic) | Track B (conversation) | Track C (ops) |
| --- | --- | --- |
| Phase 1 → 2 → 3 | Phase 4 | Phase 6 (skeleton) |
| Then Phase 5 (needs A+B) | | Phase 6 finalize after 3 |
| Then Phase 7 | | |

### 7.2 How to Run a Phase Agent

1. Confirm prerequisites are `DONE` in `PROGRESS.txt`.
2. Copy the entire **Agent Prompt** block for that phase from this PRD into a new agent session.
3. Agent implements code + makes that phase’s tests pass.
4. Agent updates `PROGRESS.txt` and the README status block.
5. Do **not** start a dependent phase until the gate tests are green.

### 7.3 Running Gate Tests

```bash
# All phase gates
pytest tests/ -v

# Single phase
pytest tests/phase_00_scaffold/ -v
pytest tests/phase_01_triage/ -v
pytest tests/phase_02_tools/ -v
pytest tests/phase_03_webhooks/ -v
pytest tests/phase_04_prompts/ -v
pytest tests/phase_05_retell/ -v
pytest tests/phase_06_deploy/ -v
pytest tests/phase_07_qa_delivery/ -v
```

### 7.4 Phase Index

| Phase | Gate tests | Prompt section |
| --- | --- | --- |
| 0 Scaffold | `tests/phase_00_scaffold/` | §7.5 |
| 1 Triage | `tests/phase_01_triage/` | §7.6 |
| 2 Tools | `tests/phase_02_tools/` | §7.7 |
| 3 Webhooks | `tests/phase_03_webhooks/` | §7.8 |
| 4 Prompts | `tests/phase_04_prompts/` | §7.9 |
| 5 Retell | `tests/phase_05_retell/` | §7.10 |
| 6 Deploy | `tests/phase_06_deploy/` | §7.11 |
| 7 QA & Delivery | `tests/phase_07_qa_delivery/` | §7.12 |

Live board: `PROGRESS.txt`.

---

### 7.5 Phase 0 — Project Scaffold (Agent Prompt)

**Role:** Implement **Phase 0 only**. Do not implement triage logic, Retell config, or booking tools.

**Prerequisites:** None (first phase). Read this PRD for context.

**Goal:** Create a runnable Python project skeleton so parallel agents can land domain code without fighting over packaging.

**Owned files (create/edit only these)**

- `pyproject.toml` or `requirements.txt` + `requirements-dev.txt`
- `app/__init__.py`
- `app/main.py` (minimal FastAPI app with `GET /health` → `{"status":"ok"}`)
- `app/config.py` (settings via env: `APP_ENV`, `LOG_LEVEL`; defaults fine)
- `.env.example`
- `.gitignore` (Python, `.env`, `__pycache__`, `.venv`, `.pytest_cache`)
- `Dockerfile` (placeholder OK; must build a container that can run uvicorn)
- Update `PROGRESS.txt` Phase 0 → DONE when tests pass
- Update `README.md` Status + Quickstart if missing

**Out of scope:** Triage / tools / Retell prompts / Cloud Run deploy scripts beyond Dockerfile skeleton.

**Acceptance criteria**

1. `pytest tests/phase_00_scaffold/ -v` passes
2. App imports: `from app.main import app`
3. Health endpoint returns 200 with JSON `status=ok`
4. Dependencies include: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `httpx`, `pytest`, `pytest-asyncio`

**Notes:** Prefer `pytest` + `TestClient` for health check. Keep `app/main.py` tiny; later phases extend it.

**Progress template:** `[DONE] Phase 0 — Scaffold — <YYYY-MM-DD> — health endpoint + packaging ready`

**Gate:** `pytest tests/phase_00_scaffold/ -v`

---

### 7.6 Phase 1 — Urgency Triage Classification (Agent Prompt)

**Role:** Implement **Phase 1 only**. Do not build FastAPI routes or Retell configs.

**Prerequisites:** Phase 0 = DONE. Gate: `pytest tests/phase_00_scaffold/ -v` green.

**Goal:** Pure-Python triage classification matching §3 so tools/webhooks can call it without LLM involvement in unit tests.

**Owned files**

- `app/domain/__init__.py`
- `app/domain/models.py` — enums + dataclasses/Pydantic models
- `app/domain/triage.py` — `classify_urgency(signals: TriageSignals) -> TriageResult`
- Update `PROGRESS.txt` / `README.md`

**Domain spec**

- `UrgencyLevel`: `CRITICAL_SAFETY` | `HIGH_PRIORITY` | `STANDARD` | `LOW_PRIORITY`
- Input `TriageSignals`: `gas_or_co_suspected`, `no_heat`, `no_ac`, `vulnerable_resident`, `is_winter`, `is_summer`, `is_maintenance_only`, `caller_notes` (optional)
- Output `TriageResult`: `urgency`, `reason`, `recommended_tool` (`escalate_emergency` | `flag_priority` | `mock_schedule`), `immediate_script_key` (e.g. `evacuate_gas` or `None`)

**Priority rules (highest match wins)**

1. Gas / CO → `CRITICAL_SAFETY` → `escalate_emergency` → script `evacuate_gas`
2. (No heat + winter + vulnerable) OR (No AC + summer + vulnerable) → `HIGH_PRIORITY` → `flag_priority`
3. Maintenance only → `LOW_PRIORITY` → `mock_schedule`
4. Else → `STANDARD` → `mock_schedule`

**Out of scope:** HTTP endpoints, Retell payloads, TTS scripts beyond `immediate_script_key`.

**Acceptance:** `pytest tests/phase_01_triage/ -v` passes; deterministic; no FastAPI route changes.

**Progress template:** `[DONE] Phase 1 — Triage — <YYYY-MM-DD> — classify_urgency rules match PRD §3`

**Gate:** `pytest tests/phase_01_triage/ -v`

---

### 7.7 Phase 2 — Mock Tool Handlers (Agent Prompt)

**Role:** Implement **Phase 2 only**. No HTTP layer yet (Phase 3).

**Prerequisites:** Phase 1 = DONE. Gate: `pytest tests/phase_01_triage/ -v` green.

**Goal:** In-memory / mock handlers for booking and escalation so Phase 3 can expose them as webhooks.

**Owned files:** `app/tools/__init__.py`, `schemas.py`, `handlers.py`, `store.py`; update `PROGRESS.txt` / `README.md`.

**Tools**

1. **`escalate_emergency`** — input `call_id`, `hazard_summary`, optional `caller_phone`. Return `{ "action": "evacuate_and_call_911", "message": "...", "escalated": true }`. Never schedule a technician.
2. **`flag_priority`** — input `call_id`, optional `address`/`availability`, `reason`. Create `priority=high` ticket; return emergency slot (ISO datetime within next 4 hours; injectable `now` for tests).
3. **`mock_schedule`** — input `call_id`, `name`, `address`, `property_type`, `availability`, `urgency` (`standard`|`low`). Validate required fields; return confirmation id + window. Missing fields → `ToolValidationError`.
4. **`check_availability`** — input `zip_code` or `address`, `urgency`. Return 2–3 mock ISO slots; high urgency → earlier slots.

**Acceptance:** `pytest tests/phase_02_tools/ -v` passes; handlers importable without a server; store can list bookings/escalations.

**Progress template:** `[DONE] Phase 2 — Tools — <YYYY-MM-DD> — escalate/flag/schedule/availability mocks ready`

**Gate:** `pytest tests/phase_02_tools/ -v`

---

### 7.8 Phase 3 — FastAPI Retell Webhooks (Agent Prompt)

**Role:** Implement **Phase 3 only**. Expose Phase 2 tools as HTTP endpoints Retell can call.

**Prerequisites:** Phase 2 = DONE. Gate: `pytest tests/phase_02_tools/ -v` green.

**Owned files:** `app/main.py` (extend; keep `/health`), `app/api/__init__.py`, `app/api/retell_webhooks.py`, `app/api/deps.py`; update progress docs.

**Endpoints** (`/webhooks/retell`)

| Method | Path | Maps to |
| --- | --- | --- |
| POST | `/webhooks/retell/escalate_emergency` | `escalate_emergency` |
| POST | `/webhooks/retell/flag_priority` | `flag_priority` |
| POST | `/webhooks/retell/mock_schedule` | `mock_schedule` |
| POST | `/webhooks/retell/check_availability` | `check_availability` |
| POST | `/webhooks/retell/classify_urgency` | wraps Phase 1 `classify_urgency` |

**Request shape:** Flat tool args **or** Retell envelope `{ "name": "<tool>", "args": { ... } }` / `{ "call": {...}, "args": {...} }`. Normalize to tool kwargs.

**Responses:** 200 + JSON on success; 422 on validation errors; never 500 for missing optional escalate fields.

**Acceptance:** `pytest tests/phase_03_webhooks/ -v` passes; `/health` still works; router on `app.main:app`.

**Progress template:** `[DONE] Phase 3 — Webhooks — <YYYY-MM-DD> — Retell tool HTTP endpoints live`

**Gate:** `pytest tests/phase_03_webhooks/ -v`

---

### 7.9 Phase 4 — Conversation Prompts & Guardrails (Agent Prompt)

**Role:** Implement **Phase 4 only**. Can run **in parallel with Phase 1** after Phase 0. Do not modify tool handlers or FastAPI routes.

**Prerequisites:** Phase 0 = DONE. Gate: `pytest tests/phase_00_scaffold/ -v` green.

**Goal:** Versioned text/JSON assets for Alex’s system prompt, guardrails, and life-safety scripts (loadable by Phase 5; assertable in unit tests). Align content with §5.

**Owned files**

- `prompts/system_alex.md`
- `prompts/scripts/evacuate_gas.md`
- `prompts/scripts/priority_empathy.md`
- `prompts/guardrails.json`
- `app/prompts/loader.py` — `load_system_prompt()`, `load_script(key)`, `load_guardrails()`

**Guardrails JSON (minimum keys):** `irrelevant_query_pivot`, `address_refusal_explanation`, `competitor_pricing_response`, `never_do` (list).

**Evacuate gas script must:** instruct evacuate; call 911 and/or gas company; **not** ask for booking details before safety instructions.

**Acceptance:** `pytest tests/phase_04_prompts/ -v` passes; loader resolves project root from any cwd; no network/LLM.

**Progress template:** `[DONE] Phase 4 — Prompts — <YYYY-MM-DD> — Alex system prompt + guardrails + safety scripts`

**Gate:** `pytest tests/phase_04_prompts/ -v`

---

### 7.10 Phase 5 — Retell Agent & Telephony Config (Agent Prompt)

**Role:** Implement **Phase 5 only**. Produce Retell-ready config artifacts and wiring docs.

**Prerequisites:** Phases 3 and 4 = DONE. Both webhook and prompt gates green.

**Owned files:** `retell/agent_config.json`, `retell/tools.json`, `retell/BEGIN.md`, `app/retell/validate_config.py` (`validate_agent_config(path) -> list[str]`); update progress docs / `.env.example` (`WEBHOOK_BASE_URL`, `RETELL_API_KEY`).

**Agent:** name `summit-air-alex`; beginning message introduces Alex / Summit Air; system prompt references or embeds `prompts/system_alex.md`; document barge-in/interruption setting.

**Tools** (relative to `{{WEBHOOK_BASE_URL}}`): all five Phase 3 paths (`escalate_emergency`, `flag_priority`, `mock_schedule`, `check_availability`, `classify_urgency`).

**Validation:** all five tools present with `name`, `description`, `parameters` (JSON schema), `url`/`webhook_url` containing expected path; beginning message non-empty.

**Acceptance:** `pytest tests/phase_05_retell/ -v` passes; `retell/BEGIN.md` covers Twilio → Retell (no secrets).

**Progress template:** `[DONE] Phase 5 — Retell — <YYYY-MM-DD> — agent/tools config + operator checklist`

**Gate:** `pytest tests/phase_05_retell/ -v`

---

### 7.11 Phase 6 — Docker & Cloud Run Deploy (Agent Prompt)

**Role:** Implement **Phase 6**. Skeleton after Phase 0; **finalize** after Phase 3.

**Prerequisites:** Phase 0 to start; Phase 3 DONE to finalize (`pytest tests/phase_03_webhooks/ -v` green).

**Owned files:** `Dockerfile`, `.dockerignore`, `scripts/deploy_cloud_run.sh` (and/or `.ps1`), `docs/deployment.md`; update progress docs.

**Dockerfile:** run `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}`; prefer non-root; copy app + prompts assets.

**Deploy script:** `gcloud run deploy` with placeholders; `--port=8080`; document unauth vs auth trade-off for Retell webhooks; no hardcoded secrets.

**`docs/deployment.md`:** why Retell + Cloud Run (§2 trade-off); how mock booking fits; env vars `APP_ENV`, `LOG_LEVEL`, `WEBHOOK_BASE_URL`.

**Acceptance:** `pytest tests/phase_06_deploy/ -v` passes (static; no live GCP); Dockerfile has `uvicorn` + `8080`; deploy script references `gcloud run deploy`.

**Progress template:** `[DONE] Phase 6 — Deploy — <YYYY-MM-DD> — Docker + Cloud Run docs/script ready`

**Gate:** `pytest tests/phase_06_deploy/ -v`

---

### 7.12 Phase 7 — QA Scenario Harness & Delivery Polish (Agent Prompt)

**Role:** Implement **Phase 7** (final gate). Cover §6.2 scenarios + polish interviewer docs.

**Prerequisites:** Phases 1–6 = DONE; full suite green preferred.

**Owned files:** `app/qa/scenarios.py`, `docs/manual_call_checklist.md`, final `README.md` / `PROGRESS.txt`; ensure `tests/phase_07_qa_delivery/` passes.

**Automated scenarios**

- **Golden Path:** maintenance → `LOW_PRIORITY` → `mock_schedule` confirmation id
- **Emergency:** no heat + winter + vulnerable → `HIGH_PRIORITY` → `flag_priority` emergency slot
- **Safety Hazard:** gas/CO → `CRITICAL_SAFETY` → `escalate_emergency` mentions 911/evacuate; **no** normal booking
- **Hostile/Distracted (logic stand-in):** competitor pivot + address-refusal text present; barge-in documented in manual checklist (do not fake WebRTC in unit tests)

**Acceptance**

1. `pytest tests/phase_07_qa_delivery/ -v` passes
2. `pytest tests/ -v` full suite green
3. README covers what it is, architecture, FDE trade-offs, tests, how to demo
4. `PROGRESS.txt` shows all phases DONE + `READY FOR REVIEW`

**Progress template:**

```text
[DONE] Phase 7 — QA & Delivery — <YYYY-MM-DD> — scenarios + manual checklist + README polish
[READY FOR REVIEW] Summit Air Voice Agent — all phase gates green
```

**Gate:** `pytest tests/phase_07_qa_delivery/ -v && pytest tests/ -v`

---

## 8. Repo Layout (Target)

```text
PRD.md                 ← MASTER: product + phase prompts + gates
PROGRESS.txt           Live phase board + changelog
README.md              Interviewer-facing overview (mirrors status)
phases/                Thin pointers back to PRD §7.x (optional convenience)
app/                   FastAPI app, domain, tools (landed by phases)
prompts/               Alex system prompt + safety scripts (Phase 4)
retell/                Agent/tool JSON + operator checklist (Phase 5)
docs/                  Deployment + manual call checklist (Phases 6–7)
tests/phase_XX_*/      Gate unit tests
```
