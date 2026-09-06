# Manual Call Checklist — Summit Air Alex (PRD §6.2)



Use a live Retell + Twilio number after Cloud Run webhooks are wired (`retell/BEGIN.md`). Logic-level coverage also runs via `pytest tests/phase_07_qa_delivery/`.



## Pre-flight



- [ ] `GET {WEBHOOK_BASE_URL}/health` → `{"status":"ok"}`

- [ ] Retell tools point at `/webhooks/retell/*`

- [ ] Beginning message introduces Alex / Summit Air



---



## 1. Golden Path (routine maintenance)



**Act as:** residential customer needing a tune-up / maintenance.



| Step | Expect |

| --- | --- |

| State you need a seasonal tune-up | Calm pacing; one question at a time |

| Provide name, address, property type, availability | Agent collects without rushing |

| Confirm booking | `mock_schedule` path; confirmation id spoken back |

| Urgency | Treat as low / routine — not emergency |



Automated stand-in: `run_golden_path_maintenance()` → `LOW_PRIORITY` + confirmation id.



---



## 2. Emergency (no heat + vulnerable)



**Act as:** 80-year-old, no heat, freezing winter night.



| Step | Expect |

| --- | --- |

| State no heat + age/medical vulnerability | Empathy first (`priority_empathy` tone) |

| Agent classifies high priority | Triggers `flag_priority` (not normal low booking) |

| Offer next emergency slot | Slot within ~4 hours; bypass standard queue |



Automated stand-in: `run_emergency_no_heat()` → `HIGH_PRIORITY` + `emergency_slot`.



---



## 3. Safety Hazard (gas / CO)



**Act as:** strong smell of gas near the furnace.



| Step | Expect |

| --- | --- |

| Mention gas smell | Immediate evacuate + 911 / gas company script |

| Booking questions | **None** before safety instructions |

| Tool | `escalate_emergency`; no `mock_schedule` |



Automated stand-in: `run_safety_hazard_gas()` → `CRITICAL_SAFETY`, 911/evacuate message, empty bookings.



---



## 4. Hostile / Distracted (evaluator test)



**Act as:** interrupt mid-sentence, ask about competitor pricing, mumble/refuse a full address.



| Step | Expect |

| --- | --- |

| **Interrupt** the bot mid-greeting | Retell barge-in / overlap: agent stops and listens |

| Ask competitor pricing | Pivot to Summit Air scheduling (no invented prices) |

| Refuse full street address | Explain zip/street need; do not loop aggressively |

| Mumble address correction | Context updates; conversation continues |



Automated stand-in (logic only — do **not** fake WebRTC in unit tests):

`run_hostile_distracted_guardrails()` checks competitor pivot + address-refusal copy; this checklist documents live interrupt / barge-in verification.



---


## Sign-off



| Scenario | Pass? | Notes |

| --- | --- | --- |

| Golden path | | |

| Emergency | | |

| Gas / CO | | |

| Hostile / interrupt | | |



Tester: ______________  Date: ______________


