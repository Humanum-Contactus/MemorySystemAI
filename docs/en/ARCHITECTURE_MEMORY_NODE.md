# Architecture — `memory-node` prototype

> **[FR →](../ARCHITECTURE_MEMORY_NODE.md)** · EN · [`LANGUES.md`](../LANGUES.md)

## Overview

```
                    ┌─────────────────────────────────────┐
                    │         HUMAN (tutor)               │
                    │  local nursery  ·  (Telegram bridge)│
                    └──────────────┬──────────────────────┘
                                   │ perceive / answer / feedback
                                   ▼
┌──────────────────────────────────────────────────────────────┐
│  organism.py  (HTTP :8765)                                   │
│                                                              │
│  1. Reception      text | hear | see                         │
│  2. Sensors        camera auto-tune · mic auto-gain          │
│  3. Identity       visual_memory · voice_memory              │
│  4. O correction   “Correction auditive” memories            │
│  5. Inhibition     tags + exposant (no blind word overlap)   │
│  6. Recall         MemorySystem.recall (priority)            │
│  7. Consultation   NVIDIA / Puter / Ollama  (tool)           │
│  8. Ask human      request_human + anti-harassment memory    │
│  9. Recording      fundamentals + exposant + source          │
│ 10. Expression     utterance (+ speak / Piper)               │
└──────────────┬───────────────────────────┬───────────────────┘
               │                           │
               ▼                           ▼
     memory_index.json              OS tools
     (MemorySystemAI core)          camera / mic / TTS
```

Module reference: [`MODULES_MEMORY_NODE.md`](MODULES_MEMORY_NODE.md).

## Role separation

| Component | Role | Is not |
|-----------|------|--------|
| `MemorySystem` | store, score, inhibit | an LLM |
| `organism.py` | sensory loop + API | a chatbot persona |
| Tagged memories | learned norms | hardcoded `if`s in `.py` |
| NVIDIA / Puter / Ollama | interpret a perception | the baby’s identity |
| OpenClaw / Telegram | remote human relay (**bridge**) | the memory system |
| `ask_human.json` | mailbox | the “don’t spam” rule |
| Nursery UI | local presence | a generic dashboard |

## Decision loop

```
perception
  │
  ├─ (hear) repair via Correction auditive memories
  │
  ├─ memory inhibition (tags + exposant ≥ 9) ──► abstain
  │     utterance = “I abstain from X” + memory id…
  │
  ├─ usable_memory_answer? ──yes──► source: memory  (no LLM)
  │
  ├─ tool_consult_llm (NVIDIA / Puter / Ollama)
  │     ├─ OK ──► learn interpretation (I) + percept
  │     └─ JE NE SAIS PAS / fail
  │              └─ request_human
  │                    ├─ pending + anti-harassment memory → wait
  │                    └─ else ask pending (channel)
  ▼
utterance
```

### Inhibition pitfall avoided

**Do not** match all e≥9 memories by word overlap  
(otherwise “Vincent” blocked teaching “c'est moi Vincent”).

**Do**: require `inhibition_tags` **and** `matches_tags(action)`.

### Ask-human chatbot pitfall

The Telegram poller is a **bridge**. The norm “don’t harass if no answer yet”
is a **memory** (e.g. C/N/e9, tags `harceler|sans_attendre|…`).  
`request_human()` consults that memory when an ask is already pending.

## HTTP API

Base: `http://HOST:8765`

### GET

| Route | Description |
|-------|-------------|
| `/` or `/ui/` | Nursery HTML |
| `/status` | role, memories, vision, mic, camera, ask, faces/voices |
| `/memories` | index entries |
| `/faces` `/visual` | face persons / pending |
| `/voices` `/speakers` | voice persons / pending |
| `/ask` | ask mailbox |
| `/volume` | Master playback (speaker) |
| `/camera` | V4L2 controls |
| `/mic` | Capture / Mic Boost |
| `/vision` | provider nvidia\|puter |
| `/snapshot/<file>` | captured JPEG |

### POST (JSON)

| Route | Typical body | Effect |
|-------|--------------|--------|
| `/perceive` | `{ "text", "speak?" }` | text cycle (+ identity / corrections) |
| `/capture` | `{ "auto_tune?" }` | photo only |
| `/see` | `{ "speak?", "path?" }` | vision + visual identity |
| `/hear` | `{ "seconds?", "speak?", "auto_tune?" }` | mic + STT + cycle |
| `/speak` | `{ "text" }` | TTS |
| `/volume` | `{ "percent?"\|"delta?"\|"mute?" }` | speaker |
| `/camera` | `{ "auto":true }` or controls | V4L2 |
| `/mic` | `{ "auto":true }` or `{ "capture":N }` | input gain |
| `/vision` | `{ "provider":"nvidia\|puter" }` | switch |
| `/voice` | `{ "enabled": true\|false }` | listen loop |
| `/ask/answer` | `{ "answer" }` | integrate human answer (exposant ~8) |
| `/reset` | `{ "confirm":"RESET_ORGANISM" }` | blank → meta bootstrap |

## Environment variables

| Variable | Default | Role |
|----------|---------|------|
| `AGENT_PORT` | `8765` | HTTP port |
| `VISION_PROVIDER` | `nvidia` | `nvidia` \| `puter` |
| `NVIDIA_API_KEY` | — | else `state/nvidia_token.txt` |
| `PUTER_AUTH_TOKEN` | — | else `state/puter_token.txt` |
| `WHISPER_MODEL` | `base` | STT |
| `VISION_FALLBACK_PUTER` | `0` | no auto fallback |

## Learning (typical exposants)

| Event | Fund. | State | Exp. |
|-------|-------|-------|------|
| Journal / percept | C/O/V/I | X | ~5 |
| Taught fact / human answer | C | P | ~8 |
| Face / voice identity | V/O | P | ~8 |
| Taught auditory correction | O | P | ~8 |
| Social anti-harassment | C | N | ~9 |
