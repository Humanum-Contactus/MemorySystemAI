# Installation et tests — prototype `memory-node`

> **FR (source)** · **[English →](en/INSTALLATION.md)** · [`LANGUES.md`](LANGUES.md)  
> Guide pour installer, lancer et tester un nœud Sensors&MemorySystemAI.  
> Aucun secret n’est nécessaire pour les tests ; les jetons d’API ne sont jamais versionnés.  
> Présentation du prototype : [`prototypes/memory-node/README.md`](../prototypes/memory-node/README.md) ·
> Tests : [`tests/`](../prototypes/memory-node/tests/README.md) · [Index docs](README.md)

## 1. Prérequis

| Élément | Requis ? | Usage |
|---------|----------|-------|
| Linux (Ubuntu Server 24.04 utilisé pour le prototype) | oui | nœud |
| Python 3 (testé avec 3.13) + `venv` | oui | runtime |
| `patch`, `curl` | conseillé | tests / API |
| ALSA (`arecord`, `amixer`) | optionnel | micro, `/hear` |
| V4L2 (`v4l2-ctl`), `ffmpeg` | optionnel | caméra, `/see` |
| Piper TTS (dossier `tts/`) | optionnel | `/speak` |
| Ollama + petit modèle | optionnel | consultation LLM locale |
| Jeton NVIDIA NIM / Puter | optionnel | LLM / vision distants |

## 2. Dépendances Python (issues des imports réels)

- **Cœur** — `memory_system.py`, `organism.py`, `fact_conflict.py`,
  `dedup_taught_facts.py`, `autonomy.py` : **bibliothèque standard uniquement**.
- **Optionnelles** — importées à la demande, le nœud démarre sans elles :
  voir [`prototypes/memory-node/requirements-optional.txt`](../prototypes/memory-node/requirements-optional.txt)
  (`numpy`, `opencv-python-headless`, `Pillow`, `faster-whisper`).
- **Tests** — `pytest` (facultatif) : [`requirements-dev.txt`](../prototypes/memory-node/requirements-dev.txt).

## 3. Tester sans installer (2 minutes)

```bash
git clone https://github.com/Humanum-Contactus/MemorySystemAI.git
cd MemorySystemAI
python3 prototypes/memory-node/tests/test_contradictions.py
python3 prototypes/memory-node/tests/test_autonomie.py
python3 prototypes/memory-node/tests/test_voix.py
# attendu pour chacun : RÉUSSI — 0 contrôle(s) en échec

# avec pytest :
python3 -m venv .venv && . .venv/bin/activate
pip install -r prototypes/memory-node/requirements-dev.txt
python -m pytest prototypes/memory-node/tests
# attendu : 3 passed
```

Les tests travaillent dans un dossier temporaire : aucun service, aucun index réel,
aucun appel réseau (le LLM est simulé).

## 4. Installer un nœud

`organism.py` attend la disposition suivante (chemin `ROOT` codé en dur :
`/opt/memorysystemai`) :

```
/opt/memorysystemai/
├── organism.py  autonomy.py  fact_conflict.py  dedup_taught_facts.py
├── visual_memory.py  voice_memory.py  sensor_camera.py  sensor_mic.py
├── ui/index.html
├── MemorySystemAI/            ← paquet = racine du dépôt
│   ├── __init__.py
│   ├── memory_system.py
│   └── memory_index.json      ← créé au premier démarrage (ardoise)
├── state/                     ← état local, jetons (mode 600), jamais versionné
├── backups/
└── .venv/
```

```bash
sudo useradd --system --create-home --groups audio,video <UTILISATEUR_SERVICE>
sudo mkdir -p /opt/memorysystemai/{MemorySystemAI,state,backups}
sudo cp __init__.py memory_system.py /opt/memorysystemai/MemorySystemAI/
sudo cp prototypes/memory-node/*.py /opt/memorysystemai/
sudo cp -r prototypes/memory-node/ui /opt/memorysystemai/
sudo python3 -m venv /opt/memorysystemai/.venv
# optionnel :
sudo /opt/memorysystemai/.venv/bin/pip install -r prototypes/memory-node/requirements-optional.txt
sudo chown -R <UTILISATEUR_SERVICE>: /opt/memorysystemai
sudo chmod 700 /opt/memorysystemai/state
```

> Ne copiez **pas** le `memory_index.json` de la racine du dépôt si vous voulez
> une ardoise vierge : le nœud crée son propre index au premier démarrage.

## 5. Configuration

```bash
sudo mkdir -p /etc/memory-node
sudo cp prototypes/memory-node/config.example.env /etc/memory-node/memory-node.env
sudo chmod 600 /etc/memory-node/memory-node.env
sudoedit /etc/memory-node/memory-node.env
```

Variables lues par le code : `AGENT_PORT`, `OLLAMA_HOST`, `OLLAMA_MODEL`,
`OLLAMA_FALLBACK`, `NVIDIA_API_KEY`, `NVIDIA_TEXT_MODEL`, `PUTER_AUTH_TOKEN`,
`PUTER_MODEL`, `PUTER_VISION_MODEL`, `VISION_PROVIDER`, `VISION_FALLBACK_PUTER`,
`WHISPER_MODEL`, `VOICE_LOOP`, `AUTONOMY_LOOP`, `AUTONOMY_INTERVAL` ; pour le pont :
`MEMORY_NODE_URL`, `ASK_POLLER_INTERVAL`, `ASK_POLLER_STATE`, `TELEGRAM_BOT_TOKEN`,
`TELEGRAM_CHAT_ID`, `OPENCLAW_CONFIG`.

Jetons : `state/nvidia_token.txt`, `state/puter_token.txt` (mode 600) — exclus par `.gitignore`.

> Définissez toujours `OLLAMA_FALLBACK` : sa valeur par défaut dans le code pointe
> vers une adresse du réseau local du prototype.

## 6. Lancement

Manuel :

```bash
cd /opt/memorysystemai
set -a; . /etc/memory-node/memory-node.env; set +a
.venv/bin/python organism.py
curl -s http://127.0.0.1:8765/status
```

Service systemd (exemple générique :
[`systemd/memory-node.service.generic.example`](../prototypes/memory-node/systemd/memory-node.service.generic.example)) :

```bash
sudo cp prototypes/memory-node/systemd/memory-node.service.generic.example \
        /etc/systemd/system/memory-node.service
sudoedit /etc/systemd/system/memory-node.service    # <UTILISATEUR_SERVICE>
sudo systemctl daemon-reload
sudo systemctl enable --now memory-node
journalctl -u memory-node -f
```

Sécurité réseau : l’API n’a pas d’authentification. Limitez le port (ex. `ufw allow
from <IP_POSTE_DE_CONTROLE> to any port 8765`) et n’exposez jamais le nœud à Internet.

## 7. Tests sur un nœud réel

1. Sauvegarde : `tar czf backups/<nom>_$(date +%Y%m%dT%H%M%S).tgz MemorySystemAI/memory_index.json state/`
2. Test de fumée : `curl -s http://127.0.0.1:8765/status`
3. Protocole contradictions : [`PROTOCOLE_TEST_CONTRADICTIONS.md`](PROTOCOLE_TEST_CONTRADICTIONS.md)
4. Fusion des doublons (copie d’abord) : voir la
   [fiche de changement](changements/2026-10-25_detection-contradictions.md).
5. Tests automatisés : [`prototypes/memory-node/tests/`](../prototypes/memory-node/tests/README.md).

## 8. Mise à jour et retour arrière

Toujours : arrêter le service → sauvegarder → copier les fichiers → redémarrer →
vérifier `/status` et `journalctl`. Chaque fiche de `docs/changements/` donne sa
procédure de retour arrière.

---

Voir aussi : [README du prototype](../prototypes/memory-node/README.md) ·
[protocole contradictions](PROTOCOLE_TEST_CONTRADICTIONS.md) ·
[fiches de changement](changements/README.md) · [CHANGELOG](../CHANGELOG.md)
