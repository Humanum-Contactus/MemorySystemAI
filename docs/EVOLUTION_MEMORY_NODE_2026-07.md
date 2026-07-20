# Évolution juillet 2026 — prototype `memory-node`

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

---

## 3. Architecture résultante

```
[Nursery kiosk laptop]              [Telegram / humain]
         │                                    │
         ▼                                    ▼
   organism.py :8765  ◄──────────  OpenClaw (skill + poller)
         │
         ├─ MemorySystem (fondamentaux / exposants)
         ├─ outils see / hear / speak
         └─ consult LLM : Puter/Kimi → Ollama
```

Détail API / env : [`ARCHITECTURE_MEMORY_NODE.md`](ARCHITECTURE_MEMORY_NODE.md).

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

---

## 5. Leçons apprises

1. Commencer par un chatbot **tue** le concept immédiatement.  
2. Enregistrer ≠ rappeler — sans priorité mémoire, le LLM masque l’apprentissage.  
3. L’enseignement humain (`X est Y`) doit monter l’exposant (~8).  
4. Ask Telegram : notif OK ; skill `answer` à solidifier.  
5. Secrets hors dépôt.  
6. Le nom **Sensors&MemorySystemAI** colle mieux à la finalité.

---

## 6. Suite (hors premier jet)

- [ ] Inhibition avant **actions machines** (SSH/sudo/disk)  
- [ ] Multi-nœuds + divergence d’exposants  
- [ ] Dégradation temporelle / consolidation  
- [ ] Vision LLM réelle  
- [ ] Relais Telegram `answer` 100 % automatique  
- [ ] Réduire le bruit de journal dans l’index  

---

## 7. Carte des fichiers

| Chemin | Rôle |
|--------|------|
| `prototypes/memory-node/organism.py` | Runtime organisme |
| `prototypes/memory-node/ui/` | Nursery |
| `prototypes/memory-node/openclaw-skill/` | Pont agent/Telegram |
| `prototypes/memory-node/systemd/` | Exemple service |
| `memory_system.py` | Cœur MemorySystemAI |
| `01_CONCEPT_FONDAMENTAL.txt` | Concept |
| `04_FEUILLE_DE_ROUTE.txt` | Roadmap historique |
| `docs/*` | Documentation évolution |

---

## 8. Remerciements / provenance

Concept et finalité : **Vincent Vermeille**.  
Incarnation prototype juillet 2026 : collaboration humaine + agent Cursor sur le LAN,
en restant fidèle à l’idée d’origine (pas un gadget chatbot).
