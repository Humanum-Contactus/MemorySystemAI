# Modules — prototype `memory-node`

> **FR** · **[English →](en/MODULES_MEMORY_NODE.md)** · [`LANGUES.md`](LANGUES.md)

Référence des fichiers runtime sous [`prototypes/memory-node/`](../prototypes/memory-node/).

> **Règle de design :** les *normes* (ne pas harceler, corrections STT, etc.) vivent
> dans `memory_index.json` (entrées à exposant + tags). Le Python **applique**
> le crible mémoire ; il ne doit pas devenir une table de règles texte.

---

## Carte des fichiers

| Fichier | Sens | Rôle |
|---------|------|------|
| [`organism.py`](../prototypes/memory-node/organism.py) | C + I + orchestration | Runtime HTTP, boucle cognitive, outils |
| [`memory_system.py`](../memory_system.py) *(racine)* | Cœur | Entrées, exposants, `matches_tags`, reinforce |
| [`visual_memory.py`](../prototypes/memory-node/visual_memory.py) | V | Empreintes visage → identité |
| [`voice_memory.py`](../prototypes/memory-node/voice_memory.py) | O | Empreintes vocales → identité |
| [`sensor_camera.py`](../prototypes/memory-node/sensor_camera.py) | V | V4L2 brightness/gamma/exposure auto |
| [`sensor_mic.py`](../prototypes/memory-node/sensor_mic.py) | O | ALSA Capture / Mic Boost selon RMS |
| [`ui/index.html`](../prototypes/memory-node/ui/index.html) | — | Nursery kiosk |
| [`openclaw-skill/`](../prototypes/memory-node/openclaw-skill/) | — | Pont Telegram (**transitoire**, pas le cœur) |

---

## `organism.py`

Point d’entrée : `python organism.py` (service systemd en prod, `ROOT=/opt/memorysystemai`).

### Boucle `interpret_with_tools`

1. **Inhibition** — uniquement mémoires avec `inhibition_tags` qui matchent l’action  
   (`exposant >= 7` inject / `>= 9` block). Pas de chevauchement lexical aveugle.
2. **Rappel** — `recall` + `usable_memory_answer` (prioritaire sur le LLM).
3. **Consultation LLM** — outil (NVIDIA / Puter / Ollama), pas identité.
4. **Ask human** — via `request_human()` : boîte `ask_human.json` + **mémoire sociale**
   anti-harcèlement (tags `harceler`, `sans_attendre`, …).

### Mémoires enseignées (exemples de *contenu*, pas de code)

| Type | Format dans `data` | Tags typiques |
|------|-------------------|---------------|
| Anti-harcèlement tuteur | « Quand je m'adresse à un humain… » | `harceler`, `sans_attendre`, `relancer` |
| Correction STT | `Correction auditive: « … » → « … »` | `correction_auditive`, `stt`, `ouie` |

Enseignement live d’une correction :

```text
quand tu entends c'est mauve ca ça veut dire c'est moi Vincent
```

### Capteurs intégrés

- **See** : capture → `sensor_camera.auto_tune_from_frame` → vision LLM (NVIDIA défaut) + `visual_memory`.
- **Hear** : record → `sensor_mic.auto_tune_from_wav` → Whisper → corrections auditives mémoire → `voice_memory` → même boucle que `/perceive`.
- **Speak** : Piper (`fr_FR-siwis`) puis Pico / espeak.

---

## `visual_memory.py`

- Empreinte locale (grille luminance + histogramme) sur crop visage (Haar ou centre).
- Persistance : `state/visual_persons.json` (hors git).
- Teach : phrases `c'est moi <Nom>`, `je suis <Nom>`, … → `label_pending_or_last`.
- Parseur de corrections auditives : `parse_auditory_correction()` lit le **texte des mémoires**.

Limite nursery : pas FaceNet — suffisant pour lier des captures successives.

---

## `voice_memory.py`

- Empreinte spectrale (bandes log + pitch/énergie) sur WAV 16 kHz mono.
- Persistance : `state/voice_persons.json`.
- Même teach d’identité que le visage (souvent lié ensemble).

---

## `sensor_camera.py` / `sensor_mic.py`

Même idée : **mesurer** (luminance frame / RMS-peak WAV) → **proposer** des contrôles
matériels → éventuellement re-capturer. L’expérience (« j’ai baissé le gain »)
peut être écrite en mémoire (fondamental V ou O).

| Capteur | Contrôles | Trop bas | Trop haut |
|---------|-----------|----------|-----------|
| Caméra | brightness, gamma, exposure… | ouvrir | fermer |
| Micro | `Capture`, `Internal Mic Boost` | monter | baisser (saturation) |

Note : le volume UI `Master` = **haut-parleur**, pas le micro. Micro = `/mic`.

---

## Secrets (jamais dans git)

| Fichier runtime | Contenu |
|-----------------|--------|
| `state/puter_token.txt` | token Puter |
| `state/nvidia_token.txt` | clé NVIDIA NIM |
| `state/ask_human.json` | boîte aux lettres ask (canal, pas la norme) |
| `state/visual_persons.json` / `voice_persons.json` | empreintes |
| `MemorySystemAI/memory_index.json` | mémoires vivantes du nœud |

Variables : `PUTER_AUTH_TOKEN`, `NVIDIA_API_KEY`, `VISION_PROVIDER`, `WHISPER_MODEL`, …

---

## Ce qui reste fragile (honnête)

Voir aussi la chronique d’évolution. Priorités concept :

1. Détection Fundamental / State (pas heuristique mots-clés).
2. Similarité sémantique (pas seul chevauchement de mots).
3. Corroboration multi-sens réelle.
4. Moins de dépendance OpenClaw / canal ask type chat.
5. Mode plus actif (l’organisme n’attend pas seulement qu’on lui parle).
