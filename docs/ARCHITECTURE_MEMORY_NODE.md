# Architecture — prototype `memory-node`

## Vue d’ensemble

```
                    ┌─────────────────────────────────────┐
                    │         HUMAIN (tuteur)             │
                    │  nursery locale  ·  (Telegram pont) │
                    └──────────────┬──────────────────────┘
                                   │ perceive / answer / feedback
                                   ▼
┌──────────────────────────────────────────────────────────────┐
│  organism.py  (HTTP :8765)                                   │
│                                                              │
│  1. Réception      texte | hear | see                        │
│  2. Capteurs       camera auto-tune · mic auto-gain          │
│  3. Identité       visual_memory · voice_memory              │
│  4. Correction O   mémoires « Correction auditive »          │
│  5. Inhibition     tags + exposant (pas chevauchement aveugle)│
│  6. Rappel         MemorySystem.recall (prioritaire)         │
│  7. Consultation   NVIDIA / Puter / Ollama  (outil)          │
│  8. Ask human      request_human + mémoire anti-harcèlement  │
│  9. Enregistrement fondamentaux + exposant + source          │
│ 10. Expression     utterance (+ speak / Piper)               │
└──────────────┬───────────────────────────┬───────────────────┘
               │                           │
               ▼                           ▼
     memory_index.json              outils OS
     (MemorySystemAI core)          caméra / micro / TTS
```

Référence modules : [`MODULES_MEMORY_NODE.md`](MODULES_MEMORY_NODE.md).

## Séparation des rôles

| Composant | Rôle | N’est pas |
|-----------|------|-----------|
| `MemorySystem` | stocker, scorer, inhiber | un LLM |
| `organism.py` | boucle sensorielle + API | un chatbot persona |
| Mémoires à tags | normes apprises (harcèlement, STT…) | des `if` hardcodés dans le `.py` |
| NVIDIA / Puter / Ollama | interpréter une perception | l’identité du bébé |
| OpenClaw / Telegram | relais humain distant (**pont**) | le système de mémoire |
| `ask_human.json` | boîte aux lettres | la règle « ne pas spammer » |
| Nursery UI | présence locale | un dashboard générique |

## Boucle décisionnelle

```
perception
  │
  ├─ (hear) repair via mémoires Correction auditive
  │
  ├─ inhibition mémoire (tags + exposant ≥ 9) ──► abstention
  │     utterance = « je m'abstiens de X » + mémoire N°…
  │
  ├─ usable_memory_answer ? ──oui──► source: memory  (pas de LLM)
  │
  ├─ tool_consult_llm (NVIDIA texte / Puter / Ollama)
  │     ├─ OK ──► apprendre interprétation (I) + perçu
  │     └─ JE NE SAIS PAS / fail
  │              └─ request_human
  │                    ├─ pending déjà là + mémoire anti-harcèlement → wait
  │                    └─ sinon ask pending (canal)
  ▼
utterance
```

### Inhibition : piège évité

**Ne pas** matcher toutes les mémoires e≥9 par chevauchement de mots  
(sinon « Vincent » bloquait l’enseignement « c'est moi Vincent »).

**Oui** : `inhibition_tags` présents **et** `matches_tags(action)`.

### Ask human : piège chatbot

Le poller Telegram est un **pont**. La norme « ne pas harceler si pas de réponse »
est une **mémoire** (ex. C/N/e9, tags `harceler|sans_attendre|…`).  
`request_human()` consulte cette mémoire quand une ask est déjà pending.

## API HTTP

Base : `http://HOST:8765`

### GET

| Route | Description |
|-------|-------------|
| `/` ou `/ui/` | Nursery HTML |
| `/status` | rôle, mémoires, vision, mic, camera, ask, faces/voices résumés |
| `/memories` | liste des entrées index |
| `/faces` `/visual` | personnes / pending visage |
| `/voices` `/speakers` | personnes / pending voix |
| `/ask` | boîte ask (`none` / `pending` / `answered` / `consumed`) |
| `/volume` | Master playback (HP) |
| `/camera` | contrôles V4L2 |
| `/mic` | Capture / Mic Boost |
| `/vision` | provider nvidia\|puter |
| `/snapshot/<file>` | JPEG capturé |

### POST (JSON)

| Route | Body typique | Effet |
|-------|--------------|-------|
| `/perceive` | `{ "text", "speak?" }` | cycle texte (+ teach identité / corrections) |
| `/capture` | `{ "auto_tune?" }` | photo seule (+ auto caméra) |
| `/see` | `{ "speak?", "path?" }` | vision + identité visuelle |
| `/hear` | `{ "seconds?", "speak?", "auto_tune?" }` | micro + STT + cycle |
| `/speak` | `{ "text" }` | TTS |
| `/volume` | `{ "percent?"\|"delta?"\|"mute?" }` | HP |
| `/camera` | `{ "auto":true }` ou contrôles | V4L2 |
| `/mic` | `{ "auto":true }` ou `{ "capture":N }` | gain entrée |
| `/vision` | `{ "provider":"nvidia\|puter" }` | switch vision |
| `/voice` | `{ "enabled": true\|false }` | boucle écoute |
| `/ask/answer` | `{ "answer" }` | intègre réponse (exposant 8) |
| `/reset` | `{ "confirm":"RESET_ORGANISM" }` | ardoise → bootstrap méta |

```bash
curl -s http://127.0.0.1:8765/status | jq .
curl -s -X POST http://127.0.0.1:8765/perceive \
  -H 'Content-Type: application/json' \
  -d '{"text":"c est moi Vincent","speak":false}'
curl -s -X POST http://127.0.0.1:8765/mic \
  -H 'Content-Type: application/json' \
  -d '{"auto":true,"seconds":2}'
```

## Variables d’environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `AGENT_PORT` | `8765` | port HTTP |
| `VISION_PROVIDER` | `nvidia` | `nvidia` \| `puter` |
| `NVIDIA_API_KEY` | — | sinon `state/nvidia_token.txt` |
| `NVIDIA_VISION_MODEL` | `google/gemma-4-31b-it` | vision NIM |
| `PUTER_AUTH_TOKEN` | — | sinon `state/puter_token.txt` |
| `PUTER_MODEL` / `PUTER_VISION_MODEL` | kimi-* | Puter |
| `OLLAMA_HOST` / `OLLAMA_MODEL` | local qwen | fallback |
| `WHISPER_MODEL` | `base` | STT |
| `VISION_FALLBACK_PUTER` | `0` | pas de fallback auto |

## Apprentissage (exposants typiques)

| Événement | Fond. | État | Exp. |
|-----------|-------|------|------|
| Journal / perçu | C/O/V/I | X | ~5 |
| Fait enseigné / réponse humaine | C | P | ~8 |
| Identité visage / voix | V/O | P | ~8 |
| Correction auditive enseignée | O | P | ~8 |
| Anti-harcèlement social | C | N | ~9 |
| Feedback + / − | C | P/N | +2 / +3 |

## Fichiers d’état (hors git)

```
state/
  puter_token.txt
  nvidia_token.txt
  ask_human.json          # canal
  visual_persons.json
  voice_persons.json
  snapshots/
  o_*.wav
MemorySystemAI/memory_index.json
```
