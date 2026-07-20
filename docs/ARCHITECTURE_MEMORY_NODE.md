# Architecture — prototype `memory-node`

## Vue d’ensemble

```
                    ┌─────────────────────────────────────┐
                    │         HUMAIN (tuteur)             │
                    │  nursery locale  ·  Telegram/OpenClaw│
                    └──────────────┬──────────────────────┘
                                   │ perceive / answer / feedback
                                   ▼
┌──────────────────────────────────────────────────────────────┐
│  organism.py  (HTTP :8765)                                   │
│                                                              │
│  1. Réception     texte | hear | see                         │
│  2. Rappel        MemorySystem.recall (prioritaire)          │
│  3. Consultation  Puter/Kimi → Ollama   (si mémoire insuff.) │
│  4. Ask human     /ask pending          (si LLM ne sait pas) │
│  5. Enregistrement fondamentaux + exposant + source          │
│  6. Expression    utterance (+ speak optionnel)              │
└──────────────┬───────────────────────────┬───────────────────┘
               │                           │
               ▼                           ▼
     memory_index.json              outils OS
     (MemorySystemAI core)          caméra / micro / espeak
```

## Séparation des rôles

| Composant | Rôle | N’est pas |
|-----------|------|-----------|
| `MemorySystem` | stocker, scorer, inhiber | un LLM |
| `organism.py` | boucle sensorielle + API | un chatbot persona |
| Puter/Kimi / Ollama | interpréter une perception | l’identité du bébé |
| OpenClaw / Telegram | relais humain distant | le système de mémoire |
| Nursery UI | présence locale | un dashboard générique |

## Boucle décisionnelle (détail)

```
perception
  │
  ├─ inhibition mémoire (exposant élevé + tags) ──► abstention
  │
  ├─ usable_memory_answer ? ──oui──► source: memory  (pas de LLM)
  │
  ├─ interprétation externe (Puter.js nursery) ?
  │
  ├─ tool_consult_llm (Puter token puis Ollama)
  │     ├─ OK ──► apprendre interprétation (I) + perçu
  │     └─ JE NE SAIS PAS / fail
  │              ├─ réponse humaine fraîche pertinente ?
  │              └─ sinon tool_ask_human → source: ask-human
  ▼
utterance
```

### Règles d’apprentissage (prototype)

- Perception / message → souvent exposant **5** (journal).
- Enseignement factuel humain (`X est Y`, sans `?`) → exposant **8**, préfixe « Fait enseigné… ».
- Réponse à `/ask/answer` → exposant **8**, « Réponse humaine intégrée… ».
- Feedback positif / négatif → états **P** / **N**, exposant renforcé.
- Bootstrap au reset → **6 entrées méta** seulement (pas de savoir du monde).

### Rappel mémoire avant LLM

Le rappel pondère :

- chevauchement lexical (bonus noms longs),
- exposant,
- source humaine / « Fait enseigné »,
- malus sur le bruit de journal (`Message reçu:`, `Interprétation (`…).

Objectif : **apprendre pour de vrai**, pas reconsulter Kimi à chaque fois.

## API HTTP

Base : `http://HOST:8765`

### GET

| Route | Description |
|-------|-------------|
| `/` ou `/ui/` | Nursery HTML |
| `/status` | rôle, nb mémoires, puter, voice_loop, ask_pending |
| `/memories` | liste des entrées |
| `/ask` | état demande humaine (`none` / `pending` / `answered` / `consumed`) |

### POST (JSON)

| Route | Body typique | Effet |
|-------|--------------|-------|
| `/perceive` | `{ "text", "speak?", "interpretation?", "llm_source?" }` | cycle texte / conscience |
| `/see` | `{ "speak?" }` | capture caméra + interprétation |
| `/hear` | `{ "seconds?", "speak?" }` | enregistrement + STT + interprétation |
| `/speak` | `{ "text" }` | TTS |
| `/voice` | `{ "enabled": true\|false }` | boucle écoute continue |
| `/ask/answer` | `{ "answer" }` | intègre réponse humaine (exposant 8) |
| `/reset` | `{ "confirm": "RESET_ORGANISM" }` | ardoise → bootstrap méta |

Exemple :

```bash
curl -s http://127.0.0.1:8765/status | jq .
curl -s -X POST http://127.0.0.1:8765/perceive \
  -H 'Content-Type: application/json' \
  -d '{"text":"Je m appelle Vincent. Retiens mon nom.","speak":false}'
```

## Variables d’environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `AGENT_PORT` | `8765` | port HTTP |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama local |
| `OLLAMA_MODEL` | `qwen2.5:1.5b-instruct` | fallback local |
| `OLLAMA_FALLBACK` | *(vide)* | second Ollama optionnel |
| `PUTER_MODEL` | `moonshotai/kimi-k2` | modèle Puter |
| `PUTER_AUTH_TOKEN` | — | sinon fichier `state/puter_token.txt` |
| `PUTER_BASE` | API Puter OpenAI-compatible | endpoint |
| `VOICE_LOOP` | — | `1` pour démarrer la boucle voix |

## Fichiers runtime (hors git)

```
/opt/memorysystemai/
  organism.py
  ui/index.html
  MemorySystemAI/          # bibliothèque core
  state/
    puter_token.txt        # secret
    ask_human.json
    organism.log
    snapshots/
  MemorySystemAI/memory_index.json
```

## Pont OpenClaw / Telegram

```
Humain --Telegram--> OpenClaw (skill baby-organism)
                         │
                         ├─ baby_api.py perceive|ask|answer
                         ▼
                   memory-node :8765

ask_poller.py  : si /ask pending → notifie Telegram
```

Env skill / poller : `MEMORY_NODE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

## Nursery (UI)

- Boutons : Écouter, Voir, Envoyer, Oui/Non, Kimi ON/OFF, Voix auto
- Puter.js optionnel pour consultation navigateur
- Liste des mémoires + panneau ask humain
- Destinée au **kiosk local** (Chromium plein écran), pas au contrôle distant SSH

## Limites connues du premier jet

- Inhibition surtout testée en dialogue ; pas encore hook systématique avant sudo/SSH.
- STT / vision : dépendent du matériel et des paquets installés.
- Relais Telegram `answer` : notif fiable ; exécution skill parfois à renforcer.
- Bruit de journal encore présent dans l’index (à consolider plus tard).
