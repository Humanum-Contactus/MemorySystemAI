# Change record — detecting contradictions between taught facts

> **[FR (source) →](../../changements/2026-10-25_detection-contradictions.md)** · EN · [`LANGUES.md`](../../LANGUES.md)  
> Chronicle: [phases M–S](../EVOLUTION_MEMORY_NODE_2026-10.md#october-2026-work) ·
> Protocol: [`TEST_PROTOCOL_CONTRADICTIONS.md`](../TEST_PROTOCOL_CONTRADICTIONS.md) ·
> Tests: [`tests/`](../../../prototypes/memory-node/tests/README.en.md) ·
> [CHANGELOG](../../../CHANGELOG.en.md) · [All records](README.md)

| Field | Value |
|-------|-------|
| Date | 25.10.2026 (deployed around 01:40, Zurich time) |
| Component | `prototypes/memory-node/` |
| Files | `fact_conflict.py` (new, +394), `dedup_taught_facts.py` (new, +245), `organism.py` (+323 / −4) |
| New dependencies | none (standard library) |
| Memory schema | unchanged (`MemorySystemAI/v1`, `correlations` field already planned) |
| Status | deployed on the node; automated tests green |

## 1. Why

On `/perceive`, any sentence "X est Y" became a C/P/e8 `Fait enseigné`. Two
contradictory versions coexisted at e8 and recall chose **the most repeated one**.
A repeated lie therefore ended up winning.

## 2. What

- **Same subject, same value** (including agreement `bleue`/`bleu`, preamble
  « pour information fiable ») → reinforcement of the existing memory, cap 8,
  **no new entry**.
- **Same subject, different value** → new e8 fact (as before) + reciprocal
  correlations + **one** `ask_human` question (`contradiction_posée:<sujet>`),
  only if the box is free.
- **Recall** on a contradicted subject → answer from memory, `uncertain: true`,
  `contradiction_ids`, both values quoted, **the LLM is not called**.
- **Human answer** naming a value → `contradiction_tranchée:<sujet>=<valeur>` in
  `human_feedback`; both facts remain, at the same exposants.
- `dedup_taught_facts.py`: **manual**, off-server merge of exact duplicates
  (dry-run by default, `--apply` with backup + archive).

**Unchanged:** thresholds 5/7/9, floor 7 for 9-10, fundamentals, states P/N/X,
inhibition by tags, living norms, memory before the LLM, identity, hearing
correction, feedback, `ask_human` anti-harassment.

Technical details and limits: see "Risks and limits" below.

## 3. How to test

```bash
# From the repository root, with no service and no real index:
python3 prototypes/memory-node/tests/test_contradictions.py
# or
python3 -m pytest prototypes/memory-node/tests
```

Expected: `RÉUSSI — 0 contrôle(s) en échec` (97 checks) / `3 passed` (all three scripts).

Test on a real node: [`../TEST_PROTOCOL_CONTRADICTIONS.md`](../TEST_PROTOCOL_CONTRADICTIONS.md).

Merging duplicates (always on a copy first):

```bash
cp memory_index.json /tmp/index_copie.json
python3 prototypes/memory-node/dedup_taught_facts.py --index /tmp/index_copie.json        # dry-run
python3 prototypes/memory-node/dedup_taught_facts.py --index /tmp/index_copie.json --apply
```

## 4. How to roll back

Before deployment, back up:

```bash
sudo systemctl stop memory-node
cd /opt/memorysystemai
sudo tar czf backups/contradictions_$(date +%Y%m%dT%H%M%S).tgz \
     MemorySystemAI/memory_index.json state/ organism.py
```

Rollback:

```bash
sudo systemctl stop memory-node
cd /opt/memorysystemai
sudo tar xzf backups/contradictions_<DATE>.tgz
sudo rm -f fact_conflict.py dedup_taught_facts.py
sudo systemctl start memory-node && systemctl is-active memory-node
```

⚠️ Restoring the archive also restores the index: everything learned since the
backup is lost. To roll back the code only, restore just `organism.py` and delete
the two new files (correlations already written remain readable by the old code).

In git: `git revert <commit>` of the "contradictions" commit.

## 5. What was actually executed (25.10.2026)

The exact commands, files touched, results and rollbacks as recorded in the
session log are in the chronicle:
[phase O (deployment)](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-o--deploying-contradiction-detection-01400145),
[phase P (duplicate merge)](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-p--merging-duplicates-0144-with-vincents-agreement),
[phase Q (test)](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-q--vornex-test-blue--red-contradiction-0145).
The commands above (sections 3 and 4) are **generic recipes**; those in the log
are authoritative for what happened. When the log does not give a command word for
word, the chronicle says so (`# commande exacte non consignée`).

```bash
# Executed (log):
sudo systemctl stop memory-node
tar tzf backups/contradictions_20261025T014030.tgz   # backup check
sudo systemctl start memory-node
# Recorded rollback:
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/contradictions_20261025T014030.tgz && rm -f fact_conflict.py dedup_taught_facts.py && sudo systemctl start memory-node && systemctl is-active memory-node
```

## 6. Risks and limits

- Split on the **first** « est » / « = »: « Le fait est que… » is cut too early.
- Subject too short (« le wifi est … »): no detection, deliberate choice.
- The question must contain all the subject’s words (≥ 4 letters).
- « bleu » ≠ « bleu clair » (possible false contradiction).
- Recognised preambles: closed list.
- If another question is already pending, the contradiction question is not asked
  (the uncertainty is still stated).
- `GET /memories` does not show correlations (read the index).
- **Observed in production**: `contradiction_ids` returned even without a
  contradiction → fixed in phase U ([record](2026-10-25_autonomie-contradiction-ids.md)).

---

See also: [October 2026 chronicle](../EVOLUTION_MEMORY_NODE_2026-10.md) ·
[test protocol](../TEST_PROTOCOL_CONTRADICTIONS.md) ·
[automated tests](../../../prototypes/memory-node/tests/README.en.md) ·
[installation](../INSTALLATION.md) · [CHANGELOG](../../../CHANGELOG.en.md)
