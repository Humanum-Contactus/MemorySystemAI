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

- **Ce qu’on cherchait** : savoir si le nœud peut se laisser convaincre par un
  mensonge répété, et pourquoi.
- **Ce qu’on a essayé** : lecture du chemin `/perceive` → `cycle_text` →
  `interpret_with_tools`, puis proposition minimale : module pur
  `fact_conflict.py`, branchement dans `organism.py`, script hors serveur
  `dedup_taught_facts.py`, essayés sur une **copie** du dépôt (protocole « Vornex »).
- **Ce qu’on a constaté** : chaque phrase « X est Y » devenait un `Fait enseigné`
  C/P/e8, sans fusion ni détection ; le rappel départageait **au nombre de copies**.
  Avec le patch, sur copie : **97 contrôles OK, 0 échec**. Le harnais de démo
  supposait un dossier déjà existant (défaut du harnais, pas du patch).
- **Ce qu’on en tire** : répéter ne doit pas rendre vrai ; on ajoute sans toucher
  aux bases, et on teste toujours sur copie d’abord.

### Phase N — Accès au nœud

- **Ce qu’on cherchait** : vérifier que le code déployé est bien celui du dépôt
  avant d’y appliquer le patch.
- **Ce qu’on a essayé** : connexion par l’interface filaire, puis par l’interface
  wifi après vérification que l’**empreinte de clé d’hôte** était identique à celle
  déjà connue ; `patch --dry-run` sur une copie des fichiers déployés.
- **Ce qu’on a constaté** : interface filaire **injoignable** (délai dépassé, absente
  de la table ARP). Le nœud n’est pas un clone git : `organism.py` y est « à plat »
  et en fins de ligne **CRLF**. Contenu identique au dépôt une fois les `\r` retirés,
  mais le dry-run échoue sur **5 hunks sur 5** (« different line endings ») → arrêt,
  rien changé. Option retenue : préparer les fichiers à plat sur la box
  (LF → patch → CRLF), contrôlés octet pour octet, et rejoués : 97 OK.
  Pare-feu `ufw` **volontairement laissé inchangé**.
- **Ce qu’on en tire** : un détail invisible (les fins de ligne) suffit à bloquer un
  patch ; une condition d’arrêt respectée vaut mieux qu’un forçage.

### Phase O — Déploiement de la détection des contradictions (25.10.2026 ~01:40)

- **Ce qu’on cherchait** : installer le patch sans rien perdre.
- **Ce qu’on a essayé** : arrêt du service, **sauvegarde horodatée** (index + état +
  `organism.py`), installation des 3 fichiers, redémarrage, puis protocole Vornex
  par `/perceive` (voir phase Q).
- **Ce qu’on a constaté** : service actif, aucune erreur, nombre de mémoires inchangé.
- **Ce qu’on en tire** : sauvegarde + commande de retour arrière écrite **avant** le
  changement. Détail : [fiche de changement](changements/2026-10-25_detection-contradictions.md).

### Phase P — Fusion des doublons (25.10.2026 ~01:44, accord de Vincent)

- **Ce qu’on cherchait** : retirer les copies exactes accumulées avant le patch, qui
  faussaient le rappel.
- **Ce qu’on a essayé** : dry-run sur une copie de l’index, puis nouvelle sauvegarde
  et `--apply`.
- **Ce qu’on a constaté** : **6 groupes** de doublons exacts fusionnés,
  **1044 → 1036** mémoires ; exposants des survivants inchangés, corrélations
  reciblées, contradictions laissées intactes, entrées retirées archivées.
- **Ce qu’on en tire** : nettoyer oui, effacer sans trace non : le dry-run montre,
  l’humain décide, l’archive garde.

### Phase Q — Test « Vornex » (contradiction bleue / rouge)

- **Ce qu’on cherchait** : vérifier en conditions réelles que la vérité ne se
  décide pas au nombre de répétitions.

| Étape | Résultat |
|-------|----------|
| « … est de couleur bleue. » | 1 fait e8 |
| « … est de couleur rouge. » | 2e fait e8, corrélation réciproque, **une** question `ask_human` |
| Rouge répété | aucun nouveau fait (doublon évité) |
| Question « De quelle couleur … ? » | `source: memory`, `uncertain`, les deux valeurs citées, « Je ne choisis pas » |
| Question posée 3 fois | **pas de relance** |

- **Ce qu’on a constaté** : comportement attendu à chaque étape. La question est
  laissée **en attente** pour Vincent.
- **Ce qu’on en tire** : la mémoire est consultée avant le LLM et dit son doute au
  lieu de choisir. Protocole : [`PROTOCOLE_TEST_CONTRADICTIONS.md`](PROTOCOLE_TEST_CONTRADICTIONS.md).

### Phase R — Test « Quarvel » (25.10.2026 23:20, verte / jaune)

- **Ce qu’on cherchait** : rejouer un test vérité / mensonge sans renforcer les
  faits Vornex encore en attente de réponse.
- **Ce qu’on a essayé** : le protocole prévu réutilisait le sujet Vornex → test
  **arrêté** avant tout envoi ; sujet neuf « lampe Quarvel du hangar » **validé par
  Vincent**, sauvegarde, puis verte → jaune → verte → question.
- **Ce qu’on a constaté** : contradiction **détectée**, corrélation réciproque ;
  le rappel **refuse de choisir** et cite les deux valeurs ; « verte » répétée :
  **pas de doublon**. **Aucune nouvelle question** : une seule peut être en attente
  (celle de Vornex l’était), c’est l’anti-harcèlement voulu. Le champ `uncertain`
  n’a pas pu être lu (sortie tronquée) : **non vérifié**.
- **Ce qu’on en tire** : un sujet de test ne se réutilise pas tant qu’une question
  est ouverte ; ce qu’on n’a pas vu, on l’écrit « non vérifié ».

### Phase S — Constats après les tests

- **Ce qu’on cherchait** : comprendre deux anomalies vues pendant le test Quarvel.
- **Ce qu’on a constaté** :
  1. **~226 souvenirs « Autonomie inhibée: … »** de plus depuis le matin, créés par la
     boucle de fond (introduite en **phase L**) : un `learn_perception` à chaque
     action bloquée.
  2. **`contradiction_ids` présent à tort dès le premier fait** (réponse de `/perceive`
     sans contradiction réelle : la liste contient le seul fait rappelé).
- **Ce qu’on en tire** : un test ciblé fait aussi apparaître des effets ailleurs ;
  on les note avant de les corriger.

### Phase T — Corrections autonomie et contradiction (25.10.2026 23:29–23:52)

> **Attention** : ces corrections ont été faites **sur le nœud** d’après le journal
> de session ; leur code **n’est pas** dans ce dépôt (branche de publication).
> Fiche de changement : *à créer dans [`changements/`](changements/)*.

- **Ce qu’on cherchait** : la cause des deux constats de la phase S.
- **Ce qu’on a essayé** : examen sur une copie en lecture seule (accord de Vincent :
  examiner et préparer, pas déployer). Causes trouvées : `autonomy.py` crée un
  souvenir à **chaque** tick bloqué (toutes les 300 s) ; `organism.py` renvoie
  `[entry.id, *ids]` même sans conflit. Patch testé sur copie : 0 échec (le code en
  production reproduisait le bug : 3 échecs), 97 OK.
- **Ce qu’on a constaté** :
  - Le patch v1 et un **nettoyage** (1271 → 730 entrées) ont été appliqués **avant**
    l’ordre d’arrêt de Vincent. Ce nettoyage ne gardait ni nombre ni dates dans le
    souvenir survivant ; rien n’a été perdu (archive complète + index d’avant).
  - Nouvelle décision de Vincent : « fusionne en gardant le nombre et les dates ».
    Patch A : `autonomy.py` compte les occurrences (avec dates ISO et fuseau) et
    `memory_system.py` sérialise ces champs (sinon ils disparaissaient à la
    sauvegarde). Testé sur copie, sauvegarde, appliqué. Le souvenir survivant
    porte **543 occurrences datées**, reconstituées une à une depuis le journal du
    nœud (changement d’heure du 25.10 compris).
  - Vérification à 10 min : 730 entrées stables, 0 corrélation orpheline, aucun
    nouveau souvenir « Autonomie inhibée », chaque tick compté.
  - Point d’attention noté : le renforcement (plafond 8) fait passer ce souvenir
    au-dessus du seuil d’injection (≥ 7).
- **Ce qu’on en tire** : une fusion doit garder la **trace** (combien, quand), pas
  seulement le texte ; et un ordre d’arrêt doit pouvoir interrompre une séquence
  déjà lancée.

| Reste à faire | État |
|---------------|------|
| Reporter ces correctifs dans le dépôt (code + tests) | à faire |
| Fiche de changement | à créer |
| Décider si ce souvenir doit rester au-dessus du seuil d’injection | à trancher |

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
| Accumulation « Autonomie inhibée » | déployé sur le nœud, à reporter dans le dépôt (phase T) | Haute |
| `contradiction_ids` sans contradiction | déployé sur le nœud, à reporter dans le dépôt (phase T) | Haute |
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
