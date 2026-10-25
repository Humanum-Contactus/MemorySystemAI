# Évolution octobre 2026 — prototype `memory-node`

> **FR (source)** · *(traduction anglaise à venir)* · [`LANGUES.md`](LANGUES.md)  
> ← **Précédent :** [Évolution juillet 2026 (phases A–I)](EVOLUTION_MEMORY_NODE_2026-07.md) ·
> **Suivant :** *(aucun pour l’instant)* · [Index docs](README.md) · [CHANGELOG](../CHANGELOG.md)

**Auteur concept :** Vincent Vermeille (Humanum-Contactus)  
**Implémentation prototype :** session agent (poste de contrôle LAN → nœud)  
**Statut :** détection des contradictions déployée sur le nœud ; corrections d’autonomie en analyse  
**Code :** [`prototypes/memory-node/`](../prototypes/memory-node/)

Ce document **reprend exactement là où s’arrête** la
[chronique de juillet 2026](EVOLUTION_MEMORY_NODE_2026-07.md) (phase I), retrace
l’historique du dépôt entre les deux chroniques (phases J–L, d’après `git log`),
puis raconte le chantier d’octobre (phases M–T) : comment le nœud a appris à
**ne pas trancher seul** quand on lui enseigne deux versions incompatibles d’un fait.

Documents liés :

- [`changements/2026-10-25_detection-contradictions.md`](changements/2026-10-25_detection-contradictions.md) — fiche de changement (phases M–Q)  
- [`PROTOCOLE_TEST_CONTRADICTIONS.md`](PROTOCOLE_TEST_CONTRADICTIONS.md) — protocole de test générique (phases Q–R)  
- [`../prototypes/memory-node/tests/README.md`](../prototypes/memory-node/tests/README.md) — tests automatisés  
- [`INSTALLATION.md`](INSTALLATION.md) — installer et tester  
- [`../CHANGELOG.md`](../CHANGELOG.md) — historique des versions  
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md#continuer-le-journal) — comment continuer ce journal  

---

## 0. Résumé en une phrase

Après l’arrivée de l’**autonomie** en juillet (outils d’exploration, boucle de fond,
normes vivantes), octobre apporte la **résistance aux contradictions** : répéter un
mensonge ne le rend plus vrai, le rappel refuse de choisir et l’humain est interrogé
**une seule fois** — sans toucher aux bases du concept.

---

## 1. Point de départ — là où s’arrête la chronique de juillet

La chronique de juillet se termine sur la **phase I — Mémoires = normes (pas tables
`.py`)** : anti-harcèlement `ask` en mémoire C/N/e9, corrections STT en mémoires O,
inhibition uniquement par **tags** + exposant, pont OpenClaw assumé comme relais.

Son dernier état décrit (§ 6 « Suite ») :

| Point | État fin juillet | Ce qu’il devient ici |
|-------|------------------|----------------------|
| Fundamental & State | heuristique fragile | inchangé |
| Similarité sémantique | chevauchement de mots | inchangé (volontairement : § 4) |
| Corroboration multi-sens | partielle | norme vivante + `answer_from_corroboration` (phase L) |
| Moins de dépendance LLM / OpenClaw | encore forte | crible mémoire avant LLM (phase L) |
| Apprentissage plus « enfantin » | basique | inchangé |
| Mode plus actif | encore passif | outils d’autonomie + boucle de fond (phases K–L) |
| Inhibition actions machines (SSH/sudo) | pas câblée | inchangé |

Dernière modification de la chronique de juillet dans git : commit `2cbf065`
(21.07.2026 12:20, mise en bilingue de la documentation).

---

## 2. Chronologie du chantier

### Entre les deux chroniques — d’après `git log` (21.07.2026)

Source : historique du dépôt (`git log 2cbf065..e586d78`, diffs relus). Rien n’est
ajouté au-delà de ce que montrent les commits et leurs diffs.

### Phase J — Documentation : whitepaper en tête, bilinguisme

| Commit | Date (Zurich) | Contenu |
|--------|---------------|---------|
| `de84c9f` | 21.07 12:20 | Bannière bilingue + résumé EN dans `SENSORS_AND_MEMORY_SYSTEM_AI.md` |
| `7084cdb` | 21.07 12:44 | README, `CONTRIBUTING.md`, `LANGUES.md`, index docs : le **whitepaper** devient le fondement ; le prototype est présenté comme une esquisse incarnée qui en découle |

### Phase K — Boîte à outils d’autonomie (`autonomy.py`)

| Commit | Date (Zurich) | Contenu |
|--------|---------------|---------|
| `fa25480` | 21.07 14:13 | Nouveau `autonomy.py` (+763), `organism.py` (+120 / −4) : `probe_sensors`, `body_map`, `look_around`, `listen_ambient`, `reach_local`, `wonder`, `correlate`, `experiment_safe`, `craft_tool`, `ask_when_stuck`, `explore_cycle` ; chaque outil passe par `through_memory` (inhibition par tags → exécution → enregistrement). `POST /explore`, `POST /autonomy`, bouton « Explorer » dans la nursery |
| `74002c1` | 21.07 14:18 | Routes `/explore` et `/autonomy` documentées dans [`ARCHITECTURE_MEMORY_NODE.md`](ARCHITECTURE_MEMORY_NODE.md) |

Principe gardé : ce n’est **pas** une « curiosité LLM » ; ce sont des outils
sensoriels / méta qui nourrissent `memory_index`.

### Phase L — Autonomie durcie : normes vivantes, bilan de source, initiative

Commit `e586d78` (21.07 15:07) — `organism.py` (+874 / −54), `autonomy.py`
(+404 / −24), `ui/index.html` (+36 / −1) :

| Brique | Contenu (d’après le diff) |
|--------|---------------------------|
| Normes vivantes | `LIVING_NORMS` / `ensure_living_norms` : 4 mémoires e7 à tags — mémoire d’abord, corroboration, initiative, consolider avant autonomie |
| Bilan de source | compteurs vivants dans `memory_index` (`note_answer_source`, `source_bilan_from_memory`) au lieu d’un fichier de stats |
| Crible avant LLM | `llm_consultation_gate` : BLOCK/ALERT issus de la mémoire avant l’outil LLM |
| Corroboration | `answer_from_corroboration` (vue + ouïe / visage + voix) |
| Maturité | `autonomy_readiness` : verdict de maturité écrit en mémoire avant toute initiative hors UI |
| Gestes | `critique_gesture`, `note_gesture_quality` (compteurs utile / faible) |
| S’écouter | `hear_self` : compare ce qui est dit à ce qui est entendu (bouton « S’écouter ») |
| Boucle de fond | `start_autonomy_loop` / `tick_initiative` (variables `AUTONOMY_LOOP`, `AUTONOMY_INTERVAL`), toujours criblée par `ACT_INITIATIVE` |

Message du commit : les normes et inhibitions restent des mémoires vivantes à
exposants ; les journaux de session restent privés (`.gitignore`).

> C’est cette **boucle de fond** qui, chaque fois qu’une action est bloquée, écrit
> une mémoire « Autonomie inhibée: … » (`autonomy.py`) — origine du constat de la
> **phase S**.

### Période non documentée — 21.07.2026 15:07 → 24.10.2026

Aucun commit et aucune chronique publiée sur cette période. Le journal de session
privé n’est pas versionné. Seuls constats faits le 25.10 sur le nœud :

- le code en service était **identique à `e586d78`** (au format des fins de ligne près) ;
- l’index comptait **environ 1034 mémoires** ;
- le déploiement est **à plat** (pas de clone git sur le nœud).

Ce qui s’est passé entre-temps sur le nœud (usage, enseignements) **n’est pas documenté**.

---

### Chantier d’octobre 2026

### Phase M — Analyse et proposition (box, lecture seule)

- Lecture du chemin `/perceive` → `cycle_text` → `interpret_with_tools`.
- Constat : chaque phrase « X est Y » devient un `Fait enseigné` C/P/e8 ; pas de
  fusion, pas de détection ; le rappel départage **par le nombre de copies**.
- Proposition minimale : module pur `fact_conflict.py`, branchement dans
  `organism.py`, script hors serveur `dedup_taught_facts.py`.
- Démonstration locale (protocole « Vornex ») : **97 contrôles OK, 0 échec** sur copie.

### Phase N — Accès au nœud

- Le nœud était **injoignable par son interface filaire** (délai dépassé, absent de la table ARP).
- Connexion faite par son **interface wifi**, après vérification que l’**empreinte de
  clé d’hôte** était identique à celle déjà connue pour le nœud.
- Pare-feu `ufw` **volontairement laissé inchangé** : le port de l’API reste limité
  à un seul poste du réseau local.
- Fichiers déployés en fins de ligne CRLF → patch adapté (LF → patch → CRLF),
  contrôlé octet pour octet.

### Phase O — Déploiement de la détection des contradictions (25.10.2026 ~01:40)

- Arrêt du service, **sauvegarde horodatée** (index + état + `organism.py`).
- Installation : `fact_conflict.py`, `dedup_taught_facts.py`, `organism.py` modifié.
- Redémarrage : service actif, aucune erreur, nombre de mémoires inchangé.
- Détail : [fiche de changement](changements/2026-10-25_detection-contradictions.md).

### Phase P — Fusion des doublons (25.10.2026 ~01:44, accord de Vincent)

- Dry-run puis `--apply` après nouvelle sauvegarde : **6 groupes** de doublons
  exacts fusionnés, **1044 → 1036** mémoires.
- Exposants des survivants inchangés, corrélations reciblées, aucune contradiction touchée.

### Phase Q — Test « Vornex » (contradiction bleue / rouge)

| Étape | Résultat |
|-------|----------|
| « … est de couleur bleue. » | 1 fait e8 |
| « … est de couleur rouge. » | 2e fait e8, corrélation réciproque, **une** question `ask_human` |
| Rouge répété | aucun nouveau fait (doublon évité) |
| Question « De quelle couleur … ? » | `source: memory`, `uncertain`, les deux valeurs citées, « Je ne choisis pas » |
| Question posée 3 fois | **pas de relance** |

Protocole : [`PROTOCOLE_TEST_CONTRADICTIONS.md`](PROTOCOLE_TEST_CONTRADICTIONS.md).

### Phase R — Test « Quarvel » (25.10.2026 23:20, verte / jaune)

- Sujet neuf, pour ne pas renforcer les faits Vornex encore en attente de réponse.
- Contradiction **détectée**, corrélation réciproque.
- Rappel : **refuse de choisir**, cite les deux valeurs.
- Répétition de « verte » : **pas de doublon**.
- **Aucune nouvelle question** : une seule question peut être en attente à la fois
  (la question Vornex l’était) — comportement voulu, c’est l’anti-harcèlement.

### Phase S — Constats après les tests

1. **~226 souvenirs « Autonomie inhibée: … »** accumulés par la boucle de fond
   (introduite en **phase L**) : un `learn_perception` à chaque action bloquée.
2. **`contradiction_ids` présent à tort dès le premier fait** (réponse de `/perceive`
   sans contradiction réelle : la liste contient le seul fait rappelé).

### Phase T — Corrections en cours d’analyse *(EN COURS — non déployé)*

> **Entrée à compléter par Vincent / la session suivante.**

| Correction | Piste | État |
|------------|-------|------|
| Accumulation « Autonomie inhibée » (S.1) | *à compléter* | en analyse |
| `contradiction_ids` dès le premier fait (S.2) | *à compléter* | en analyse |

- Date de déploiement : *à compléter*  
- Fiche de changement : *à créer dans [`changements/`](changements/)*  
- Tests : *à compléter*  
- Retour arrière : *à compléter*  

---

## 3. Architecture résultante

```
POST /perceive
   │
   ├─ correction auditive / identité / feedback   (phase I, inchangés)
   ├─ fait enseigné (« X est Y »)
   │     └─ fact_conflict.classify_new_fact       (phase O)
   │           ├─ nouveau        → Fait enseigné C/P/e8 (comme avant)
   │           ├─ doublon        → renforcement (plafond 8), pas de nouvelle entrée
   │           └─ contradiction  → nouveau fait + corrélations réciproques
   │                               + 1 question ask_human (si boîte libre)
   └─ interpret_with_tools
         ├─ inhibition (≥ 9)                       (inchangé)
         ├─ contradiction ouverte → rappel incertain, source memory (phase O)
         ├─ rappel mémoire / corroboration          (phase L)
         └─ crible LLM → LLM / ask_human            (phase L)

Boucle de fond (phase L) : tick_initiative → through_memory → mémoire « Autonomie … »
```

---

## 4. Décisions de conception (traces)

| Tentation | Décision |
|-----------|----------|
| Effacer le fait « faux » | Rejeté — les deux restent, aux mêmes exposants |
| Passer le mensonge en état N | Rejeté — pas de punition implicite |
| Laisser le nombre de répétitions départager | Rejeté — le rappel refuse de choisir |
| File d’attente de questions | Rejeté — une question à la fois, pas de harcèlement |
| Brancher `MemorySystem.evaluate` (3 mots communs) | Rejeté — fusions abusives |
| Migration de l’index au démarrage | Rejeté — anciens index relus tels quels |
| Ouvrir le pare-feu pour faciliter l’accès | Rejeté — `ufw` inchangé |

---

## 5. Leçons apprises

1. La répétition n’est pas une preuve : sans lien explicite, la mémoire « vote ».  
2. Un test réel doit utiliser un **sujet neuf** pour ne pas renforcer un test précédent.  
3. Toujours **sauvegarder avant**, et écrire la commande de retour arrière **avant** d’agir.  
4. Le déploiement à plat et les fins de ligne CRLF piègent un `patch` naïf.  
5. Une boucle de fond qui écrit en mémoire à chaque blocage **gonfle l’index**.  
6. Vérifier l’empreinte de clé d’hôte avant de changer d’interface réseau.  
7. Une période sans commit ni chronique est une période perdue pour la recherche :
   tenir le journal **au fil de l’eau** (voir [règle de contribution](../CONTRIBUTING.md#continuer-le-journal)).

---

## 6. Suite (priorités concept)

| Point | État | Priorité |
|-------|------|----------|
| Accumulation « Autonomie inhibée » | en analyse (phase T) | Haute |
| `contradiction_ids` sans contradiction | en analyse (phase T) | Haute |
| Fundamental & State | heuristique fragile (hérité de juillet) | Haute |
| Similarité sémantique | chevauchement de mots (hérité de juillet) | Haute |
| Réponse humaine aux questions Vornex en attente | en attente de Vincent | Moyenne |
| Heuristique « premier est » (français simple) | limite connue | Moyenne |
| Inhibition actions machines (SSH/sudo) | pas câblée (hérité de juillet) | Moyenne |
| `GET /memories` sans corrélations | connu | Basse |

---

## 7. Carte des fichiers

| Chemin | Rôle | Phase |
|--------|------|-------|
| `prototypes/memory-node/autonomy.py` | Outils d’autonomie, boucle d’initiative | K–L |
| `prototypes/memory-node/fact_conflict.py` | Heuristique sujet / valeur, bibliothèque standard | O |
| `prototypes/memory-node/dedup_taught_facts.py` | Fusion des doublons (dry-run par défaut) | O–P |
| `prototypes/memory-node/organism.py` | Runtime ; branchements L et O | L, O |
| `prototypes/memory-node/tests/` | Tests automatisés (97 contrôles) | O |
| `docs/changements/` | Fiches de changement | O |

---

## 8. Remerciements / provenance

Concept et finalité : **Vincent Vermeille** (Humanum-Contactus).  
Juillet 2026 (phases J–L) : commits du dépôt. Octobre 2026 (phases M–T) :
collaboration humaine + agent, chaque étape validée par Vincent, sauvegardée avant,
et réversible.

---

← **Précédent :** [Évolution juillet 2026 (phases A–I)](EVOLUTION_MEMORY_NODE_2026-07.md) ·
**Suivant :** *(aucun pour l’instant)* · [Index docs](README.md) · [CHANGELOG](../CHANGELOG.md) ·
[Fiche de changement](changements/2026-10-25_detection-contradictions.md)
