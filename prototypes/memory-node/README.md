# Prototype `memory-node` — organisme incarné

Premier jet d’un **nœud Sensors&MemorySystemAI** : ardoise quasi vide,
outils sensoriels, consultation LLM externe, apprentissage par exposants,
nursery graphique locale, pont Telegram via OpenClaw.

> Ce n’est **pas** un chatbot avec interdits texte.  
> Le LLM (Kimi/Puter, Ollama, …) est un **outil**, pas l’identité.

Documentation projet :

- [Chronique d’évolution](../../docs/EVOLUTION_MEMORY_NODE_2026-07.md)  
- [Architecture & API](../../docs/ARCHITECTURE_MEMORY_NODE.md)  
- [Pourquoi ça compte](../../docs/POURQUOI_CA_COMPTE.md)  
- [Index docs](../../docs/README.md)

---

## Contenu de ce dossier

| Fichier | Rôle |
|---------|------|
| `organism.py` | Runtime HTTP : mémoire + see/hear/speak + consult LLM + ask humain |
| `ui/index.html` | Nursery kiosk (interaction locale) |
| `systemd/memory-node.service.example` | Unit systemd |
| `openclaw-skill/` | Skill OpenClaw + `baby_api.py` + `ask_poller.py` |

Prérequis bibliothèque : placer le package `MemorySystemAI` (ce dépôt) dans
`PYTHONPATH` ou à côté de `organism.py` (voir chemins dans `organism.py` :
`ROOT=/opt/memorysystemai` en prod).

---

## Boucle cognitive

```
perception (texte / micro / caméra)
    → rappel mémoire (prioritaire si fait déjà appris)
    → sinon consulter LLM (Puter/Kimi puis Ollama)
    → sinon ask_human
    → enregistrer (fondamentaux + exposant)
```

---

## API (résumé)

| Méthode | Route | Rôle |
|---------|-------|------|
| GET | `/` | Nursery |
| GET | `/status` `/memories` `/ask` | État |
| POST | `/perceive` | Perception texte |
| POST | `/see` `/hear` `/speak` | Capteurs |
| POST | `/ask/answer` | Réponse tuteur |
| POST | `/voice` | Boucle écoute |
| POST | `/reset` | `{"confirm":"RESET_ORGANISM"}` |

Détail : [ARCHITECTURE_MEMORY_NODE.md](../../docs/ARCHITECTURE_MEMORY_NODE.md).

---

## Scénario de démo (texte)

```bash
export MEMORY_NODE_URL=http://127.0.0.1:8765

# 1. Identité
python openclaw-skill/baby_api.py perceive "Bonjour. Qui es-tu ?"

# 2. Nomination
python openclaw-skill/baby_api.py perceive "Je m appelle Vincent. Retiens mon nom."

# 3. Vérification
python openclaw-skill/baby_api.py perceive "Comment je m appelle ?"

# 4. Enseignement
python openclaw-skill/baby_api.py perceive "MonWifi est le reseau local via Starlink."

# 5. Rappel (doit idealement renvoyer source memory)
python openclaw-skill/baby_api.py perceive "Qu est-ce que MonWifi ?"
python openclaw-skill/baby_api.py status
```

Sur la nursery : même séquence via le champ texte + bouton **Kimi ON/OFF**.

---

## Déploiement (esquisse)

1. Machine Linux avec caméra/micro.  
2. Copier ce dépôt → ex. `/opt/memorysystemai/` (core + `organism.py` + `ui/`).  
3. `python3 -m venv .venv` + dépendances (Ollama client HTTP stdlib ; STT optionnel).  
4. Ollama local et/ou `state/puter_token.txt` (chmod 600).  
5. Installer `systemd/memory-node.service.example`.  
6. Optionnel : Openbox + Chromium kiosk → `http://127.0.0.1:8765/`.  
7. Optionnel : OpenClaw skill + `MEMORY_NODE_URL` + poller Telegram.

---

## Secrets — ne jamais committer

- `state/puter_token.txt`  
- tokens Telegram / mots de passe  
- `memory_index.json` de production (mémoires personnelles)

---

## Statut honnête

Prototype **abouti comme premier jet de démonstration du principe**.  
Pas encore le système nerveux complet (inhibition pré-action machine, multi-nœuds,
consolidation…). Voir feuille de route `04_FEUILLE_DE_ROUTE.txt`.
