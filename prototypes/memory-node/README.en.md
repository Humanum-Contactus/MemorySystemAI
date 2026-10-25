# Prototype `memory-node` — embodied organism

> **[FR (source) →](README.md)** · EN · [`LANGUES.md`](../../docs/LANGUES.md)

First cut of a **Sensors&MemorySystemAI node**: near-blank slate, sensory tools,
external LLM consultation, learning by exposants, local graphical nursery.

> This is **not** a chatbot with text bans.  
> The LLM is a **tool**, not the identity.  
> Learned norms live in **`memory_index`**, not in `.py` tables.

Documentation:

| Doc | Content |
|-----|---------|
| [Evolution chronicle July 2026 (EN)](../../docs/en/EVOLUTION_MEMORY_NODE_2026-07.md) | Build history (phases A–I) |
| [Evolution chronicle October 2026 (EN)](../../docs/en/EVOLUTION_MEMORY_NODE_2026-10.md) | Phases J–W: contradictions, autonomy, voice |
| [Installation and tests (EN)](../../docs/en/INSTALLATION.md) | Install, configure, test |
| [Change records (EN)](../../docs/en/changements/README.md) | Why / what / test / rollback |
| [Architecture & API (EN)](../../docs/en/ARCHITECTURE_MEMORY_NODE.md) | Flows + HTTP |
| [Modules (EN)](../../docs/en/MODULES_MEMORY_NODE.md) | File-by-file |
| [Why it matters (EN)](../../docs/en/WHY_IT_MATTERS.md) | Research intent |
| [Languages](../../docs/LANGUES.md) | FR source of truth |

---

## Folder contents

| File | Role |
|------|------|
| `organism.py` | HTTP runtime: cognitive loop + tools |
| `visual_memory.py` | Face → identity (V) |
| `voice_memory.py` | Voice → identity (O) |
| `sensor_camera.py` | V4L2 auto-tune |
| `sensor_mic.py` | ALSA mic gain auto-tune |
| `ui/index.html` | Nursery kiosk |
| `requirements.txt` | Indicative Python deps |
| `systemd/memory-node.service.example` | systemd unit |
| `config.example.env` | Configuration example, no secret |
| `fact_conflict.py` | Detects contradictions between taught facts |
| `dedup_taught_facts.py` | Manual duplicate merge (dry-run by default) |
| `tests/` | Automated tests (`test_contradictions.py`, `test_autonomie.py`, `test_voix.py`) — [README](tests/README.en.md) |
| `maintenance/` | Manual off-server scripts ("Autonomie inhibée" merge, VP002 deletion) — [README](maintenance/README.en.md) |
| `systemd/memory-node.service.generic.example` | Generic systemd unit |
| `openclaw-skill/` | Telegram bridge (**bridge**, not concept core) |

---

## Cognitive loop

```
perception (text / mic / camera)
    → inhibition (tagged memories, high exposant)
    → memory recall (priority if fact already learned)
    → else consult LLM (tool)
    → else request_human (inhibited if anti-harassment memory + pending)
    → record (fundamentals + exposant)
```

## API (summary)

See [ARCHITECTURE (EN)](../../docs/en/ARCHITECTURE_MEMORY_NODE.md) for full routes:
`/perceive`, `/see`, `/hear`, `/mic`, `/camera`, `/ask/answer`, `/reset`, …

## Useful tutor teachings

```text
c'est moi Vincent
quand tu entends c'est mauve ca ça veut dire c'est moi Vincent
MonWifi est le réseau local.
```

## What this is not yet

Semantic similarity, full multi-sense corroboration, reliable Fundamental/State,
independence from chat-like bridges. Compass: **memory sieve + exposants**, everywhere.
