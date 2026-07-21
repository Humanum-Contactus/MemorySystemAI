# Contribuer / Contributing — MemorySystemAI

> **FR + EN** · Politique des langues : [`docs/LANGUES.md`](docs/LANGUES.md)  
> Le français prime pour le sens conceptuel.

MIT License — Vincent Vermeille (Humanum Contactus).

---

## Français

### Ce qu’est ce projet

Système de **mémoire sensorielle-émotionnelle** pour agents IA : fondamentaux,
exposants, inhibition **apprise** — pas un chatbot avec interdits texte.

Le prototype `memory-node` (juillet 2026) montre un organisme quasi vide avec
capteurs, rappel mémoire d’abord, LLM = outil, tuteur humain.

**À lire avant de coder :**

1. [`01_CONCEPT_FONDAMENTAL.txt`](01_CONCEPT_FONDAMENTAL.txt)  
2. [`docs/POURQUOI_CA_COMPTE.md`](docs/POURQUOI_CA_COMPTE.md)  
3. [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md)  
4. [`docs/MODULES_MEMORY_NODE.md`](docs/MODULES_MEMORY_NODE.md)  
5. [`prototypes/memory-node/README.md`](prototypes/memory-node/README.md)

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

---

## English

### What this project is

A **sensory-emotional memory system** for AI agents: fundamentals, emotional
exponents, **learned** inhibition — not a chatbot with text bans.

The July 2026 `memory-node` prototype shows an almost-empty organism with
sensors, memory-first recall, LLM-as-tool, and human tutoring.

**Read before coding:**

1. [`docs/en/CONCEPT_FUNDAMENTAL.md`](docs/en/CONCEPT_FUNDAMENTAL.md) (overview) + FR `01_` for full depth  
2. [`docs/en/WHY_IT_MATTERS.md`](docs/en/WHY_IT_MATTERS.md)  
3. [`docs/en/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/en/EVOLUTION_MEMORY_NODE_2026-07.md)  
4. [`docs/en/MODULES_MEMORY_NODE.md`](docs/en/MODULES_MEMORY_NODE.md)  
5. [`prototypes/memory-node/README.en.md`](prototypes/memory-node/README.en.md)

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
