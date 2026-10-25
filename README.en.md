# MemorySystemAI

**Sensory-Emotional Memory System for AI Agents**  
*(proposed evolution: **Sensors&MemorySystemAI** — sensors + memory)*

> **[Version française (conceptuelle) →](README.md)** · **EN**  
> Language policy: [`docs/LANGUES.md`](docs/LANGUES.md) — **French is authoritative** for meaning.

---

## Start with the foundation

The heart of this project is not the prototype code: it is the **whitepaper**.

### 📄 [MemorySystemAI Whitepaper v1](whitepaper/MemorySystemAI_Whitepaper_v1.md)

Vincent Vermeille — May 2026 (FR/EN in the same document)

> An artificial nervous system for AI: sensory memory, emotional exponents,
> and learned inhibition. Text rules influence; they do not **constrain**.
> Loop: **Action → Evaluation → Exponent → Injection → Decision**.

That document is the conceptual base (often reasoned in French): empirical diagnosis
(EFI incidents), 7 fundamentals, exposants, roadmap toward more native modulation.
**Everything else in this repository follows from it.**

Also: [`docs/en/CONCEPT_FUNDAMENTAL.md`](docs/en/CONCEPT_FUNDAMENTAL.md) ·
[`docs/en/WHY_IT_MATTERS.md`](docs/en/WHY_IT_MATTERS.md)

---

## What else is in the repo

A Python implementation of the whitepaper — remember experiences and **block
dangerous actions before they happen**, not via text bans.

> **July 2026 — embodied prototype:** [`prototypes/memory-node/`](prototypes/memory-node/)  
> Artisanal first sketch on real hardware. Useful to *see* the concept live —
> not to replace the whitepaper.  
> Chronicle: [`docs/en/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/en/EVOLUTION_MEMORY_NODE_2026-07.md)

---

## The Problem (summary)

Text-based rules don't work. Agents can **rationalize** around them in real time.
Detail: **[whitepaper](whitepaper/MemorySystemAI_Whitepaper_v1.md)**.

## The Solution (summary)

Inject **memories** (emotional weight = **exposant**) into the decision loop
*before* action — an **inhibition mechanism**, not mere prompt context.

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
| 7–8 | High | **Proactive injection** |
| 9–10 | Traumatic | **Automatic block** |

Traumatic memories (9–10) **never decay below 7**.

## Philosophy

Empirical and teaching-oriented: code commented for beginners, standard library
first, every dependency justified, open formats (JSON, text, Markdown), no
mandatory closed service, and a journal that tells the process (hypothesis,
attempt, result, lesson), so knowledge does not leave with people. Ground rule: if the assistants
disappear, anyone must be able to understand, review and redo our actions, with no
subscription, paid service or closed tool. Details:
[CONTRIBUTING.md — Project philosophy](CONTRIBUTING.md#project-philosophy).

## Quick Start (code)

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

→ [`prototypes/memory-node/README.en.md`](prototypes/memory-node/README.en.md)

## Roadmap

- [x] Phase 1 — Core library / CLI  
- [x] memory-node prototype (sketch)  
- [ ] Phases 2–4 — richer loop, decay, multi-node  
- [ ] Long-term — compile a base LLM *around* this substrate

## Origin

Real EFI incidents despite written bans — full story in the
[whitepaper](whitepaper/MemorySystemAI_Whitepaper_v1.md).

## License

MIT — [LICENSE](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md).

---

*"I know I shouldn't" is not the same as "I can't."  
Without senses and memory weight, generation is not a nervous system.*
