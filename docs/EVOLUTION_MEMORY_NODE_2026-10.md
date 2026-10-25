# Évolution octobre 2026 — prototype `memory-node`

> **FR (source)** · **[English →](en/EVOLUTION_MEMORY_NODE_2026-10.md)** · [`LANGUES.md`](LANGUES.md)  
> ← **Précédent :** [Période 21.07 – 24.10.2026 (projet en pause)](EVOLUTION_MEMORY_NODE_2026-07-10.md) ·
> **Suivant :** *(aucun pour l’instant)* · [Index docs](README.md) · [CHANGELOG](../CHANGELOG.md)

**Auteur concept :** Vincent Vermeille (Humanum-Contactus)  
**Implémentation prototype :** session agent (poste de contrôle LAN → nœud)  
**Statut :** détection des contradictions, corrections autonomie et voix déployées sur le nœud et reportées dans ce dépôt  
**Code :** [`prototypes/memory-node/`](../prototypes/memory-node/)

Ce document **reprend exactement là où s’arrête** la
[chronique de juillet 2026](EVOLUTION_MEMORY_NODE_2026-07.md) (phase I), retrace
l’historique du dépôt entre les deux chroniques (phases J–L, d’après `git log`),
puis raconte le chantier d’octobre (phases M–W) : comment le nœud a appris à
**ne pas trancher seul** quand on lui enseigne deux versions incompatibles d’un fait.

Documents liés :

- [`changements/2026-10-25_detection-contradictions.md`](changements/2026-10-25_detection-contradictions.md) — fiche de changement (phases M–Q)  
- [`changements/2026-10-25_autonomie-contradiction-ids.md`](changements/2026-10-25_autonomie-contradiction-ids.md) — fiche (phases S–V)  
- [`changements/2026-10-25_voix-half-duplex.md`](changements/2026-10-25_voix-half-duplex.md) — fiche (phase W)  
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

- **Fichiers touchés** : ceux des commits ci-dessus. **Commandes** : non consignées
  (seul l’historique git existe). **Résultat** : visible dans les diffs.
  **Retour arrière** : `git revert de84c9f 7084cdb`

### Phase K — Boîte à outils d’autonomie (`autonomy.py`)

| Commit | Date (Zurich) | Contenu |
|--------|---------------|---------|
| `fa25480` | 21.07 14:13 | Nouveau `autonomy.py` (+763), `organism.py` (+120 / −4) : `probe_sensors`, `body_map`, `look_around`, `listen_ambient`, `reach_local`, `wonder`, `correlate`, `experiment_safe`, `craft_tool`, `ask_when_stuck`, `explore_cycle` ; chaque outil passe par `through_memory` (inhibition par tags → exécution → enregistrement). `POST /explore`, `POST /autonomy`, bouton « Explorer » dans la nursery |
| `74002c1` | 21.07 14:18 | Routes `/explore` et `/autonomy` documentées dans [`ARCHITECTURE_MEMORY_NODE.md`](ARCHITECTURE_MEMORY_NODE.md) |

Principe gardé : ce n’est **pas** une « curiosité LLM » ; ce sont des outils
sensoriels / méta qui nourrissent `memory_index`.

- **Fichiers touchés** : `prototypes/memory-node/autonomy.py`, `organism.py`, `ui/index.html`,
  `docs/ARCHITECTURE_MEMORY_NODE.md`. **Commandes** : non consignées (historique git
  seulement). **Retour arrière** : `git revert 74002c1 fa25480`

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

- **Commandes** : non consignées (historique git seulement). **Retour arrière** :
  `git revert e586d78`

### Période non documentée — 21.07.2026 15:07 → 24.10.2026

Aucun commit et aucune chronique publiée sur cette période. Le journal de session
privé n’est pas versionné. Seuls constats faits le 25.10 sur le nœud :

- le code en service était **identique à `e586d78`** (au format des fins de ligne près) ;
- l’index comptait **environ 1034 mémoires** ;
- le déploiement est **à plat** (pas de clone git sur le nœud).

Ce qui s’est passé entre-temps sur le nœud (usage, enseignements) **n’est pas documenté**.

---

### Chantier d’octobre 2026

### Comment lire chaque phase

Chaque phase suit le même plan : **ce qu’on cherchait** (hypothèse), **ce qu’on a
essayé**, **ce qu’on a constaté**, **ce qu’on en tire** (leçon), puis **fichiers
touchés**, **commandes exécutées** et **retour arrière**. Les commandes viennent du
journal de session ; les données privées y sont remplacées par des marqueurs
(`<UTILISATEUR>`, `<IP_DU_NOEUD>`, `<IP_FILAIRE_DU_NOEUD>`). Quand le journal ne
donne pas la commande mot pour mot, c’est écrit en commentaire
`# commande exacte non consignée` : rien n’est reconstitué.

### Phase M — Analyse et proposition (box, lecture seule ; 25.10.2026 01:13–01:34)

- **Ce qu’on cherchait** : savoir si le nœud peut se laisser convaincre par un
  mensonge répété, et pourquoi.
- **Ce qu’on a essayé** : lecture du chemin `/perceive` → `cycle_text` →
  `interpret_with_tools`, puis proposition minimale (module pur `fact_conflict.py`,
  branchement dans `organism.py`, script hors serveur `dedup_taught_facts.py`),
  essayée sur une **copie** du dépôt avec le protocole « Vornex ».
- **Ce qu’on a constaté** : chaque phrase « X est Y » devenait un `Fait enseigné`
  C/P/e8, sans fusion ni détection ; le rappel départageait **au nombre de copies**.
  Avec le patch, sur copie : **97 contrôles OK, 0 échec**. Le harnais de démo
  supposait un dossier déjà existant (défaut du harnais, pas du patch).
- **Ce qu’on en tire** : répéter ne doit pas rendre vrai ; on ajoute sans toucher
  aux bases, et on teste toujours sur copie d’abord.
- **Fichiers touchés** : aucun sur le nœud ; copie jetable sur la box.
- **Commandes** :

```bash
cp -a /workspace/MemorySystemAI /tmp/msai
cd /tmp/msai
patch -p1 --dry-run < proposition.patch   # redirection exacte non consignée ; « dry-run OK »
patch -p1 < proposition.patch             # idem ; « appliqué proprement »
python3 -m py_compile prototypes/memory-node/organism.py \
  prototypes/memory-node/fact_conflict.py prototypes/memory-node/dedup_taught_facts.py
# commande exacte non consignée : lancement du script de démonstration (97 contrôles)
```

- **Retour arrière** : `rm -rf /tmp/msai /tmp/prop /tmp/vornex-apply`

### Phase N — Accès au nœud (01:38–01:45)

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
- **Fichiers touchés** : aucun sur le nœud (copies dans `/tmp/stage`).
- **Commandes** :

```bash
ssh <UTILISATEUR>@<IP_FILAIRE_DU_NOEUD>          # → « Connection timed out »
Test-NetConnection <IP_FILAIRE_DU_NOEUD> -Port 22  # (PowerShell, poste de contrôle) → échec
ssh -v -o StrictHostKeyChecking=yes <UTILISATEUR>@<IP_DU_NOEUD>  # lecture de l’empreinte, forme exacte non consignée
patch -p1 --dry-run   # sur /tmp/stage/... → 5/5 hunks FAILED (« different line endings »)
# commandes exactes non consignées : conversion LF → patch → CRLF sur la box
```

- **Retour arrière** : sans objet ; nettoyage `rm -rf /tmp/stage /tmp/proposition.patch` sur le nœud.

### Phase O — Déploiement de la détection des contradictions (01:40–01:45)

- **Ce qu’on cherchait** : installer le patch sans rien perdre.
- **Ce qu’on a essayé** : arrêt du service, **sauvegarde horodatée** (index + état +
  `organism.py`), installation des 3 fichiers, redémarrage, puis protocole Vornex
  par `/perceive` (voir phase Q).
- **Ce qu’on a constaté** : service actif, aucune erreur, nombre de mémoires inchangé.
  `py_compile` n’a pas pu écrire son cache (`__pycache__` appartenant à root) : non
  bloquant, le service compile en mémoire.
- **Ce qu’on en tire** : sauvegarde + commande de retour arrière écrite **avant** le
  changement.
- **Fichiers touchés** : `organism.py`, `fact_conflict.py` (nouveau), `dedup_taught_facts.py` (nouveau).
- **Commandes** :

```bash
sudo systemctl stop memory-node
# commande exacte non consignée : création de backups/contradictions_20261025T014030.tgz
#   (MemorySystemAI/memory_index.json + state/ + organism.py)
tar tzf backups/contradictions_20261025T014030.tgz   # contrôle : 340 entrées
# commande exacte non consignée : copie des 3 fichiers dans /opt/memorysystemai
sudo systemctl start memory-node
```

- **Retour arrière** :

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/contradictions_20261025T014030.tgz && rm -f fact_conflict.py dedup_taught_facts.py && sudo systemctl start memory-node && systemctl is-active memory-node
```

  (restaure aussi l’index au 25.10 01:40:30 : les mémoires créées depuis seraient perdues.)
  Détail : [fiche de changement](changements/2026-10-25_detection-contradictions.md).

### Phase P — Fusion des doublons (01:44, accord de Vincent)

- **Ce qu’on cherchait** : retirer les copies exactes accumulées avant le patch, qui
  faussaient le rappel.
- **Ce qu’on a essayé** : dry-run sur une copie de l’index, puis nouvelle sauvegarde
  et `--apply`.
- **Ce qu’on a constaté** : **6 groupes** de doublons exacts fusionnés,
  **1044 → 1036** mémoires ; exposants des survivants inchangés, corrélations
  reciblées, contradictions laissées intactes, entrées retirées archivées.
- **Ce qu’on en tire** : nettoyer oui, effacer sans trace non : le dry-run montre,
  l’humain décide, l’archive garde.
- **Fichiers touchés** : `MemorySystemAI/memory_index.json` (+ `.bak-…` et `dedup-archive-….json` créés par le script).
- **Commandes** :

```bash
sudo systemctl stop memory-node
# commande exacte non consignée : création de backups/dedup_20261025T014429.tgz (index + state/)
tar tzf backups/dedup_20261025T014429.tgz        # 341 entrées
python3 dedup_taught_facts.py --index MemorySystemAI/memory_index.json            # dry-run (chemin exact non consigné)
python3 dedup_taught_facts.py --index MemorySystemAI/memory_index.json --apply    # idem
sudo systemctl start memory-node
```

- **Retour arrière** :

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/dedup_20261025T014429.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

### Phase Q — Test « Vornex » (contradiction bleue / rouge, ~01:45)

- **Ce qu’on cherchait** : vérifier en conditions réelles que la vérité ne se
  décide pas au nombre de répétitions.
- **Ce qu’on a essayé** : envois successifs à `/perceive` (sans voix) :

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
- **Fichiers touchés** : index (nouvelles mémoires), `state/ask_human.json`.
- **Commandes** :

```bash
# commande exacte non consignée : curl depuis le nœud vers 127.0.0.1:8765/perceive (speak=false),
#   une requête par phrase du tableau
```

- **Retour arrière** : celui de la phase O (efface aussi ces mémoires de test).

### Phase R — Test « Quarvel » (25.10.2026 23:17–23:25, verte / jaune)

- **Ce qu’on cherchait** : rejouer un test vérité / mensonge sans renforcer les
  faits Vornex encore en attente de réponse.
- **Ce qu’on a essayé** : le protocole prévu réutilisait le sujet Vornex → test
  **arrêté à 23:17** avant tout envoi ; sujet neuf « lampe Quarvel du hangar »
  **validé par Vincent** (« oui, va pour la lampe Quarvel »), sauvegarde, puis
  verte → jaune → verte → question.
- **Ce qu’on a constaté** : contradiction **détectée**, corrélation réciproque ;
  le rappel **refuse de choisir** et cite les deux valeurs ; « verte » répétée :
  **pas de doublon**. **Aucune nouvelle question** : une seule peut être en attente
  (celle de Vornex l’était), c’est l’anti-harcèlement voulu. Le champ `uncertain`
  n’a pas pu être lu (sortie tronquée) : **non vérifié**. L’index était passé de
  ~1036 à 1262 entrées depuis le matin (voir phase S).
- **Ce qu’on en tire** : un sujet de test ne se réutilise pas tant qu’une question
  est ouverte ; ce qu’on n’a pas vu, on l’écrit « non vérifié ».
- **Fichiers touchés** : index (+6 mémoires) ; `ask_human.json` inchangé.
- **Commandes** :

```bash
# commande exacte non consignée : création de backups/inhibition_20261025T232008.tgz
tar tzf backups/inhibition_20261025T232008.tgz   # 350 entrées
# commandes exactes non consignées : 4 envois à /perceive (É1 verte, É2 jaune, É3 verte, É4 question)
```

- **Retour arrière** (efface tout ce qui a été appris depuis 23:20:08) :

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/inhibition_20261025T232008.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

### Phase S — Constats après les tests

- **Ce qu’on cherchait** : comprendre deux anomalies vues pendant le test Quarvel.
- **Ce qu’on a constaté** :
  1. **~226 souvenirs « Autonomie inhibée: … »** de plus depuis le matin, créés par la
     boucle de fond (introduite en **phase L**) : un `learn_perception` à chaque
     action bloquée.
  2. **`contradiction_ids` présent à tort dès le premier fait** (la liste contient le
     seul fait rappelé, sans contradiction réelle).
- **Ce qu’on en tire** : un test ciblé fait aussi apparaître des effets ailleurs ;
  on les note avant de les corriger.
- **Fichiers touchés / commandes / retour arrière** : aucun (observation).

### Phase T — Examen des deux constats (23:29–23:35, rien modifié en production)

- **Ce qu’on cherchait** : la cause exacte de S.1 et S.2.
- **Ce qu’on a essayé** : accord de Vincent : « examiner et préparer, pas déployer ».
  Copie en lecture seule du nœud rapatriée sur la box, lecture du code, patch
  préparé et testé sur cette copie.
- **Ce qu’on a constaté** :
  - S.1 : `autonomy.py` (`through_memory`) crée un souvenir à **chaque** tick bloqué,
    toutes les 300 s (12 par heure) : **542** souvenirs, dont 541 au texte identique.
  - S.2 : `organism.py` renvoie `[entry.id, *ids]` même quand `ids` est vide ; la
    valeur est ensuite recopiée dans la réponse.
  - Sur copie : code patché **0 échec** ; code en production **3 échecs** (bug
    reproduit) ; démonstration contradictions **97 OK**. Dry-run du nettoyage :
    1 groupe, 1270 → 730.
  - Point d’attention : le renforcement (plafond 8) ferait passer le souvenir
    survivant au-dessus du seuil d’injection (≥ 7).
- **Ce qu’on en tire** : reproduire le bug sur l’ancien code avant de croire au correctif.
- **Fichiers touchés** : aucun en production.
- **Commandes** :

```bash
# commandes exactes non consignées : archive /tmp/autosnap.tgz sur le nœud, rapatriée sur la box
# commandes exactes non consignées : lancement des tests sur copie (ancien code / code patché)
```

- **Retour arrière** : sans objet.

### Phase U — Correction : `contradiction_ids` annoncé trop tôt (déployée à 23:36)

- **Ce qu’on cherchait** : qu’un premier fait ne soit plus présenté comme une contradiction.
- **Ce qu’on a essayé** : une ligne : `[entry.id, *ids] if ids else []`, livrée dans
  le même patch que la phase V (v1).
- **Ce qu’on a constaté** : sur copie, É1 propre, É2/É4 `uncertain: true` + 2 ids ;
  appliqué en production avec la phase V (dry-run OK, fins de ligne CRLF conservées,
  `compile()` en mémoire OK). Test automatisé :
  [`tests/test_autonomie.py`](../prototypes/memory-node/tests/test_autonomie.py) (section 4).
- **Ce qu’on en tire** : un champ d’API doit dire la même chose que l’état réel.
- **Fichiers touchés** : `organism.py`. Fiche : [`changements/2026-10-25_autonomie-contradiction-ids.md`](changements/2026-10-25_autonomie-contradiction-ids.md).
- **Commandes / retour arrière** : voir phase V (même patch, même sauvegarde).

### Phase V — « Autonomie inhibée » : compter au lieu de recopier (23:36–23:52)

- **Ce qu’on cherchait** : arrêter l’accumulation de copies sans perdre l’histoire
  des refus.
- **Ce qu’on a essayé** :
  1. **Patch v1** : un refus identique **renforce** le souvenir existant (même règle
     que les faits enseignés, plafond 8) au lieu d’en créer un nouveau.
  2. **Nettoyage v1** du stock existant (1271 → 730).
  3. **Stop de Vincent**, puis **nouvelle décision** : « fusionne en gardant le
     nombre et les dates ».
  4. **Patch A** : `autonomy.py` compte les occurrences (`occurrences` +
     `occurrence_dates` ISO avec fuseau) ; `memory_system.py` sérialise et relit ces
     deux champs (sinon `to_dict` / `from_dict` les effaçaient à chaque sauvegarde).
  5. **Fusion avec occurrences** vers le souvenir survivant de l’autonomie inhibée, en reconstruisant le
     compteur depuis l’archive du nettoyage v1 et les heures depuis le journal du nœud.
- **Ce qu’on a constaté** :
  - Le nettoyage v1 a été appliqué à 23:36:26, **avant** l’ordre d’arrêt de Vincent,
    et il **ne gardait ni le nombre ni les dates**. Rien n’a été perdu : archive
    complète des 541 entrées retirées + index complet d’avant ; rien n’a été restauré.
  - Patch A testé sur copie : 3 ticks → compteur +3, entrées stables, champs conservés
    après sauvegarde et rechargement, 0 orphelin, 97 tests OK.
  - Fusion : **543 occurrences** (1 + 541 archivées + 1 renforcement), 543 dates ISO.
    Les heures du journal du nœud correspondaient une pour une, jour par jour
    (21.07 : 76, 22.07 : 210, 24.10 : 5, 25.10 : 252) ; le changement d’heure du
    25.10 (02:xx en double) est géré (+02:00 puis +01:00).
  - Résultat : **730 souvenirs**, 0 corrélation orpheline. Vérification à 10 min
    (23:51) : 730 stables, aucun nouveau « Autonomie inhibée », chaque tick compté
    (546 occurrences), survivant à e8.
- **Ce qu’on en tire** : une fusion doit garder la **trace** (combien, quand), pas
  seulement le texte ; un ordre d’arrêt doit pouvoir interrompre une séquence déjà
  lancée ; un nouveau champ n’existe vraiment que si la sauvegarde le conserve.
- **Fichiers touchés** : `autonomy.py`, `organism.py` (phase U), `memory_system.py`,
  index (+ archive `autonomie-archive-….json` et copies `.bak-…`). Scripts :
  [`maintenance/`](../prototypes/memory-node/maintenance/README.md).
  Fiche : [`changements/2026-10-25_autonomie-contradiction-ids.md`](changements/2026-10-25_autonomie-contradiction-ids.md).
- **Commandes** :

```bash
sudo systemctl stop memory-node                                    # 23:36:07
# commande exacte non consignée : création de backups/autonomie_20261025T233607.tgz
patch -p1 --dry-run < proposition.patch   # forme exacte non consignée ; « dry-run OK »
# commande exacte non consignée : application du patch v1
python3 nettoyage_autonomie_inhibee.py --index MemorySystemAI/memory_index.json --apply   # chemin exact non consigné
sudo systemctl start memory-node                                   # 23:36:46
sudo systemctl stop memory-node                                    # 23:40:03
# commande exacte non consignée : création de backups/autonomie_occurrences_20261025T234003.tgz
# commande exacte non consignée : application du patch A
python3 fusion_autonomie_occurrences.py --index MemorySystemAI/memory_index.json \
  --keep <ID_DU_SURVIVANT> --archive MemorySystemAI/autonomie-archive-20261025-233626.json --log <JOURNAL_DU_NOEUD>
#   (dry-run puis --apply à 23:40:22 ; arguments exacts non consignés)
sudo systemctl start memory-node                                   # 23:40:22
```

- **Retour arrière** :

```bash
# avant la fusion avec occurrences (code v1 + index à 730) :
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/autonomie_occurrences_20261025T234003.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
# complet (code d’origine + index à 1271) :
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/autonomie_20261025T233607.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

  Cette dernière archive ne contient pas `memory_system.py` : le restaurer depuis
  `autonomie_occurrences_20261025T234003.tgz` ou garder la version patchée
  (rétrocompatible). Les deux retours arrière effacent ce qui a été appris depuis.

### Phase W — Corrections voix (23:53)

- **Ce qu’on cherchait** : que le nœud ne prenne plus sa propre voix de synthèse
  pour une personne.
- **Ce qu’on a essayé** :
  1. `autonomy.py` : `hear_self` n’appelle plus `voice.process_wav` (l’apprentissage
     de la perception est gardé) ;
  2. `voice_memory.py` : les clips `tts_self_*` sont ignorés (`_is_tts_self`) par
     `process_wav` et `label_pending_or_last` ;
  3. `organism.py` : half-duplex `SPEAKING` autour des lectures audio, garde de 0,5 s ;
     l’enregistrement attend au plus 100 s puis enregistre quand même ;
  4. suppression de la fausse fiche voix, qui était la voix de synthèse elle-même.
- **Ce qu’on a constaté** : tests sur copie **20/20**, démonstration contradictions
  97 OK ; en production : service actif, 0 erreur, fiches existantes inchangées,
  question en attente inchangée. `hear_self` n’ayant pas tourné depuis, la
  correction 1 est **vérifiée sur copie uniquement**. `sensory_agent.py` (autre
  processus qui enregistre) n’est **pas** couvert par `SPEAKING` (non modifié).
- **Ce qu’on en tire** : une machine qui s’écoute doit savoir distinguer sa voix ;
  le plus simple est de ne pas écouter pendant qu’elle parle.
- **Fichiers touchés** : `autonomy.py`, `voice_memory.py`, `organism.py`,
  `state/voice_persons.json`. Test : [`tests/test_voix.py`](../prototypes/memory-node/tests/test_voix.py).
  Fiche : [`changements/2026-10-25_voix-half-duplex.md`](changements/2026-10-25_voix-half-duplex.md).
- **Commandes** :

```bash
sudo systemctl stop memory-node                                    # 23:53:40
# commande exacte non consignée : création de backups/voix_20261025T235340.tgz (355 fichiers)
# commande exacte non consignée : installation des fichiers patchés (voix.patch)
python3 supprimer_vp002.py state/voice_persons.json --apply   # chemin exact non consigné
sudo systemctl start memory-node                                   # 23:53:43
```

- **Retour arrière** :

```bash
# commande non consignée au journal ; sur le modèle des phases précédentes :
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/voix_20261025T235340.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

| Reste à faire | État |
|---------------|------|
| Décider si le souvenir « Autonomie inhibée » doit rester au-dessus du seuil d’injection (≥ 7) | à trancher |
| Couvrir `sensory_agent.py` par le half-duplex | reporté (décision de Vincent : « pas maintenant ») |
| Répondre aux questions Vornex en attente | Vincent |


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

Boucle de fond (phase L) : tick_initiative → through_memory → « Autonomie inhibée »
      └─ même refus → renforcement + occurrences / dates   (phase V)

Voix (phase W) : lecture TTS → SPEAKING levé → micro en attente (+0,5 s)
      hear_self → pas d’empreinte vocale ; clips tts_self_* ignorés
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
8. Une fusion doit garder la trace (nombre, dates), et un nouveau champ n’existe
   que si la sauvegarde le conserve (phase V).
9. Un ordre d’arrêt doit pouvoir interrompre une séquence déjà lancée (phase V).
10. Une machine qui s’écoute doit reconnaître sa propre voix (phase W).

---

## 6. Suite (priorités concept)

| Point | État | Priorité |
|-------|------|----------|
| Accumulation « Autonomie inhibée » | corrigé (phases U–V) | — |
| `contradiction_ids` sans contradiction | corrigé (phases U–V) | — |
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
| `prototypes/memory-node/autonomy.py` | Outils d’autonomie, boucle d’initiative | K–L, V–W |
| `prototypes/memory-node/fact_conflict.py` | Heuristique sujet / valeur, bibliothèque standard | O |
| `prototypes/memory-node/dedup_taught_facts.py` | Fusion des doublons (dry-run par défaut) | O–P |
| `prototypes/memory-node/organism.py` | Runtime ; branchements L, O, U, W | L, O, U, W |
| `prototypes/memory-node/voice_memory.py` | Mémoire des voix ; ignore `tts_self_*` | W |
| `memory_system.py` | Champs facultatifs `occurrences` / `occurrence_dates` | V |
| `prototypes/memory-node/maintenance/` | Scripts manuels (fusion, suppression de la fausse fiche voix) | V–W |
| `prototypes/memory-node/tests/` | Tests automatisés (97 + 15 + 18 contrôles) | O, U–W |
| `docs/changements/` | Fiches de changement | O, U–W |

---

## 8. Remerciements / provenance

Concept et finalité : **Vincent Vermeille** (Humanum-Contactus).  
Juillet 2026 (phases J–L) : commits du dépôt. Octobre 2026 (phases M–W) :
collaboration humaine + agent ; chaque étape soumise à Vincent, sauvegardée avant
et réversible — sauf le nettoyage v1 de la phase V, appliqué avant son ordre
d’arrêt (rien perdu : archive complète).

---

← **Précédent :** [Période 21.07 – 24.10.2026 (projet en pause)](EVOLUTION_MEMORY_NODE_2026-07-10.md) ·
**Suivant :** *(aucun pour l’instant)* · [Index docs](README.md) · [CHANGELOG](../CHANGELOG.md) ·
[Fiches de changement](changements/README.md)
