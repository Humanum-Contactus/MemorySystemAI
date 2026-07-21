# Évolution juillet 2026 — prototype `memory-node`

> **FR (source)** · **[English →](en/EVOLUTION_MEMORY_NODE_2026-07.md)** · [`LANGUES.md`](LANGUES.md)

**Auteur concept :** Vincent Vermeille (Humanum-Contactus)  
**Implémentation prototype :** session agent Cursor (PC de contrôle LAN → laptop nœud)  
**Statut :** premier jet démonstratif incarné — Sensors&MemorySystemAI en puissance  
**Code :** [`prototypes/memory-node/`](../prototypes/memory-node/)

Ce document est la **chronique de mise en place** : comment on est passé du concept /
de la bibliothèque Python à un portable qui perçoit, apprend, et demande de l’aide.

Documents liés :

- [`POURQUOI_CA_COMPTE.md`](POURQUOI_CA_COMPTE.md) — sens & finalité  
- [`ARCHITECTURE_MEMORY_NODE.md`](ARCHITECTURE_MEMORY_NODE.md) — API & flux  
- [`SENSORS_AND_MEMORY_SYSTEM_AI.md`](SENSORS_AND_MEMORY_SYSTEM_AI.md) — nommage  

---

## 0. Résumé en une phrase

On a incarné MemorySystemAI comme un **bébé organisme** : ardoise quasi vide,
capteurs + mémoire à exposants, LLM uniquement comme outil, humain comme tuteur —
démonstration live (mémoire SatRadio sans repasser par Kimi ; ask via Telegram).

---

## 1. Intention (rappel du concept)

**Problème.** Les LLM génèrent. Ils n’ont pas de système nerveux.  
Les interdits texte n’inhibent pas vraiment (incidents EFI du whitepaper).

**Objectif.** Sensors&MemorySystemAI :

1. **Capteurs** — V/O/T/G/Od/I/C + outils see/hear/speak  
2. **Mémoire sensorielle-émotionnelle** — exposants + P/N/X  
3. **Boucle** — réception → évaluation → enregistrement → renforcement → injection  
4. **LLM** — outil d’interprétation, pas identité / pas loi  
5. **Humain** — tuteur quand la mémoire est insuffisante  

Le prototype n’est **pas** un chatbot local.

---

## 2. Chronologie du chantier

### Phase A — Machine cible

- Laptop Acer repris comme nœud dédié (sortie du rôle Hackintosh pour ce use-case).
- Install **Ubuntu Server 24.04** via PXE/HTTP depuis un PC Windows du LAN
  (tftpd, autoinstall cloud-init, ISO servie en HTTP).
- Coupure : postinstall apt sans route → finition en **chroot** `/target`
  (user, paquets, hostname `memory-node`).
- Attention EFI / multi-disques : alignée sur les leçons empiriques du concept
  (ne jamais confondre partitions boot).

### Phase B — Stack runtime

- Bibliothèque `MemorySystemAI` sous `/opt/memorysystemai/`.
- Ollama + modèle CPU léger = **fallback** de consultation.
- Caméra V4L2, audio (groupes `audio` / `video`).
- Premier jet « agent chatbot + règles texte » → **écarté** (contredit le concept).

### Phase C — Organisme (`organism.py`)

Réécriture :

| Principe | Implémentation |
|----------|----------------|
| Ardoise vide | bootstrap = 6 entrées **méta** seulement |
| Outils | see, hear, speak, consult_llm, ask_human |
| Pas d’interdits texte | inhibition = mémoires exposant élevé |
| API | HTTP `:8765` |
| Apprendre vraiment | rappel mémoire **avant** LLM (correctifs v1) |

### Phase D — Nursery graphique locale

- Pas de desktop Server → Xorg + Openbox + LightDM + Chromium **kiosk**.
- UI `ui/index.html` servie par l’organisme (`GET /`).
- Usage quotidien **sur l’écran du portable**, pas via SSH.

### Phase E — Kimi / Puter

- API Puter OpenAI-compatible + Puter.js dans la nursery.
- Essai Kimi K3 puis choix **Kimi K2** pour l’élevage de départ.
- Token dans `state/puter_token.txt` (hors git).

### Phase F — OpenClaw + Telegram

- Skill `baby-organism` (`perceive` / `ask` / `answer`).
- Poller : `/ask` pending → notification Telegram.
- Flux réel observé : demande bébé → notif → réponse humaine → mémoire.

### Phase G — Démo & preuve d’apprentissage

1. « Qui es-tu ? » → consultation outil LLM.  
2. « Je m’appelle Vincent… » → mémorisation.  
3. « Comment je m’appelle ? » → rappel.  
4. Enseignement **SatRadioElectronsLibres** = WiFi local via Starlink.  
5. Re-question → **`source: memory`** (sans Kimi).  
6. Ask Telegram + réponse intégrée (exposant 8).

### Phase H — Capteurs & identité (suite juillet 2026)

| Brique | Contenu |
|--------|---------|
| Vision réelle | JPEG `/see` → NVIDIA NIM (défaut) ou Puter ; switch UI/API |
| Visages | `visual_memory.py` — empreintes locales, teach « c'est moi Vincent » |
| Voix | `voice_memory.py` — empreintes spectrales, même teach |
| Caméra auto | `sensor_camera.py` — luminosité → brightness/gamma/exposure |
| Micro auto | `sensor_mic.py` — RMS/peak → Capture / Mic Boost (souvent *saturation*, pas trop faible) |
| TTS | Piper `fr_FR-siwis-medium` préféré |
| Clavier kiosk | disposition CH_FR |

### Phase I — Mémoires = normes (pas tables `.py`)

Corrections d’architecture alignées sur le concept :

1. **Anti-harcèlement ask** — mémoire C/N/e9 (tags `harceler`, `sans_attendre`, …).  
   `request_human()` ne spam pas une ask pending ; utterance = texte de la mémoire.  
   Suppression des rate-limits fichier / listes de phrases dans le code.

2. **Corrections STT** — mémoires O  
   `Correction auditive: « c'est mauve ca » → « c'est moi Vincent »`.  
   Le runtime lit/applique/renforce ; enseignement possible en langage naturel.

3. **Inhibition** — uniquement via **tags** + exposant.  
   Bug corrigé : les mémoires e9 « Visage reconnu: Vincent » ne doivent plus  
   bloquer la phrase « c'est moi Vincent » (faux « Je m'abstiens »).

4. **Pont OpenClaw** — assumé comme *relais*, pas comme cœur.  
   Risque conscient : retomber en logique chatbot si on grossit ce canal.

---

## 3. Architecture résultante

```
[Nursery kiosk laptop]              [Telegram / humain — pont]
         │                                    │
         ▼                                    ▼
   organism.py :8765  ◄──────────  OpenClaw (skill + poller)
         │
         ├─ MemorySystem (fondamentaux / exposants / tags)
         ├─ visual_memory + voice_memory
         ├─ sensor_camera + sensor_mic
         ├─ outils see / hear / speak (Piper)
         └─ consult LLM : NVIDIA → Puter → Ollama
```

Détail API / modules :
[`ARCHITECTURE_MEMORY_NODE.md`](ARCHITECTURE_MEMORY_NODE.md) ·
[`MODULES_MEMORY_NODE.md`](MODULES_MEMORY_NODE.md).

---

## 4. Décisions de conception (traces)

| Tentation | Décision |
|-----------|----------|
| Chatbot + system prompt d’interdits | Rejeté |
| Remplir la mémoire au boot | Rejeté (ardoise) |
| LLM = personnalité du nœud | Rejeté (outil seulement) |
| Toujours appeler Kimi | Rejeté après correctif recall |
| Contrôle seulement en SSH | Rejeté → nursery locale |
| Kimi K3 dès le départ | Downgrade volontaire à K2 pour l’élevage |
| Rate-limit ask dans un `.json` / `.py` | Rejeté → mémoire sociale |
| Table regex STT « mauve→Vincent » dans le code | Rejeté → mémoires Correction auditive |
| Inhibition = tous les e9 qui partagent des mots | Rejeté → tags seulement |

---

## 5. Leçons apprises

1. Commencer par un chatbot **tue** le concept immédiatement.  
2. Enregistrer ≠ rappeler — sans priorité mémoire, le LLM masque l’apprentissage.  
3. L’enseignement humain (`X est Y`) doit monter l’exposant (~8).  
4. Ask Telegram : utile comme pont ; grossir ce canal = risque chatbot.  
5. Secrets hors dépôt.  
6. Le nom **Sensors&MemorySystemAI** colle mieux à la finalité.  
7. **Norme apprise = entrée mémoire**, mécanisme = code qui lit les tags.  
8. Capteur trop fort (micro saturé) gêne autant que trop faible.  
9. Le danger n’est plus « ne pas avancer », c’est avancer **hors concept**.

---

## 6. Suite (priorités concept)

Aligné sur le diagnostic interne du chantier :

| Point | État | Priorité |
|-------|------|----------|
| Fundamental & State | heuristique fragile | Haute |
| Similarité sémantique | chevauchement de mots | Haute |
| Corroboration multi-sens | partielle (visage+voix teach) | Haute |
| Moins de dépendance LLM / OpenClaw | encore forte | Haute |
| Apprentissage plus « enfantin » | basique | Moyenne |
| Mode plus actif | encore passif | Moyenne |
| Inhibition actions machines (SSH/sudo) | pas câblée | Moyenne |

---

## 7. Carte des fichiers

| Chemin | Rôle |
|--------|------|
| `prototypes/memory-node/organism.py` | Runtime organisme |
| `prototypes/memory-node/visual_memory.py` | Identité V |
| `prototypes/memory-node/voice_memory.py` | Identité O |
| `prototypes/memory-node/sensor_camera.py` | Auto caméra |
| `prototypes/memory-node/sensor_mic.py` | Auto micro |
| `prototypes/memory-node/ui/` | Nursery |
| `prototypes/memory-node/openclaw-skill/` | Pont agent/Telegram |
| `prototypes/memory-node/systemd/` | Exemple service |
| `memory_system.py` | Cœur MemorySystemAI |
| `docs/MODULES_MEMORY_NODE.md` | Référence modules |
| `docs/*` | Documentation évolution |

---

## 8. Remerciements / provenance

Concept et finalité : **Vincent Vermeille** (Humanum-Contactus).  
Incarnation prototype juillet 2026 : collaboration humaine + agent Cursor sur le LAN,
en restant fidèle à l’idée d’origine (pas un gadget chatbot).
