# Journal des modifications (CHANGELOG)

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Dates au format JJ.MM.AAAA (heure de Zurich). Le récit détaillé est dans
[`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md) et
[`docs/EVOLUTION_MEMORY_NODE_2026-10.md`](docs/EVOLUTION_MEMORY_NODE_2026-10.md).

## [Non publié]

### En cours (non déployé)
- Limiter l’accumulation des souvenirs « Autonomie inhibée » créés par la boucle de fond (~226 en une journée).
- Ne plus renvoyer `contradiction_ids` quand il n’y a pas de contradiction.

### Ajouté
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
- Durcissement de l’autonomie du memory-node : bilan de source, rappel, état de préparation et critique gestuelle dans `memory_index`.
- Prototype `memory-node` (phases A–I) : voir la chronique de juillet 2026.
