# Journal des modifications (CHANGELOG)

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Dates au format JJ.MM.AAAA (heure de Zurich). Le récit détaillé est dans les chroniques :

| Chronique | Phases |
|-----------|--------|
| [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md) | A–I |
| [`docs/EVOLUTION_MEMORY_NODE_2026-10.md`](docs/EVOLUTION_MEMORY_NODE_2026-10.md) | J–T |

Fiches de changement : [`docs/changements/`](docs/changements/) ·
Règle pour continuer : [`CONTRIBUTING.md`](CONTRIBUTING.md#continuer-le-journal) ·
Index : [`docs/README.md`](docs/README.md)

## [Non publié]

### En cours (non déployé) — [phase T](docs/EVOLUTION_MEMORY_NODE_2026-10.md#phase-t--corrections-en-cours-danalyse-en-cours--non-déployé)
- Limiter l’accumulation des souvenirs « Autonomie inhibée » créés par la boucle de fond (~226 en une journée).
- Ne plus renvoyer `contradiction_ids` quand il n’y a pas de contradiction.

### Ajouté — phases M–R, fiche [`2026-10-25_detection-contradictions`](docs/changements/2026-10-25_detection-contradictions.md)
- `prototypes/memory-node/fact_conflict.py` : détection des contradictions entre faits enseignés (sujet / valeur, accord simple, préambules).
- `prototypes/memory-node/dedup_taught_facts.py` : fusion manuelle des doublons exacts (dry-run par défaut, sauvegarde + archive avec `--apply`).
- `prototypes/memory-node/tests/test_contradictions.py` : 97 contrôles automatisés (script ou pytest).
- Documentation : installation, protocole de test contradictions, fiche de changement, chronique octobre 2026.
- `config.example.env`, `requirements-optional.txt`, `requirements-dev.txt`, unité systemd générique.

### Modifié
- `prototypes/memory-node/organism.py` : branchement de la détection dans `cycle_text` et `interpret_with_tools` ; doublon = renforcement (plafond 8) ; contradiction = corrélations réciproques + une seule question `ask_human` ; rappel incertain sans LLM. `learn_perception` renvoie l’entrée créée.
- `.gitignore` : caches Python.

### Inchangé (bases du concept)
- Exposants 1-10, injection ≥ 7, blocage ≥ 9, plancher 7 pour 9-10, inhibition apprise par tags, normes vivantes, fondamentaux des sens, mémoire consultée avant le LLM, `ask_human` sans harceler.

### Déploiement sur le nœud du prototype
- 25.10.2026 ~01:40 : détection des contradictions déployée.
- 25.10.2026 ~01:44 : 6 groupes de doublons fusionnés (1044 → 1036 mémoires).

## [2026-07-21] — `e586d78`

Chronique : [phases J–L](docs/EVOLUTION_MEMORY_NODE_2026-10.md#entre-les-deux-chroniques--daprès-git-log-21072026) (d’après `git log`).

- `e586d78` — Autonomie durcie : normes vivantes, bilan de source, crible avant LLM, corroboration, maturité, critique des gestes, `hear_self`, boucle d’initiative de fond.
- `74002c1` — Routes `/explore` et `/autonomy` documentées.
- `fa25480` — Boîte à outils d’autonomie `autonomy.py`, `POST /explore`, `POST /autonomy`.
- `7084cdb` — Le whitepaper devient le fondement de la documentation.
- `de84c9f` — Bannière bilingue du document de nommage.

## [2026-07-20 – 2026-07-21] — prototype `memory-node`

Chronique : [phases A–I](docs/EVOLUTION_MEMORY_NODE_2026-07.md).

- `2cbf065` — Documentation bilingue (FR source, miroirs EN).
- `80f258c` — Évolution memory-node documentée : capteurs, identité, normes apprises.
- `92843d9` — `CONTRIBUTING`, good first issues, modèles d’issues.
- `56a6831`, `434eb97` — Prototype `memory-node` et documentation Sensors&MemorySystemAI.

## [1.1] — 09.05.2026 — `310e761`

- Implémentation Python : cœur `MemorySystem`, CLI, intégration OpenClaw, données d’amorçage.

## [1.0] — 04.05.2026 — `ba8ff51`

- MemorySystemAI : système nerveux artificiel (mémoire sensorielle, exposants émotionnels, inhibition apprise).
