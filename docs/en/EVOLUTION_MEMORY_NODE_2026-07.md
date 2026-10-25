# Evolution July 2026 — `memory-node` prototype

> **[FR (source) →](../EVOLUTION_MEMORY_NODE_2026-07.md)** · EN · [`LANGUES.md`](../LANGUES.md)  
> ← **Previous:** *(none — first chronicle)* · **Next:** [Evolution October 2026 (phases J–W)](EVOLUTION_MEMORY_NODE_2026-10.md) · [Docs index](README.md) · [CHANGELOG](../../CHANGELOG.en.md)

**Concept author:** Vincent Vermeille (Humanum-Contactus)  
**Status:** first embodied demonstrator — Sensors&MemorySystemAI in power  
**Code:** [`prototypes/memory-node/`](../../prototypes/memory-node/)

This is the **chronicle** of bringing the concept / Python library onto a laptop
that perceives, learns, and asks for help.

Related: [`WHY_IT_MATTERS.md`](WHY_IT_MATTERS.md) · [`ARCHITECTURE_MEMORY_NODE.md`](ARCHITECTURE_MEMORY_NODE.md) · [`MODULES_MEMORY_NODE.md`](MODULES_MEMORY_NODE.md)

---

## 0. One-sentence summary

We embodied MemorySystemAI as a **baby organism**: near-blank slate, sensors +
exponent memory, LLM only as tool, human as tutor — live demos (memory recall
without re-asking the LLM; ask via Telegram bridge).

---

## 1. Intention

**Problem.** LLMs generate. They have no nervous system.  
Text bans do not truly inhibit (EFI incidents in the whitepaper/concept).

**Goal.** Sensors&MemorySystemAI:

1. **Sensors** — V/O/T/G/Od/I/C + see/hear/speak tools  
2. **Sensory-emotional memory** — exposants + P/N/X  
3. **Loop** — reception → evaluation → recording → reinforcement → injection  
4. **LLM** — interpretation tool, not identity / not law  
5. **Human** — tutor when memory is insufficient  

The prototype is **not** a local chatbot.

---

## 2. Build chronology

### Phase A — Target machine

- Acer laptop as dedicated node (Ubuntu Server 24.04 via LAN PXE/autoinstall).
- Hostname `memory-node`; camera/audio groups; EFI care from concept lessons.

### Phase B — Runtime stack

- `MemorySystemAI` under `/opt/memorysystemai/`.
- Ollama as consult fallback; first “chatbot + text rules” agent **rejected**.

### Phase C — Organism (`organism.py`)

| Principle | Implementation |
|-----------|----------------|
| Blank slate | bootstrap = **meta** entries only |
| Tools | see, hear, speak, consult_llm, ask_human |
| No text bans | inhibition = high-exposant **tagged** memories |
| API | HTTP `:8765` |
| Real learning | memory recall **before** LLM |

### Phase D — Local nursery

Xorg + Openbox + Chromium kiosk; UI `ui/index.html` on the laptop screen.

### Phase E–F — LLM tools & Telegram bridge

Puter/Kimi then NVIDIA vision; OpenClaw skill + ask poller as **bridge** (not core).

### Phase G — Learning proof

Teach facts → re-ask → `source: memory`; human answer → exposant ~8.

### Phase H — Sensors & identity

| Brick | Content |
|-------|---------|
| Real vision | JPEG `/see` → NVIDIA NIM (default) or Puter |
| Faces | `visual_memory.py` — local embeddings, teach “c'est moi Vincent” |
| Voice | `voice_memory.py` — spectral embeddings |
| Camera auto | `sensor_camera.py` |
| Mic auto | `sensor_mic.py` (often **clipping**, not too quiet) |
| TTS | Piper `fr_FR-siwis-medium` |

### Phase I — Norms = memories (not `.py` tables)

1. **Ask anti-harassment** — C/N/e9 memory; `request_human()` respects pending.  
2. **STT corrections** — O memories `Correction auditive: « … » → « … »`.  
3. **Inhibition** — tags only (fixed false “I abstain” on saying “Vincent”).  
4. **OpenClaw** — assumed as relay; growing it risks chatbot logic.

---

## 3. Design decisions

| Temptation | Decision |
|------------|----------|
| Chatbot + text bans | Rejected |
| Fill memory at boot | Rejected |
| LLM = node personality | Rejected |
| Always call the LLM | Rejected after recall fix |
| Ask rate-limit in `.json`/`.py` | Rejected → social memory |
| STT regex table in code | Rejected → auditory memories |
| Inhibit via all e9 word overlaps | Rejected → tags only |

---

## 4. Lessons

1. Starting as a chatbot **kills** the concept.  
2. Recording ≠ recalling.  
3. Human teaching should raise exposant (~8).  
4. Telegram ask is a bridge; enlarging it is chatbot risk.  
5. Secrets stay out of git.  
6. **Learned norm = memory entry**; mechanism = code that reads tags.  
7. The danger is no longer “not moving” — it is moving **off-concept**.

---

## 5. Next priorities

| Point | State | Priority |
|-------|-------|----------|
| Fundamental & State | fragile heuristics | High |
| Semantic similarity | word overlap | High |
| Multi-sense corroboration | partial | High |
| Less LLM / OpenClaw dependence | still strong | High |
| More childlike / active learning | basic / passive | Medium |
| Machine-action inhibition (SSH/sudo) | not wired | Medium |

---

## 6. Provenance

Concept: **Vincent Vermeille**.  
July 2026 embodiment: human + Cursor agent on the LAN, staying faithful to
the original idea (not a chatbot gadget).

---

← **Previous:** *(none — first chronicle)* · **Next:** [Evolution October 2026 (phases J–W)](EVOLUTION_MEMORY_NODE_2026-10.md) · [Docs index](README.md) · [CHANGELOG](../../CHANGELOG.en.md)
