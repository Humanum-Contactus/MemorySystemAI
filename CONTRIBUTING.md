# Contributing to MemorySystemAI / Sensors&MemorySystemAI

Thank you for your interest. This project is **open source** under the
[MIT License](LICENSE) (Vincent Vermeille — Humanum Contactus).

## What this project is

A **sensory-emotional memory system** for AI agents: fundamentals, emotional
exponents, learned inhibition — not a chatbot with text bans.

The July 2026 `memory-node` prototype shows an almost-empty organism with
sensors, memory-first recall, LLM-as-tool, and human tutoring (Telegram).

Please read before coding:

1. [`01_CONCEPT_FONDAMENTAL.txt`](01_CONCEPT_FONDAMENTAL.txt)  
2. [`docs/POURQUOI_CA_COMPTE.md`](docs/POURQUOI_CA_COMPTE.md)  
3. [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md)  
4. [`docs/MODULES_MEMORY_NODE.md`](docs/MODULES_MEMORY_NODE.md)  
5. [`prototypes/memory-node/README.md`](prototypes/memory-node/README.md)

## Design rules (non-negotiable)

- **No text bans as identity.** Inhibition = learned memories (exposant + tags).
- **Norms live in `memory_index`**, not in Python lookup tables / rate-limit files.
- **LLM is a tool**, not the organism’s persona.
- Prefer sensory corroboration and memory-first recall over “just ask the model”.
- Do not commit secrets (`state/*_token.txt`, `.env`, personal journals).

## Design rules (non-negotiable)

- **LLM ≠ identity.** Models (Kimi, Ollama, …) are *consult tools*.
- **No text-ban security.** Inhibition must come from **memories + exponents**.
- **Blank slate first.** Do not ship encyclopedic world knowledge in bootstrap.
- **Memory before re-ask.** If a fact was taught, prefer recall over calling the LLM again.
- Prefer small, reviewable PRs over large rewrites.

## How to contribute

1. Fork the repo / open a branch from `main`.
2. Pick a [good first issue](#good-first-issues) or propose an issue first.
3. Keep secrets out of git (`puter_token`, Telegram tokens, personal `memory_index.json`).
4. Open a Pull Request with: *what*, *why*, *how to test*.

### Local core library

```bash
python memory_cli.py stats
python memory_cli.py check "sudo rm -rf /efi"
```

### Prototype `memory-node` (optional hardware)

See [`prototypes/memory-node/README.md`](prototypes/memory-node/README.md).  
You can develop against the HTTP API without the full kiosk stack.

## Good first issues

These are intentional on-ramps for new contributors:

| # | Title | Area |
|---|--------|------|
| 1 | Reduce journal noise in memory index | `organism` recall / learning |
| 2 | Harden Telegram `answer` relay (OpenClaw skill) | `openclaw-skill` |
| 3 | Unit tests for memory-first recall | tests |
| 4 | Pre-action inhibition hook example (SSH/sudo dry-run) | core + docs |

Detailed descriptions: [`docs/GOOD_FIRST_ISSUES.md`](docs/GOOD_FIRST_ISSUES.md).

## Communication

- Prefer GitHub Issues / PRs for technical discussion.
- Concept authority: Vincent Vermeille (Humanum-Contactus).
- Constructive disagreement welcome — especially when it protects the nervous-system model against “just add another system prompt”.

## Code of collaboration

Be precise, kind, and concrete. This project exists because text rules failed in
real life; help us build mechanisms that **constrain**, not slogans that
**suggest**.
