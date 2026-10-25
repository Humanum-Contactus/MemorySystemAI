# Changelog

> **[FR (source) →](CHANGELOG.md)** · EN · [`LANGUES.md`](docs/LANGUES.md)

Format inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Dates as DD.MM.YYYY (Zurich time). French is authoritative. The detailed story is in the chronicles:

| Chronicle | Phases |
|-----------|--------|
| [`docs/en/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/en/EVOLUTION_MEMORY_NODE_2026-07.md) | A–I |
| [`docs/en/EVOLUTION_MEMORY_NODE_2026-10.md`](docs/en/EVOLUTION_MEMORY_NODE_2026-10.md) | J–W |

Change records: [`docs/en/changements/`](docs/en/changements/README.md) ·
Rule for continuing: [`CONTRIBUTING.md`](CONTRIBUTING.md#continuing-the-journal) ·
Index: [`docs/en/README.md`](docs/en/README.md)

## [Unreleased]

### Fixed — phases U–W (deployed on the node on 25.10.2026, carried here)
- [Phase U](docs/en/EVOLUTION_MEMORY_NODE_2026-10.md#phase-u--fix-contradiction_ids-announced-too-early-deployed-at-2336): `contradiction_ids` empty when there is no contradiction (`organism.py`).
- [Phase V](docs/en/EVOLUTION_MEMORY_NODE_2026-10.md#phase-v--autonomie-inhibée-counting-instead-of-copying-23362352): a repeated autonomy refusal reinforces a single memory and counts `occurrences` + `occurrence_dates` (`autonomy.py`); `memory_system.py` keeps these optional fields. `maintenance/` scripts. Record [`2026-10-25_autonomie-contradiction-ids`](docs/en/changements/2026-10-25_autonomie-contradiction-ids.md).
- [Phase W](docs/en/EVOLUTION_MEMORY_NODE_2026-10.md#phase-w--voice-fixes-2353): `hear_self` no longer writes to voice memory, `tts_self_*` clips ignored, half-duplex `SPEAKING` (+0.5 s), VP002 deleted. Record [`2026-10-25_voix-half-duplex`](docs/en/changements/2026-10-25_voix-half-duplex.md).
- Tests: `tests/test_autonomie.py`, `tests/test_voix.py` (fabricated data).

### Added — phases M–R, record [`2026-10-25_detection-contradictions`](docs/en/changements/2026-10-25_detection-contradictions.md)
- `prototypes/memory-node/fact_conflict.py`: detects contradictions between taught facts (subject / value, simple agreement, preambles).
- `prototypes/memory-node/dedup_taught_facts.py`: manual merge of exact duplicates (dry-run by default, backup + archive with `--apply`).
- `prototypes/memory-node/tests/test_contradictions.py`: 97 automated checks (script or pytest).
- Documentation: installation, contradiction test protocol, change record, October 2026 chronicle (FR + EN mirrors).
- `config.example.env`, `requirements-optional.txt`, `requirements-dev.txt`, generic systemd unit.

### Changed
- `prototypes/memory-node/organism.py`: detection hooked into `cycle_text` and `interpret_with_tools`; duplicate = reinforcement (cap 8); contradiction = reciprocal correlations + a single `ask_human` question; uncertain recall without the LLM. `learn_perception` returns the created entry.
- `.gitignore`: Python caches.

### Unchanged (concept foundations)
- Exposants 1-10, injection ≥ 7, blocking ≥ 9, floor 7 for 9-10, learned inhibition by tags, living norms, sense fundamentals, memory consulted before the LLM, `ask_human` without harassment.

### Deployment on the prototype node
- 25.10.2026 ~01:40: contradiction detection deployed.
- 25.10.2026 ~01:44: 6 duplicate groups merged (1044 → 1036 memories).

## [2026-07-21] — `e586d78`

Chronicle: [phases J–L](docs/en/EVOLUTION_MEMORY_NODE_2026-10.md#between-the-two-chronicles--from-git-log-21072026) (from `git log`).

- `e586d78` — Hardened autonomy: living norms, source balance, screen before the LLM, corroboration, maturity, gesture critique, `hear_self`, background initiative loop.
- `74002c1` — `/explore` and `/autonomy` routes documented.
- `fa25480` — Autonomy toolbox `autonomy.py`, `POST /explore`, `POST /autonomy`.
- `7084cdb` — The whitepaper becomes the foundation of the documentation.
- `de84c9f` — Bilingual banner on the naming document.

## [2026-07-20 – 2026-07-21] — `memory-node` prototype

Chronicle: [phases A–I](docs/en/EVOLUTION_MEMORY_NODE_2026-07.md).

- `2cbf065` — Bilingual documentation (FR source, EN mirrors).
- `80f258c` — memory-node evolution documented: sensors, identity, learned norms.
- `92843d9` — `CONTRIBUTING`, good first issues, issue templates.
- `56a6831`, `434eb97` — `memory-node` prototype and Sensors&MemorySystemAI documentation.

## [1.1] — 09.05.2026 — `310e761`

- Python implementation: `MemorySystem` core, CLI, OpenClaw integration, seed data.

## [1.0] — 04.05.2026 — `ba8ff51`

- MemorySystemAI: artificial nervous system (sensory memory, emotional exposants, learned inhibition).
