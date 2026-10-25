# Contribuer / Contributing — MemorySystemAI

> **FR + EN** · Politique des langues : [`docs/LANGUES.md`](docs/LANGUES.md)  
> Le français prime pour le sens conceptuel.

MIT License — Vincent Vermeille (Humanum Contactus).

---

## Français

### Philosophie du projet

MemorySystemAI est une démarche **empirique et pédagogique** : on essaie, on
observe, on note, et chacun doit pouvoir refaire le chemin. Le code doit encore
être compréhensible dans dix ans par quelqu'un qui n'a pas connu ses auteurs.
L'exemple du COBOL le montre : des programmes encore en service, et de moins en
moins de gens pour les comprendre, parce que le savoir est parti avec les
personnes au lieu d'être écrit à côté du code.

**Règle de base (Vincent)** : si les assistants disparaissent, n’importe qui doit
pouvoir **comprendre, relire et refaire** nos actions sans nous. Aucune dépendance
à un abonnement, à un service payant ou à un outil fermé. Concrètement : chaque
action est écrite dans le journal avec ses commandes exactes, les fichiers
touchés, la raison, le résultat observé et le retour en arrière.

Règles concrètes :

1. **Commenter pour un débutant.** Chaque fichier ajouté commence par un en-tête
   « À quoi sert ce fichier / Comment l'essayer ». Chaque fonction non évidente
   dit *pourquoi* elle existe et *comment* elle s'y prend, en français.
   Modèle : [`prototypes/memory-node/fact_conflict.py`](prototypes/memory-node/fact_conflict.py).
2. **Bibliothèque standard d'abord.** Python seul (`json`, `re`, `pathlib`,
   `http.server`…) tant que c'est raisonnable.
3. **Justifier chaque dépendance.** Une bibliothèque externe s'ajoute seulement
   si elle apporte ce que la bibliothèque standard ne peut pas faire (vision,
   transcription audio…). Elle reste **facultative** quand c'est possible et
   figure, avec sa raison, dans `requirements-optional.txt` ou la doc d'installation.
4. **Formats ouverts.** La mémoire, la configuration et la documentation sont en
   JSON, texte brut ou Markdown, lisibles avec n'importe quel éditeur.
5. **Pas de service fermé obligatoire.** Le nœud doit démarrer et se tester hors
   ligne. Un service extérieur (LLM, API) est un outil remplaçable, jamais une condition.
6. **Le journal raconte la démarche.** Chaque phase dit : *ce qu'on cherchait*
   (hypothèse), *ce qu'on a essayé*, *ce qu'on a constaté* (y compris les échecs),
   *ce qu'on en tire* (leçon). Voir [Continuer le journal](#continuer-le-journal).

### Ce qu’est ce projet

Système de **mémoire sensorielle-émotionnelle** pour agents IA : fondamentaux,
exposants, inhibition **apprise** — pas un chatbot avec interdits texte.

Le prototype `memory-node` (juillet 2026) montre un organisme quasi vide avec
capteurs, rappel mémoire d’abord, LLM = outil, tuteur humain.

**À lire avant de coder :**

1. [`whitepaper/MemorySystemAI_Whitepaper_v1.md`](whitepaper/MemorySystemAI_Whitepaper_v1.md) — **fondement**  
2. [`01_CONCEPT_FONDAMENTAL.txt`](01_CONCEPT_FONDAMENTAL.txt)  
3. [`docs/POURQUOI_CA_COMPTE.md`](docs/POURQUOI_CA_COMPTE.md)  
4. [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md)  
5. [`docs/MODULES_MEMORY_NODE.md`](docs/MODULES_MEMORY_NODE.md)  
6. [`prototypes/memory-node/README.md`](prototypes/memory-node/README.md)

### Règles de design (non négociables)

- **Pas d’interdits texte comme identité.** Inhibition = mémoires (exposant + tags).
- **Les normes vivent dans `memory_index`**, pas dans des tables Python / rate-limits.
- **Le LLM est un outil**, pas la persona de l’organisme.
- Préférer corroboration sensorielle et rappel mémoire plutôt que « demander au modèle ».
- Ne pas committer de secrets (`state/*_token.txt`, `.env`, journaux privés).
- Ardoise d’abord : pas de savoir encyclopédique au bootstrap.
- PRs petites et relisibles.

### Comment contribuer

1. Fork / branche depuis `main`.  
2. Choisir une [good first issue](docs/GOOD_FIRST_ISSUES.md) ou ouvrir une issue.  
3. Ouvrir une PR : *quoi*, *pourquoi*, *comment tester*.

```bash
python memory_cli.py stats
python memory_cli.py check "sudo rm -rf /efi"
```

### Continuer le journal

Le journal du projet = les chroniques `docs/EVOLUTION_MEMORY_NODE_AAAA-MM.md`.
Pour tout changement du prototype :

1. **Nouvelle phase** dans la chronique du mois en cours, **lettre suivante**
   (après W : X, Y, …) : ce qu’on cherchait, ce qu’on a essayé, ce qu’on a
   constaté, ce qu’on en tire, plus le retour arrière.
   Nouveau mois → nouvelle chronique qui **reprend là où la précédente s’arrête**
   (dernière phase, dernier état), avec liens *Précédent / Suivant* en tête et en fin
   des deux fichiers. Une période sans trace se dit « non documentée » : on n’invente rien.
2. **Nouvelle fiche** `docs/changements/AAAA-MM-JJ_sujet.md` : pourquoi, quoi,
   comment tester, comment revenir en arrière ; l’ajouter à
   [`docs/changements/README.md`](docs/changements/README.md).
3. **Entrée CHANGELOG** sous `[Non publié]`, avec lien vers la phase et la fiche.
4. **Tests** dans `prototypes/memory-node/tests/` ; les lister dans son `README.md`.
5. **Liens** : relatifs, puis `python3 tools/check_links.py` doit afficher 0 lien cassé.
6. Aucun secret ni donnée personnelle (IP, jetons, empreintes, visages, voix, proches) :
   utiliser des exemples génériques (`<IP_DU_NOEUD>`).

---

## English

### Project philosophy

MemorySystemAI is an **empirical, teaching-oriented** effort: try, observe,
write it down, so anyone can retrace the path. Code must still be understandable
in ten years by someone who never met its authors. COBOL shows why: programs still
running, fewer and fewer people who understand them, because the knowledge left
with the people instead of being written next to the code.

**Ground rule (Vincent)**: if the assistants disappear, anyone must be able to
**understand, review and redo** our actions without us. No dependency on a
subscription, a paid service or a closed tool. In practice: every action is
written in the journal with its exact commands, files touched, reason, observed
result and rollback.

Concrete rules (the French section is authoritative):

1. **Comment for a beginner.** Every new file opens with a "what this file is
   for / how to try it" header; every non-obvious function says *why* and *how*.
   Model: [`prototypes/memory-node/fact_conflict.py`](prototypes/memory-node/fact_conflict.py) (comments in French).
2. **Standard library first.**
3. **Justify every dependency**; keep it optional when possible and list it with
   its reason in `requirements-optional.txt` or the install docs.
4. **Open formats**: JSON, plain text, Markdown.
5. **No mandatory closed service**: the node must start and be testable offline.
6. **The journal tells the process**: hypothesis, what was tried, what was
   observed (failures included), lesson. See [Continuing the journal](#continuing-the-journal).

### What this project is

A **sensory-emotional memory system** for AI agents: fundamentals, emotional
exponents, **learned** inhibition — not a chatbot with text bans.

The July 2026 `memory-node` prototype shows an almost-empty organism with
sensors, memory-first recall, LLM-as-tool, and human tutoring.

**Read before coding:**

1. [`whitepaper/MemorySystemAI_Whitepaper_v1.md`](whitepaper/MemorySystemAI_Whitepaper_v1.md) — **foundation**  
2. [`docs/en/CONCEPT_FUNDAMENTAL.md`](docs/en/CONCEPT_FUNDAMENTAL.md) (overview) + FR `01_` for full depth  
3. [`docs/en/WHY_IT_MATTERS.md`](docs/en/WHY_IT_MATTERS.md)  
4. [`docs/en/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/en/EVOLUTION_MEMORY_NODE_2026-07.md)  
5. [`docs/en/MODULES_MEMORY_NODE.md`](docs/en/MODULES_MEMORY_NODE.md)  
6. [`prototypes/memory-node/README.en.md`](prototypes/memory-node/README.en.md)

### Design rules (non-negotiable)

- **No text bans as identity.** Inhibition = memories (exposant + tags).
- **Norms live in `memory_index`**, not Python lookup tables / rate-limit files.
- **LLM is a tool**, not the organism’s persona.
- Prefer sensory corroboration and memory-first recall over “just ask the model”.
- Do not commit secrets.
- Blank slate first — no encyclopedic bootstrap.
- Prefer small, reviewable PRs.

### How to contribute

1. Fork / branch from `main`.  
2. Pick a [good first issue](docs/GOOD_FIRST_ISSUES.md) or propose an issue.  
3. Open a PR with: *what*, *why*, *how to test*.

Thank you — merci.

### Continuing the journal

See the French section [« Continuer le journal »](#continuer-le-journal): new phase (next letter) in the current chronicle, a change sheet in `docs/changements/`, a CHANGELOG entry, tests, relative links checked with `python3 tools/check_links.py`.
