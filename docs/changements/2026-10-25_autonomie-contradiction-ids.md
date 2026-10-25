# Fiche de changement — « Autonomie inhibée » compté + `contradiction_ids`

> **FR (source)** · **[English →](../en/changements/2026-10-25_autonomie-contradiction-ids.md)** · [`LANGUES.md`](../LANGUES.md)  
> Chronique : [phases S–V](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-s--constats-après-les-tests) ·
> Tests : [`test_autonomie.py`](../../prototypes/memory-node/tests/test_autonomie.py) ·
> Scripts : [`maintenance/`](../../prototypes/memory-node/maintenance/README.md) ·
> [CHANGELOG](../../CHANGELOG.md) · [Toutes les fiches](README.md)

| Champ | Valeur |
|-------|--------|
| Date | 25.10.2026, 23:36 (v1) puis 23:40 (patch A + fusion), heure de Zurich |
| Fichiers | `prototypes/memory-node/autonomy.py`, `prototypes/memory-node/organism.py`, `memory_system.py` ; scripts `maintenance/fusion_autonomie_occurrences.py`, `maintenance/nettoyage_autonomie_inhibee.py` |
| Dépendances nouvelles | aucune (bibliothèque standard ; `zoneinfo` pour le script de fusion) |
| Schéma mémoire | deux champs **facultatifs** : `occurrences`, `occurrence_dates` (écrits seulement s’ils sont remplis) |
| Statut | déployé sur le nœud ; reporté dans ce dépôt ; tests verts |

## 1. Pourquoi

- La boucle de fond créait un **nouveau** souvenir « Autonomie inhibée: … » à chaque
  tick bloqué (toutes les 300 s) : 542 souvenirs, dont 541 identiques.
- `/perceive` renvoyait `contradiction_ids` dès le premier fait, sans contradiction.

## 2. Quoi

- `autonomy.py` : un refus identique **renforce** le souvenir existant (plafond 8)
  et ajoute une occurrence datée (ISO avec fuseau) ; sinon le souvenir est créé avec
  `occurrences = 1`.
- `memory_system.py` : sérialise et relit `occurrences` / `occurrence_dates`.
- `organism.py` : `contradiction_ids` vaut `[]` sans contradiction.
- Fusion de l’existant vers un survivant, nombre et dates reconstruits
  (`fusion_autonomie_occurrences.py`).

**Inchangé :** seuils, plancher 7, fondamentaux, états, normes vivantes, détection
des contradictions.

## 3. Comment tester

```bash
python3 prototypes/memory-node/tests/test_autonomie.py      # données fabriquées
python3 prototypes/memory-node/tests/test_contradictions.py # 97 contrôles, non-régression
```

## 4. Ce qui a été exécuté, et retour arrière

Commandes exactes, résultats et démarche (y compris le **stop de Vincent** après le
nettoyage v1 et sa décision de **garder le nombre et les dates**) :
[phase V](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-v---autonomie-inhibée---compter-au-lieu-de-recopier-23362352).

```bash
# Retour arrière consigné — avant la fusion avec occurrences :
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/autonomie_occurrences_20261025T234003.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
# Retour arrière consigné — complet (code d’origine, index à 1271) :
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/autonomie_20261025T233607.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

Dans git : `git revert <commit>`.

## 5. Risques et limites

- Le survivant renforcé atteint e8, **au-dessus du seuil d’injection (≥ 7)** : à trancher.
- `nettoyage_autonomie_inhibee.py` ne garde ni nombre ni dates : conservé pour
  l’historique, à ne plus utiliser.
- Le script de fusion n’utilise les heures du journal du nœud que si elles
  correspondent une pour une ; sinon, date du jour seulement.
