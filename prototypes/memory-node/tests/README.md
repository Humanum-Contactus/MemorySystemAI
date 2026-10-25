# Tests automatisés — `memory-node`

| Fichier | Couvre | Contrôles |
|---------|--------|-----------|
| [`test_contradictions.py`](test_contradictions.py) | détection des contradictions, doublons, plancher 9→7, identité / correction auditive / feedback intacts, script de fusion, index ancien | 97 |

```bash
# depuis la racine du dépôt
python3 prototypes/memory-node/tests/test_contradictions.py   # sans dépendance
python3 -m pytest prototypes/memory-node/tests                # avec pytest
```

Tout se passe dans un dossier temporaire (aucun service, aucun index réel, LLM simulé).

Liens : [fiche de changement](../../../docs/changements/2026-10-25_detection-contradictions.md) ·
[protocole sur nœud réel](../../../docs/PROTOCOLE_TEST_CONTRADICTIONS.md) ·
[installation](../../../docs/INSTALLATION.md) · [README du prototype](../README.md)
