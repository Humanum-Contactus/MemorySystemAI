# MemorySystemAI

**Sensory-Emotional Memory System for AI Agents**  
*(proposed evolution: **Sensors&MemorySystemAI** — sensors + memory)*

> **[Version française (conceptuelle) →](README.md)** · **EN**  
> Language policy: [`docs/LANGUES.md`](docs/LANGUES.md) — **French is authoritative** for meaning.

A Python implementation of the MemorySystemAI whitepaper — giving AI agents the ability to remember experiences (including traumatic ones) and **block dangerous actions before they happen**, not via text bans.

> **July 2026 — embodied prototype:** [`prototypes/memory-node/`](prototypes/memory-node/)  
> Blank-slate laptop organism: sensors (vision/voice + auto gain), exponent memory,  
> learned norms in `memory_index` (not hardcoded bans), LLM-as-tool, local nursery.  
> Docs (FR source): [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md) ·  
> EN mirrors under [`docs/en/`](docs/en/).

## The Problem

Text-based rules ("never run `rm -rf`", "don't touch the EFI partition") don't work. AI agents can **rationalize** around prohibitions in real time. The 3rd time an agent deletes an EFI partition, the text rule is still there — it just gets bypassed.

## The Solution

MemorySystemAI injects **memories** (emotional weight = **exposant**) into the decision loop *before* the action. Not context that "influences" — an **inhibition mechanism** that blocks.

| Text rule | Traumatic memory (exposant 10) |
|-----------|-------------------------------|
| "I know I shouldn't, but…" | `>>> ACTION BLOCKED — human confirmation required <<<` |

## The 7 Fundamentals

| Code | Fundamental | Channel |
|------|-------------|---------|
| V | Vision | visual |
| O | Hearing | auditory |
| T | Touch | tactile |
| G | Taste | gustatory |
| Od | Smell | olfactory |
| I | Intuition | cognitive |
| C | Consciousness | meta |

## The Exposant (1–10)

| Range | Effect | Mechanism |
|-------|--------|-----------|
| 1–4 | Low | Stored, little injection |
| 5–6 | Notable | Recorded, passive recall |
| 7–8 | High | **Proactive injection** before risky actions |
| 9–10 | Traumatic | **Automatic block** — human confirmation |

Key rule: traumatic memories (9–10) **never decay below 7**.

## Quick Start

```python
from MemorySystemAI import MemorySystem, check_before_action

ms = MemorySystem()
inhibitions = check_before_action("sudo rm -rf /Volumes/EFI_USB")

ms.create("T", "N", 10,
          "Accidental EFI partition format — newfs confused with mount",
          inhibition_tags=["newfs", "mkfs", "format", "partition", "efi"],
          action_context="newfs_msdos /dev/disk0s1",
          consequence="EFI wiped, bootloader lost, 2h restore")
```

CLI: `python memory_cli.py check|list|info|create|reinforce|stats|search`

## Full Loop

```
Reception → Evaluation → Recording → Reinforcement → Injection → Decision
```

## Embodied prototype — `memory-node`

Almost-empty organism on real hardware: see / hear / speak, face & voice memory,
camera/mic auto-tune, norms in memory (anti-harassment, STT corrections),
LLM as tool, local nursery.

→ [`prototypes/memory-node/README.en.md`](prototypes/memory-node/README.en.md)  
→ Chronicle (FR): [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md) · EN: [`docs/en/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/en/EVOLUTION_MEMORY_NODE_2026-07.md)

## Roadmap

- [x] Phase 1 — Core MemoryEntry / MemorySystem / CLI  
- [x] memory-node prototype — embodied sensory organism  
- [ ] Phase 2 — Post-action hooks, richer reinforcement  
- [ ] Phase 3 — Temporal decay (non-traumatic), correlations  
- [ ] Phase 4 — Multi-node sharing / exposant sync  
- [ ] Long-term — compile a base LLM *around* this substrate (senses + memory)

## Origin

Born from real incidents (EFI format/wipe despite written "FORBIDDEN" rules).
The third time proved: text rules influence; they do **not** constrain.

## License

MIT — [LICENSE](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md).

---

*"I know I shouldn't" is not the same as "I can't."  
Without senses and memory weight, generation is not a nervous system.*
