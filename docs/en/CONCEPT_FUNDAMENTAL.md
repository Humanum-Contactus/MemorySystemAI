# Fundamental concept — MemorySystemAI

> **[FR — 01_CONCEPT_FONDAMENTAL.txt →](../../01_CONCEPT_FONDAMENTAL.txt)** · EN summary  
> Full analytical depth is in the French source. This is a faithful overview.

## Idea

A memory system structured on Nature’s **7 fundamentals**, with tunable emotional
**exposants**, forming a permanent learning loop:

**Action → Evaluation → Exposant → Injection → Decision**

It addresses a core architectural gap in current AI: the absence of a **nervous system**.
LLMs generate text statistically without a learned inhibition mechanism.
This project proposes a functional equivalent of a sensory-emotional system.

## The problem with LLM-only architecture

- Input → next-token probabilities → tokens…  
- **No** evaluation step before action  
- **No** consequence → learning loop  
- **No** learned inhibition mechanism  
- "Reasoning" is statistical emergence, not an engineered constraint

Safety rules in prompts are **text in context** — they influence generation;
they do not **constrain** it.

### Empirical incidents (project origin)

- **2026-05-01**: `newfs_msdos` instead of `mount_msdos` → EFI formatted, OpenCore lost  
- **2026-05-04**: `sudo rm -rf` on an active EFI mount → partition contents wiped  
- Errors recurred despite written "FORBIDDEN" memory notes — because a text ban is not a mechanism

## Solution sketch

| Code | Fundamental | Meaning |
|------|-------------|---------|
| V | Vision | seen / read |
| O | Hearing | heard / spoken |
| T | Touch | manipulated / actuated |
| G | Taste | tested / tried |
| Od | Smell | sensed / foresensed |
| I | Intuition | deduced / correlated |
| C | Consciousness | meta / self-learning |

Emotional states: **P** positive · **N** negative · **X** unknown.

Exposant 1–10 drives recording, injection, and blocking (see README).

## Long-term aim (author)

Compile a **base LLM around this substrate**: senses (discovery, drivers, config),
memory + shared exposants, research / conceptualization / tool-making —
not a giant pretrained persona with rules glued on afterwards.

See also: [`WHY_IT_MATTERS.md`](WHY_IT_MATTERS.md), prototype `memory-node`.
