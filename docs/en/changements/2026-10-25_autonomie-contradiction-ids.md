# Change record — "Autonomie inhibée" counted + `contradiction_ids`

> **[FR (source) →](../../changements/2026-10-25_autonomie-contradiction-ids.md)** · EN · [`LANGUES.md`](../../LANGUES.md)  
> Chronicle: [phases S–V](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-s--findings-after-the-tests) ·
> Tests: [`test_autonomie.py`](../../../prototypes/memory-node/tests/test_autonomie.py) ·
> Scripts: [`maintenance/`](../../../prototypes/memory-node/maintenance/README.en.md) ·
> [CHANGELOG](../../../CHANGELOG.en.md) · [All records](README.md)

| Field | Value |
|-------|-------|
| Date | 25.10.2026, 23:36 (v1) then 23:40 (patch A + merge), Zurich time |
| Files | `prototypes/memory-node/autonomy.py`, `prototypes/memory-node/organism.py`, `memory_system.py`; scripts `maintenance/fusion_autonomie_occurrences.py`, `maintenance/nettoyage_autonomie_inhibee.py` |
| New dependencies | none (standard library; `zoneinfo` for the merge script) |
| Memory schema | two **optional** fields: `occurrences`, `occurrence_dates` (written only when filled) |
| Status | deployed on the node; carried into this repository; tests green |

## 1. Why

- The background loop created a **new** "Autonomie inhibée: …" memory on every
  blocked tick (every 300 s): 542 memories, 541 of them identical.
- `/perceive` returned `contradiction_ids` from the first fact, with no contradiction.

## 2. What

- `autonomy.py`: an identical refusal **reinforces** the existing memory (cap 8)
  and adds a dated occurrence (ISO with time zone); otherwise the memory is created
  with `occurrences = 1`.
- `memory_system.py`: serialises and reads back `occurrences` / `occurrence_dates`.
- `organism.py`: `contradiction_ids` is `[]` when there is no contradiction.
- Merge of the existing stock into one survivor, number and dates rebuilt
  (`fusion_autonomie_occurrences.py`).

**Unchanged:** thresholds, floor 7, fundamentals, states, living norms,
contradiction detection.

## 3. How to test

```bash
python3 prototypes/memory-node/tests/test_autonomie.py      # fabricated data
python3 prototypes/memory-node/tests/test_contradictions.py # 97 checks, non-regression
```

## 4. What was executed, and rollback

Exact commands, results and approach (including **Vincent’s stop** after cleanup v1
and his decision to **keep the number and the dates**):
[phase V](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-v--autonomie-inhibée-counting-instead-of-copying-23362352).

```bash
# Recorded rollback — before the merge with occurrences:
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/autonomie_occurrences_20261025T234003.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
# Recorded rollback — full (original code, index at 1271):
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/autonomie_20261025T233607.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

In git: `git revert <commit>`.

## 5. Risks and limits

- The reinforced survivor reaches e8, **above the injection threshold (≥ 7)**: to decide.
- `nettoyage_autonomie_inhibee.py` keeps neither number nor dates: kept for the
  record, not to be used any more.
- The merge script uses the node log times only if they match one to one;
  otherwise, today’s date only.
