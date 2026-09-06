# Retell + Twilio Operator Checklist



Wire Summit Air's inbound number to Retell, then point custom tools at the FastAPI webhooks on Cloud Run. No secrets belong in this repo — use dashboard/env vars only.



## 1. Prerequisites



- Twilio account with an inbound voice number

- Retell AI account + API key (`RETELL_API_KEY` in `.env`, never committed)

- Cloud Run (or ngrok) base URL exported as `WEBHOOK_BASE_URL` (no trailing slash)



## 2. Twilio → Retell



1. In Retell, create/import the agent from `retell/agent_config.json` (name: `summit-air-alex`).

2. Attach tools from `retell/tools.json`. Replace `{{WEBHOOK_BASE_URL}}` with the live origin.

3. In Twilio, point the number's voice webhook / SIP trunk to Retell's telephony endpoint for this agent (Retell dashboard → Phone Numbers → Connect Twilio).

4. Place a test call; confirm STT/TTS and barge-in (interrupt mid-sentence — agent should stop and listen).



## 3. Webhook wiring



| Tool | Method | Path |

| --- | --- | --- |

| `classify_urgency` | POST | `{WEBHOOK_BASE_URL}/webhooks/retell/classify_urgency` |

| `escalate_emergency` | POST | `{WEBHOOK_BASE_URL}/webhooks/retell/escalate_emergency` |

| `flag_priority` | POST | `{WEBHOOK_BASE_URL}/webhooks/retell/flag_priority` |

| `mock_schedule` | POST | `{WEBHOOK_BASE_URL}/webhooks/retell/mock_schedule` |

| `check_availability` | POST | `{WEBHOOK_BASE_URL}/webhooks/retell/check_availability` |



Health check: `GET {WEBHOOK_BASE_URL}/health` → `{"status":"ok"}`.



## 4. Barge-in / interruptions



Agent config sets high interruption sensitivity and documents Retell native overlap detection. Do not fake WebRTC in unit tests — verify barge-in on a live call (see `docs/manual_call_checklist.md`).



## 5. Prompts / language



- Languages: English (`en-US`) + Spanish Latin America (`es-419`) — set in `retell/agent_config.json` as `"language": ["en-US", "es-419"]`

- In the Retell dashboard, use Multiselect and pick both locales (do not use legacy `"multi"`)

- Beginning message offers Spanish (`Para español, dígalo ahora`)

- System prompt (EN): `prompts/system_alex.md` — includes language-matching rules

- System prompt (ES): `prompts/es/system_alex.md`

- Guardrails: `prompts/guardrails.json` / `prompts/es/guardrails.json`

- Gas/CO script: `prompts/scripts/evacuate_gas.md` / `prompts/es/scripts/evacuate_gas.md`


