# Automated tests — `memory-node`

> **[FR (source) →](README.md)** · EN · [`LANGUES.md`](../../../docs/LANGUES.md)

| File | Covers | Checks |
|------|--------|--------|
| [`test_contradictions.py`](test_contradictions.py) | contradiction detection, duplicates, 9→7 floor, identity / hearing correction / feedback intact, merge script, old index | 97 |
| [`test_autonomie.py`](test_autonomie.py) | "Autonomie inhibée" counted (occurrences + dates), fields kept on save, `contradiction_ids` empty without contradiction, merge script with archive | 15 |
| [`test_voix.py`](test_voix.py) | `hear_self` without voiceprint, `tts_self_*` clips ignored, half-duplex `SPEAKING` + 0.5 s guard, VP002 deletion | 18 |
| [`pytest_scripts_test.py`](pytest_scripts_test.py) | pytest bridge running the three scripts above | — |

```bash
# from the repository root, no dependency
python3 prototypes/memory-node/tests/test_contradictions.py
python3 prototypes/memory-node/tests/test_autonomie.py
python3 prototypes/memory-node/tests/test_voix.py
python3 -m pytest prototypes/memory-node/tests                # optional, with pytest
```

Everything happens in a temporary folder (no service, no real index, mocked LLM).
Voice and memory data are **fabricated** by the tests. Without `numpy` (optional),
one check in `test_voix.py` verifies a lighter version. Test output and code
comments are in French (`RÉUSSI` = passed).

Links: [change records](../../../docs/en/changements/README.md) ·
[real-node protocol](../../../docs/en/TEST_PROTOCOL_CONTRADICTIONS.md) ·
[installation](../../../docs/en/INSTALLATION.md) · [prototype README](../README.en.md) ·
[maintenance scripts](../maintenance/README.en.md)
