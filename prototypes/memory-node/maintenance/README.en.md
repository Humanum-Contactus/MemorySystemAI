# Maintenance — manual scripts (off-server)

> **[FR (source) →](README.md)** · EN · [`LANGUES.md`](../../../docs/LANGUES.md)

Scripts run **by hand**, service stopped, **after a backup**, always tried on a
copy first (dry-run by default, `--apply` to write). These are the versions
executed on the node on 25.10.2026 (see the
[October journal](../../../docs/en/EVOLUTION_MEMORY_NODE_2026-10.md)). Their
comments stay in French.

| Script | Role | Phase |
|--------|------|-------|
| [`fusion_autonomie_occurrences.py`](fusion_autonomie_occurrences.py) | merges the "Autonomie inhibée" memories, keeping number + dates | V |
| [`nettoyage_autonomie_inhibee.py`](nettoyage_autonomie_inhibee.py) | older merge **without** counter — historical, do not use any more | V |
| [`supprimer_vp002.py`](supprimer_vp002.py) | removes the false voice profile of the synthetic voice | W |

Tests: [`../tests/test_autonomie.py`](../tests/test_autonomie.py), [`../tests/test_voix.py`](../tests/test_voix.py).
