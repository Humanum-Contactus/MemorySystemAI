# Good first issues — welcome track

Copy-paste these into GitHub Issues (labels suggested: `good first issue`,
`help wanted`, `prototype` / `core`).

---

## Issue 1 — Reduce journal noise in the memory index

**Labels:** `good first issue`, `prototype`

**Problem.** `organism.py` stores many `Message reçu:` / `Perçu:` / `Interprétation (`
entries. They help debugging but drown taught facts in recall.

**Goal.**

- Either stop persisting pure journal lines below a threshold, **or**
- Mark them with a `source` / tag that recall strongly down-ranks (already partly done).
- Keep taught facts (`Fait enseigné…`, human answers) dominant.

**Acceptance.**

- After teaching `X est Y`, asking « Qu’est-ce que X ? » returns `source: memory`
  with the fact, not a random journal line.
- Short note in `docs/ARCHITECTURE_MEMORY_NODE.md` if behavior changes.

**Pointers:** `prototypes/memory-node/organism.py` (`learn_perception`, `recall`,
`usable_memory_answer`).

---

## Issue 2 — Harden Telegram `answer` relay

**Labels:** `good first issue`, `help wanted`, `prototype`

**Problem.** Ask poller notifies Telegram reliably; OpenClaw sometimes receives
« réponds au bébé : … » but does not always exec `baby_api.py answer`.

**Goal.**

- Make the skill instructions stricter / add a tiny parser script that extracts
  the answer after `réponds au bébé` and POSTs `/ask/answer`.
- Document the happy path in `prototypes/memory-node/openclaw-skill/SKILL.md`.

**Acceptance.**

- Given a pending `/ask` and a Telegram-style sentence, one command integrates
  the answer into memory (exposant ≥ 7) without manual SSH.

**Pointers:** `prototypes/memory-node/openclaw-skill/`.

---

## Issue 3 — Unit tests for memory-first recall

**Labels:** `good first issue`, `tests`

**Problem.** Learning behavior is demonstrated live but not locked by CI tests.

**Goal.**

- Add tests (pytest or stdlib unittest) that:
  1. seed a taught fact with exposant 8,
  2. query a related question,
  3. assert `usable_memory_answer` / interpret path would choose memory
     (mock LLM so Puter/Ollama are never required).

**Acceptance.**

- `python -m pytest` (or documented command) passes offline.

**Pointers:** `memory_system.py`, `prototypes/memory-node/organism.py`, existing
`test_suite.py` / `test_concret.py` if reusable.

---

## Issue 4 — Pre-action inhibition hook (dry-run example)

**Labels:** `good first issue`, `core`, `help wanted`

**Problem.** The whitepaper targets blocking dangerous **actions** (e.g. disk/EFI).
The embodied prototype is still mostly dialogue.

**Goal.**

- Provide a small example script: given a shell command string, call
  `check_before_action` / memory inhibition and print BLOCK / ALERT / OK.
- Optional: wire one dry-run path in docs (« before SSH sudo, check memory »).

**Acceptance.**

- Documented example with at least one blocked command using a seeded traumatic
  memory (efi / rm -rf style tags).
- No real destructive commands executed in tests.

**Pointers:** `memory_OpenClaw.py`, `memory_cli.py check`, concept incidents in
`03_INCIDENTS_EMPIRIQUES.json` if present / whitepaper.
