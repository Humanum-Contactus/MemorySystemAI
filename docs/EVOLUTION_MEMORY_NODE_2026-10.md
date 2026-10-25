# Évolution octobre 2026 — prototype `memory-node`

> **FR (source)** · *(traduction anglaise à venir)* · [`LANGUES.md`](LANGUES.md)

**Auteur concept :** Vincent Vermeille (Humanum-Contactus)  
**Implémentation prototype :** session agent (poste de contrôle LAN → nœud)  
**Statut :** détection des contradictions déployée sur le nœud ; corrections d’autonomie en analyse  
**Code :** [`prototypes/memory-node/`](../prototypes/memory-node/)

Ce document **prolonge** la [chronique de juillet 2026](EVOLUTION_MEMORY_NODE_2026-07.md) :
comment le nœud a appris à **ne pas trancher seul** quand on lui enseigne deux
versions incompatibles d’un même fait.

Documents liés :

- [`changements/2026-10-25_detection-contradictions.md`](changements/2026-10-25_detection-contradictions.md) — fiche de changement  
- [`PROTOCOLE_TEST_CONTRADICTIONS.md`](PROTOCOLE_TEST_CONTRADICTIONS.md) — protocole de test générique  
- [`INSTALLATION.md`](INSTALLATION.md) — installer et tester  
- [`../CHANGELOG.md`](../CHANGELOG.md) — historique des versions  

---

## 0. Résumé en une phrase

Répéter un mensonge ne le rend plus vrai : deux faits enseignés contradictoires
sont **liés** dans la mémoire, le rappel **refuse de choisir** et l’humain est
interrogé **une seule fois** — sans toucher aux bases du concept.

---

## 1. Intention (rappel du concept)

**Problème.** Sur le chemin `/perceive`, chaque phrase en « est » devenait un
`Fait enseigné` à exposant 8. Vérité et mensonge coexistaient à e8 et le rappel
départageait **par le nombre de copies** : le plus répété gagnait.

**Objectif.** Rester fidèle à Sensors&MemorySystemAI :

1. **Mémoire consultée avant le LLM** — y compris pour dire « je ne sais pas trancher »  
2. **Exposants inchangés** — 1-10, injection ≥ 7, blocage ≥ 9, plancher 7 pour 9-10  
3. **L’humain comme tuteur** — `ask_human`, une question, **sans harceler**  
4. **Normes vivantes** — rien de figé en table `.py`  

---

## 2. Chronologie du chantier

### Phase J — Analyse et proposition (box, lecture seule)

- Lecture du chemin `/perceive` → `cycle_text` → `interpret_with_tools`.
- Constat : pas de fusion, pas de détection, départage par répétition.
- Proposition minimale : un module pur `fact_conflict.py`, un branchement dans
  `organism.py`, un script hors serveur `dedup_taught_facts.py`.
- Démonstration locale (protocole « Vornex ») : **97 contrôles OK, 0 échec** sur copie.

### Phase K — Accès au nœud

- Le nœud était **injoignable par son interface filaire** (délai dépassé, absent de la table ARP).
- Connexion faite par son **interface wifi**, après vérification que l’**empreinte de
  clé d’hôte** était identique à celle déjà connue pour le nœud.
- Pare-feu `ufw` **volontairement laissé inchangé** : le port de l’API reste limité
  à un seul poste du réseau local.
- Le déploiement est **à plat** (`organism.py` directement dans le dossier
  d’installation, pas de clone git) ; fichiers en fins de ligne CRLF → patch
  adapté (LF → patch → CRLF), contrôlé octet pour octet.

### Phase L — Déploiement de la détection des contradictions (25.10.2026 ~01:40)

- Arrêt du service, **sauvegarde horodatée** (index + état + `organism.py`).
- Installation : `fact_conflict.py`, `dedup_taught_facts.py`, `organism.py` modifié.
- Redémarrage : service actif, aucune erreur, nombre de mémoires inchangé.

### Phase M — Fusion des doublons (25.10.2026 ~01:44, accord de Vincent)

- Dry-run puis `--apply` après nouvelle sauvegarde : **6 groupes** de doublons
  exacts fusionnés, **1044 → 1036** mémoires.
- Exposants des survivants inchangés, corrélations reciblées, aucune contradiction touchée.

### Phase N — Test « Vornex » (contradiction bleue / rouge)

| Étape | Résultat |
|-------|----------|
| « … est de couleur bleue. » | 1 fait e8 |
| « … est de couleur rouge. » | 2e fait e8, corrélation réciproque, **une** question `ask_human` |
| Rouge répété | aucun nouveau fait (doublon évité) |
| Question « De quelle couleur … ? » | `source: memory`, `uncertain`, les deux valeurs citées, « Je ne choisis pas » |
| Question posée 3 fois | **pas de relance** |

### Phase O — Test « Quarvel » (25.10.2026 23:20, verte / jaune)

- Sujet neuf, pour ne pas renforcer les faits Vornex encore en attente de réponse.
- Contradiction **détectée**, corrélation réciproque.
- Rappel : **refuse de choisir**, cite les deux valeurs.
- Répétition de « verte » : **pas de doublon**.
- **Aucune nouvelle question** : une seule question peut être en attente à la fois
  (la question Vornex l’était) — comportement voulu, c’est l’anti-harcèlement.

### Phase P — Constats après les tests

1. **~226 souvenirs « Autonomie inhibée: … »** accumulés par la boucle de fond
   (`autonomy.py`) en une journée : un `learn_perception` à chaque action bloquée.
2. **`contradiction_ids` présent à tort dès le premier fait** (réponse de `/perceive`
   sans contradiction réelle : la liste contient le seul fait rappelé).

### Phase Q — Corrections en cours d’analyse *(EN COURS — non déployé)*

> **Entrée à compléter par Vincent / la session suivante.**

| Correction | Piste | État |
|------------|-------|------|
| Accumulation « Autonomie inhibée » | *à compléter* | en analyse |
| `contradiction_ids` dès le premier fait | *à compléter* | en analyse |

- Date de déploiement : *à compléter*  
- Tests : *à compléter*  
- Retour arrière : *à compléter*  

---

## 3. Architecture résultante

```
POST /perceive
   │
   ├─ correction auditive / identité / feedback   (inchangés)
   ├─ fait enseigné (« X est Y »)
   │     └─ fact_conflict.classify_new_fact
   │           ├─ nouveau        → Fait enseigné C/P/e8 (comme avant)
   │           ├─ doublon        → renforcement (plafond 8), pas de nouvelle entrée
   │           └─ contradiction  → nouveau fait + corrélations réciproques
   │                               + 1 question ask_human (si boîte libre)
   └─ interpret_with_tools
         ├─ inhibition (≥ 9)                       (inchangé)
         ├─ contradiction ouverte → rappel incertain, source memory
         ├─ rappel mémoire                          (inchangé)
         └─ LLM / ask_human                          (inchangé)
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

---

## 6. Suite (priorités concept)

| Point | État | Priorité |
|-------|------|----------|
| Accumulation « Autonomie inhibée » | en analyse | Haute |
| `contradiction_ids` sans contradiction | en analyse | Haute |
| Réponse humaine aux questions Vornex en attente | en attente de Vincent | Moyenne |
| `GET /memories` sans corrélations | connu | Basse |
| Heuristique « premier est » (français simple) | limite connue | Moyenne |

---

## 7. Carte des fichiers

| Chemin | Rôle |
|--------|------|
| `prototypes/memory-node/fact_conflict.py` | Heuristique sujet / valeur, bibliothèque standard |
| `prototypes/memory-node/dedup_taught_facts.py` | Fusion des doublons (dry-run par défaut) |
| `prototypes/memory-node/organism.py` | Branchement dans `cycle_text` et `interpret_with_tools` |
| `prototypes/memory-node/tests/` | Tests automatisés (97 contrôles) |
| `docs/changements/` | Fiches de changement |

---

## 8. Remerciements / provenance

Concept et finalité : **Vincent Vermeille** (Humanum-Contactus).  
Chantier octobre 2026 : collaboration humaine + agent, chaque étape validée par Vincent,
sauvegardée avant, et réversible.
