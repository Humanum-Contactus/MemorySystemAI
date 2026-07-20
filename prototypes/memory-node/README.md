# Prototype `memory-node` — organisme incarné

Premier jet d’un **nœud Sensors&MemorySystemAI** : ardoise quasi vide,
outils sensoriels, consultation LLM externe, apprentissage par exposants,
nursery graphique locale, pont Telegram via OpenClaw.

> Ce n’est **pas** un chatbot avec interdits texte.  
> Le LLM (Kimi/Puter, Ollama, …) est un **outil**, pas l’identité.

## Contenu

| Fichier | Rôle |
|---------|------|
| `organism.py` | Runtime HTTP : mémoire + see/hear/speak + consult LLM + ask humain |
| `ui/index.html` | Nursery kiosk (interaction locale) |
| `systemd/memory-node.service.example` | Service Linux |
| `openclaw-skill/` | Skill + CLI + poller Telegram (exemple) |

## Boucle cognitive

```
perception (texte / micro / caméra)
    → rappel mémoire (prioritaire si fait déjà appris)
    → sinon consulter LLM (Puter/Kimi puis Ollama)
    → sinon ask_human
    → enregistrer (fondamentaux + exposant)
```

## API minimale

- `GET /` — nursery UI  
- `GET /status` `/memories` `/ask`  
- `POST /perceive` `/see` `/hear` `/speak` `/ask/answer` `/voice` `/reset`

## Déploiement rapide (idée)

1. Machine Linux avec caméra/micro (ex. laptop dédié).
2. Copier `MemorySystemAI/` (bibliothèque) + `organism.py` + `ui/`.
3. venv + deps (`faster-whisper` optionnel pour STT).
4. Ollama local **et/ou** token Puter dans `state/puter_token.txt`.
5. `systemd` + (optionnel) Openbox/Chromium kiosk sur `http://127.0.0.1:8765/`.
6. OpenClaw skill pointant vers `MEMORY_NODE_URL`.

## Secrets — ne jamais committer

- `state/puter_token.txt`
- tokens Telegram / mots de passe machine
- indexes mémoire personnels (`memory_index.json` de prod)

Voir aussi : [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](../../docs/EVOLUTION_MEMORY_NODE_2026-07.md).
