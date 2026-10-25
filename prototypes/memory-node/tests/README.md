# Tests automatisés — `memory-node`

> **FR (source)** · **[English →](README.en.md)** · [`LANGUES.md`](../../../docs/LANGUES.md)

| Fichier | Couvre | Contrôles |
|---------|--------|-----------|
| [`test_contradictions.py`](test_contradictions.py) | détection des contradictions, doublons, plancher 9→7, identité / correction auditive / feedback intacts, script de fusion, index ancien | 97 |
| [`test_autonomie.py`](test_autonomie.py) | « Autonomie inhibée » compté (occurrences + dates), champs conservés à la sauvegarde, `contradiction_ids` vide sans contradiction, script de fusion avec archive | 15 |
| [`test_voix.py`](test_voix.py) | `hear_self` sans empreinte vocale, clips `tts_self_*` ignorés, half-duplex `SPEAKING` + garde 0,5 s, suppression de VP002 | 18 |
| [`pytest_scripts_test.py`](pytest_scripts_test.py) | pont pytest qui lance les trois scripts ci-dessus | — |

```bash
# depuis la racine du dépôt, sans dépendance
python3 prototypes/memory-node/tests/test_contradictions.py
python3 prototypes/memory-node/tests/test_autonomie.py
python3 prototypes/memory-node/tests/test_voix.py
python3 -m pytest prototypes/memory-node/tests                # facultatif, avec pytest
```

Tout se passe dans un dossier temporaire (aucun service, aucun index réel, LLM
simulé). Les données de voix et de mémoire sont **fabriquées** par les tests.
Sans `numpy` (facultatif), un contrôle de `test_voix.py` vérifie une version allégée.

Liens : [fiches de changement](../../../docs/changements/README.md) ·
[protocole sur nœud réel](../../../docs/PROTOCOLE_TEST_CONTRADICTIONS.md) ·
[installation](../../../docs/INSTALLATION.md) · [README du prototype](../README.md) ·
[scripts de maintenance](../maintenance/README.md)
