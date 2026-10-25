# Change record — voice: no longer mistaking itself for someone

> **[FR (source) →](../../changements/2026-10-25_voix-half-duplex.md)** · EN · [`LANGUES.md`](../../LANGUES.md)  
> Chronicle: [phase W](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-w--voice-fixes-2353) ·
> Tests: [`test_voix.py`](../../../prototypes/memory-node/tests/test_voix.py) ·
> [CHANGELOG](../../../CHANGELOG.en.md) · [All records](README.md)

| Field | Value |
|-------|-------|
| Date | 25.10.2026, 23:53, Zurich time |
| Files | `prototypes/memory-node/autonomy.py`, `voice_memory.py`, `organism.py`; script `maintenance/supprimer_vp002.py`; data `state/voice_persons.json` (node) |
| New dependencies | none |
| Status | deployed on the node; carried into this repository; tests green |

## 1. Why

The node listened to itself speaking (`hear_self`) and recorded its **own synthetic
voice** as a person: false voice profile. Its microphone could also record
while it was speaking.

## 2. What

1. `hear_self` no longer calls `voice.process_wav`.
2. `voice_memory.py` ignores any `tts_self_*` clip.
3. `organism.py`: half-duplex `SPEAKING` + 0.5 s guard; wait capped at 100 s.
4. Deletion of the false voice profile (`supprimer_vp002.py`, other profiles checked identical).

Limit: `sensory_agent.py` (separate process) is not covered by `SPEAKING`.
Extending the half-duplex to `sensory_agent.py` is **postponed by Vincent’s decision** (“not now”).

## 3. How to test

```bash
python3 prototypes/memory-node/tests/test_voix.py   # fabricated data and sounds
```

## 4. What was executed, and rollback

Commands and approach: [phase W](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-w--voice-fixes-2353).
The session log records no rollback command for this step; following the others:

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/voix_20261025T235340.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```
