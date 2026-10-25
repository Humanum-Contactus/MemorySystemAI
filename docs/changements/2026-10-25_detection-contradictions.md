# Fiche de changement — détection des contradictions entre faits enseignés

> Chronique : [phases M–S](../EVOLUTION_MEMORY_NODE_2026-10.md#chantier-doctobre-2026) ·
> Protocole : [`PROTOCOLE_TEST_CONTRADICTIONS.md`](../PROTOCOLE_TEST_CONTRADICTIONS.md) ·
> Tests : [`tests/`](../../prototypes/memory-node/tests/README.md) ·
> [CHANGELOG](../../CHANGELOG.md) · [Toutes les fiches](README.md)

| Champ | Valeur |
|-------|--------|
| Date | 25.10.2026 (déployé vers 01:40, heure de Zurich) |
| Composant | `prototypes/memory-node/` |
| Fichiers | `fact_conflict.py` (nouveau, +394), `dedup_taught_facts.py` (nouveau, +245), `organism.py` (+323 / −4) |
| Dépendances nouvelles | aucune (bibliothèque standard) |
| Schéma mémoire | inchangé (`MemorySystemAI/v1`, champ `correlations` déjà prévu) |
| Statut | déployé sur le nœud ; tests automatisés verts |

## 1. Pourquoi

Sur `/perceive`, toute phrase « X est Y » devenait un `Fait enseigné` C/P/e8.
Deux versions contradictoires coexistaient à e8 et le rappel choisissait **la plus
répétée**. Un mensonge répété finissait donc par gagner.

## 2. Quoi

- **Même sujet, même valeur** (y compris accord `bleue`/`bleu`, préambule « pour
  information fiable ») → renforcement de la mémoire existante, plafond 8,
  **pas de nouvelle entrée**.
- **Même sujet, valeur différente** → nouveau fait e8 (comme avant) + corrélations
  réciproques + **une** question `ask_human` (`contradiction_posée:<sujet>`),
  seulement si la boîte est libre.
- **Rappel** sur un sujet contredit → réponse depuis la mémoire, `uncertain: true`,
  `contradiction_ids`, les deux valeurs citées, **le LLM n’est pas appelé**.
- **Réponse humaine** désignant une valeur → `contradiction_tranchée:<sujet>=<valeur>`
  dans `human_feedback` ; les deux faits restent, aux mêmes exposants.
- `dedup_taught_facts.py` : fusion **manuelle**, hors serveur, des doublons exacts
  (dry-run par défaut, `--apply` avec sauvegarde + archive).

**Inchangé :** seuils 5/7/9, plancher 7 pour 9-10, fondamentaux, états P/N/X,
inhibition par tags, normes vivantes, mémoire avant LLM, identité, correction
auditive, feedback, anti-harcèlement `ask_human`.

Détail technique et limites : voir la section « Risques et limites » ci-dessous.

## 3. Comment tester

```bash
# Depuis la racine du dépôt, sans service ni index réel :
python3 prototypes/memory-node/tests/test_contradictions.py
# ou
python3 -m pytest prototypes/memory-node/tests
```

Attendu : `RÉUSSI — 0 contrôle(s) en échec` (97 contrôles) / `1 passed`.

Test sur un nœud réel : [`../PROTOCOLE_TEST_CONTRADICTIONS.md`](../PROTOCOLE_TEST_CONTRADICTIONS.md).

Fusion des doublons (toujours sur une copie d’abord) :

```bash
cp memory_index.json /tmp/index_copie.json
python3 prototypes/memory-node/dedup_taught_facts.py --index /tmp/index_copie.json        # dry-run
python3 prototypes/memory-node/dedup_taught_facts.py --index /tmp/index_copie.json --apply
```

## 4. Comment revenir en arrière

Avant le déploiement, sauvegarder :

```bash
sudo systemctl stop memory-node
cd /opt/memorysystemai
sudo tar czf backups/contradictions_$(date +%Y%m%dT%H%M%S).tgz \
     MemorySystemAI/memory_index.json state/ organism.py
```

Retour arrière :

```bash
sudo systemctl stop memory-node
cd /opt/memorysystemai
sudo tar xzf backups/contradictions_<DATE>.tgz
sudo rm -f fact_conflict.py dedup_taught_facts.py
sudo systemctl start memory-node && systemctl is-active memory-node
```

⚠️ Restaurer l’archive restaure aussi l’index : tout ce qui a été appris depuis la
sauvegarde est perdu. Pour ne revenir que sur le code, restaurer seulement
`organism.py` et supprimer les deux nouveaux fichiers (les corrélations déjà
écrites restent lisibles par l’ancien code).

Dans git : `git revert <commit>` du commit « contradictions ».

## 5. Risques et limites

- Découpage sur le **premier** « est » / « = » : « Le fait est que… » se coupe trop tôt.
- Sujet trop court (« le wifi est … ») : pas de détection, choix volontaire.
- La question doit contenir tous les mots du sujet (≥ 4 lettres).
- « bleu » ≠ « bleu clair » (fausse contradiction possible).
- Préambules reconnus : liste fermée.
- Si une autre question attend déjà, la question de contradiction n’est pas posée
  (l’incertitude est quand même dite).
- `GET /memories` ne montre pas les corrélations (lire l’index).
- **Constaté en production** : `contradiction_ids` renvoyé même sans contradiction
  (correction en analyse, voir chronique octobre 2026, phase Q).

---

Voir aussi : [chronique octobre 2026](../EVOLUTION_MEMORY_NODE_2026-10.md) ·
[protocole de test](../PROTOCOLE_TEST_CONTRADICTIONS.md) ·
[tests automatisés](../../prototypes/memory-node/tests/README.md) ·
[installation](../INSTALLATION.md) · [CHANGELOG](../../CHANGELOG.md)
