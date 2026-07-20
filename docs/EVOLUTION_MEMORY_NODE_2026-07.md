# Évolution juillet 2026 — prototype `memory-node`

**Auteur concept :** Vincent Vermeille (Humanum-Contactus)  
**Implémentation prototype :** session agent Cursor (DeskTopRel1 → nœud laptop)  
**Statut :** premier jet démonstratif du concept (Sensors&MemorySystemAI)

Ce document trace le **processus de mise en place** qui a mené au prototype
incarné : un portable Ubuntu quasi vide qui perçoit, consulte des LLM comme
outils, apprend par exposants, et peut demander de l’aide via Telegram.

---

## 1. Intention (rappel du concept)

Problème : les LLM n’ont pas de système nerveux. Les interdits texte
n’inhibent pas vraiment.

Objectif MemorySystemAI / **Sensors&MemorySystemAI** :

1. **Capteurs** — entrée monde (V/O/… + outils see/hear/speak)
2. **Mémoire sensorielle-émotionnelle** — fondamentaux + exposants + P/N/X
3. **Boucle** — réception → évaluation → enregistrement → renforcement → injection
4. **LLM** — outil d’interprétation, pas identité / pas loi
5. **Humain** — tuteur quand la mémoire est insuffisante

Le prototype n’est donc **pas** un chatbot local : c’est un **organisme mémoire**
qui commence presque vide.

---

## 2. Chronologie du chantier (haut niveau)

### Phase A — Machine cible

- Portable Acer (ex-dual boot Win/macOS OpenCore) repris comme nœud dédié.
- Installation **Ubuntu Server 24.04** via PXE/HTTP depuis un PC Windows du LAN
  (autoinstall, puis réparation chroot quand le postinstall réseau a échoué).
- Hostname : `memory-node`.
- Disque Ubuntu sur un SSD ; conserver la prudence sur les EFI (leçons empiriques
  du whitepaper : incidents `newfs` / `rm` EFI).

### Phase B — Stack runtime

- Code MemorySystemAI (bibliothèque Python) déployé sous `/opt/memorysystemai/`.
- Ollama local + modèle léger CPU (ex. `qwen2.5:1.5b-instruct`) comme **fallback**.
- Caméra `/dev/video*`, audio ALC255 (groupes `audio`/`video`).
- Premier agent type “chatbot” → **rejeté** : contraire au concept.

### Phase C — Organisme (`organism.py`)

Réécriture alignée concept :

- bootstrap = **méta uniquement** (presque vide sur le monde)
- outils : `see`, `hear`, `speak`, `consult_llm`, `ask_human`
- inhibition via **mémoires à exposant élevé**, pas RISK_PATTERNS texte
- API HTTP `:8765`
- rappel mémoire **prioritaire** avant reconsultation LLM (après correctifs
  d’apprentissage SatRadio / enseignement humain)

### Phase D — Nursery graphique locale

- Ubuntu Server n’avait pas de bureau → stack légère :
  Xorg + Openbox + LightDM + Chromium **kiosk**
- UI `ui/index.html` servie par l’organisme (`GET /`)
- Interaction **sur le portable**, sans SSH pour l’usage quotidien

### Phase E — Consultation Kimi via Puter

- Intégration Puter OpenAI-compatible + Puter.js nursery
- Modèle de départ : Kimi K3 puis retour **Kimi K2** (suffisant pour l’élevage)
- Token Puter en fichier local (`state/puter_token.txt`), jamais dans git

### Phase F — Pont OpenClaw / Telegram

- Skill `baby-organism` : `perceive` / `ask` / `answer`
- Poller : notifie Telegram quand `/ask` est `pending`
- Flux observé : bébé demande → notif → humain répond sur Telegram →
  réponse intégrée en mémoire (exposant fort)

### Phase G — Démo texte live

Séquence : identité → nomination (Vincent) → rappel du nom → enseignement
SatRadioElectronsLibres (WiFi local via Starlink) → re-question répondue
**depuis la mémoire** (`source: memory`), sans repasser par Kimi.

---

## 3. Architecture résultante

```
[Nursery kiosk sur laptop]          [Telegram / humain]
         │                                    │
         ▼                                    ▼
   organism.py :8765  ◄──────────  OpenClaw (skill + poller)
         │
         ├─ MemorySystem (fondamentaux / exposants)
         ├─ outils see / hear / speak
         └─ consult LLM : Puter/Kimi → Ollama fallback
```

Code publié sous : `prototypes/memory-node/`.

---

## 4. Leçons apprises (prototype)

1. **Ne pas commencer par un chatbot** — on fausse immédiatement le concept.
2. **Enregistrer ≠ rappeler** — sans priorisation mémoire, le LLM ré-interprète
   à chaque fois et masque l’apprentissage.
3. **Enseignement humain** (`X est Y`) doit monter l’exposant (≈8) pour injecter.
4. **Ask Telegram** : la notif marche ; le relais `answer` OpenClaw doit être
   robuste (sinon intégrer manuellement / renforcer la skill).
5. **Secrets** : tokens Puter/Telegram hors dépôt.
6. **Nom** : `Sensors&MemorySystemAI` décrit mieux capteurs + mémoire que
   MemorySystemAI seul (proposition — voir doc dédiée).

---

## 5. Suite logique (hors premier jet)

- Inhibition **avant action machine** réelle (SSH/sudo), pas seulement dialogue
- Multi-nœuds + divergence d’exposants (feuille de route phase 3)
- Dégradation temporelle / consolidation
- Vision LLM réelle (image → description) au lieu du raw frame seul
- Relais Telegram `answer` 100 % automatique
- Nettoyage du bruit de journal (`Message reçu:`) vs faits enseignés

---

## 6. Fichiers de référence dans ce dépôt

- Concept : `01_CONCEPT_FONDAMENTAL.txt`
- Feuille de route : `04_FEUILLE_DE_ROUTE.txt`
- Core Python : `memory_system.py`
- Prototype incarné : `prototypes/memory-node/`
- Proposition de nommage : `docs/SENSORS_AND_MEMORY_SYSTEM_AI.md`
