# Maintenance — scripts manuels (hors serveur)

> **FR (source)** · **[English →](README.en.md)** · [`LANGUES.md`](../../../docs/LANGUES.md)

Scripts lancés **à la main**, service arrêté, **après sauvegarde**, toujours
essayés d’abord sur une copie (dry-run par défaut, `--apply` pour écrire).
Ce sont les versions exécutées sur le nœud le 25.10.2026 (voir
[journal d’octobre](../../../docs/EVOLUTION_MEMORY_NODE_2026-10.md)).

| Script | Rôle | Phase |
|--------|------|-------|
| [`fusion_autonomie_occurrences.py`](fusion_autonomie_occurrences.py) | regroupe les « Autonomie inhibée » en gardant nombre + dates | V |
| [`nettoyage_autonomie_inhibee.py`](nettoyage_autonomie_inhibee.py) | ancienne fusion **sans** compteur — historique, ne plus utiliser | V |
| [`supprimer_vp002.py`](supprimer_vp002.py) | retire la fausse fiche voix de la synthèse | W |

Tests : [`../tests/test_autonomie.py`](../tests/test_autonomie.py), [`../tests/test_voix.py`](../tests/test_voix.py).
