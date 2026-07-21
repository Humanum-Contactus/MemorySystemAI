# Modules — `memory-node` prototype

> **[FR →](../MODULES_MEMORY_NODE.md)** · EN · [`LANGUES.md`](../LANGUES.md)

Runtime file reference under [`prototypes/memory-node/`](../../prototypes/memory-node/).

> **Design rule:** *norms* (do not harass, STT corrections, etc.) live in
> `memory_index.json` (entries with exposant + tags). Python **applies** the
> memory sieve; it must not become a table of text rules.

---

## File map

| File | Sense | Role |
|------|-------|------|
| [`organism.py`](../../prototypes/memory-node/organism.py) | C + I + orchestration | HTTP runtime, cognitive loop, tools |
| [`memory_system.py`](../../memory_system.py) *(repo root)* | Core | Entries, exposants, `matches_tags`, reinforce |
| [`visual_memory.py`](../../prototypes/memory-node/visual_memory.py) | V | Face embeddings → identity |
| [`voice_memory.py`](../../prototypes/memory-node/voice_memory.py) | O | Voice embeddings → identity |
| [`sensor_camera.py`](../../prototypes/memory-node/sensor_camera.py) | V | V4L2 brightness/gamma/exposure auto |
| [`sensor_mic.py`](../../prototypes/memory-node/sensor_mic.py) | O | ALSA Capture / Mic Boost from RMS |
| [`autonomy.py`](../../prototypes/memory-node/autonomy.py) | C/I + V/O | Autonomous exploration (memory golden rule) |
| [`ui/index.html`](../../prototypes/memory-node/ui/index.html) | — | Nursery kiosk |
| [`openclaw-skill/`](../../prototypes/memory-node/openclaw-skill/) | — | Telegram bridge (**transitional**, not the core) |

---

## `organism.py`

Entry: `python organism.py` (systemd in prod, `ROOT=/opt/memorysystemai`).

### `interpret_with_tools` loop

1. **Inhibition** — only memories with `inhibition_tags` matching the action  
   (`exposant >= 7` inject / `>= 9` block). No blind lexical overlap.
2. **Recall** — `recall` + `usable_memory_answer` (priority over LLM).
3. **LLM consult** — tool (NVIDIA / Puter / Ollama), not identity.
4. **Ask human** — `request_human()`: mailbox `ask_human.json` + **social memory**
   anti-harassment (tags `harceler`, `sans_attendre`, …).

### Taught memories (content examples, not code)

| Type | `data` format | Typical tags |
|------|---------------|--------------|
| Tutor anti-harassment | “When I address a human…” | `harceler`, `sans_attendre`, `relancer` |
| STT correction | `Correction auditive: « … » → « … »` | `correction_auditive`, `stt`, `ouie` |

Live teaching of a correction:

```text
quand tu entends c'est mauve ca ça veut dire c'est moi Vincent
```

### Integrated sensors

- **See**: capture → `sensor_camera.auto_tune_from_frame` → vision LLM (NVIDIA default) + `visual_memory`.
- **Hear**: record → `sensor_mic.auto_tune_from_wav` → Whisper → auditory corrections from memory → `voice_memory` → same loop as `/perceive`.
- **Speak**: Piper (`fr_FR-siwis`) then Pico / espeak.

---

## `visual_memory.py` / `voice_memory.py`

Local lightweight embeddings (not FaceNet / ECAPA). Persistence under `state/` (not in git).
Teach: `c'est moi <Name>`, `je suis <Name>`, … → `label_pending_or_last`.

---

## `sensor_camera.py` / `sensor_mic.py`

Same idea: **measure** (frame luminance / WAV RMS-peak) → **propose** hardware controls → optional recapture.
Experience (“I lowered gain”) can be written as V/O memories.

| Sensor | Controls | Too low | Too high |
|--------|----------|---------|----------|
| Camera | brightness, gamma, exposure… | open up | close down |
| Mic | `Capture`, `Internal Mic Boost` | raise | lower (clipping) |

Note: UI `Master` volume = **speaker**, not mic. Mic = `/mic`.

---

## Secrets (never in git)

`state/puter_token.txt`, `state/nvidia_token.txt`, `ask_human.json`, person DBs, live `memory_index.json` on the node.

---

## Still fragile (honest)

1. Fundamental / State detection (keyword heuristics).  
2. Semantic similarity (still word overlap).  
3. True multi-sense corroboration.  
4. Less OpenClaw / chat-like ask channel.  
5. More active mode (organism does not only wait to be spoken to).
