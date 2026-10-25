# Installation and tests — `memory-node` prototype

> **[FR (source) →](../INSTALLATION.md)** · EN · [`LANGUES.md`](../LANGUES.md)  
> Guide to install, run and test a Sensors&MemorySystemAI node. French is authoritative.  
> No secret is needed for the tests; API tokens are never committed.  
> Prototype overview: [`prototypes/memory-node/README.en.md`](../../prototypes/memory-node/README.en.md) ·
> Tests: [`tests/`](../../prototypes/memory-node/tests/README.en.md) · [Docs index](README.md)

## 1. Requirements

| Item | Required? | Use |
|------|-----------|-----|
| Linux (Ubuntu Server 24.04 used for the prototype) | yes | node |
| Python 3 (tested with 3.13) + `venv` | yes | runtime |
| `patch`, `curl` | recommended | tests / API |
| ALSA (`arecord`, `amixer`) | optional | microphone, `/hear` |
| V4L2 (`v4l2-ctl`), `ffmpeg` | optional | camera, `/see` |
| Piper TTS (`tts/` folder) | optional | `/speak` |
| Ollama + small model | optional | local LLM consultation |
| NVIDIA NIM / Puter token | optional | remote LLM / vision |

## 2. Python dependencies (taken from the real imports)

- **Core** — `memory_system.py`, `organism.py`, `fact_conflict.py`,
  `dedup_taught_facts.py`, `autonomy.py`: **standard library only**.
- **Optional** — imported on demand, the node starts without them:
  see [`requirements-optional.txt`](../../prototypes/memory-node/requirements-optional.txt)
  (`numpy`, `opencv-python-headless`, `Pillow`, `faster-whisper`).
- **Tests** — `pytest` (optional): [`requirements-dev.txt`](../../prototypes/memory-node/requirements-dev.txt).

## 3. Test without installing (2 minutes)

```bash
git clone https://github.com/Humanum-Contactus/MemorySystemAI.git
cd MemorySystemAI
python3 prototypes/memory-node/tests/test_contradictions.py
python3 prototypes/memory-node/tests/test_autonomie.py
python3 prototypes/memory-node/tests/test_voix.py
# expected for each: RÉUSSI — 0 contrôle(s) en échec

# with pytest:
python3 -m venv .venv && . .venv/bin/activate
pip install -r prototypes/memory-node/requirements-dev.txt
python -m pytest prototypes/memory-node/tests
# expected: 3 passed
```

Tests run in a temporary folder: no service, no real index, no network call (the LLM is mocked).

## 4. Installing a node

`organism.py` expects this layout (`ROOT` path hard-coded: `/opt/memorysystemai`):

```
/opt/memorysystemai/
├── organism.py  autonomy.py  fact_conflict.py  dedup_taught_facts.py
├── visual_memory.py  voice_memory.py  sensor_camera.py  sensor_mic.py
├── ui/index.html
├── MemorySystemAI/            ← package = repository root
│   ├── __init__.py
│   ├── memory_system.py
│   └── memory_index.json      ← created on first start (blank slate)
├── state/                     ← local state, tokens (mode 600), never committed
├── backups/
└── .venv/
```

```bash
sudo useradd --system --create-home --groups audio,video <SERVICE_USER>
sudo mkdir -p /opt/memorysystemai/{MemorySystemAI,state,backups}
sudo cp __init__.py memory_system.py /opt/memorysystemai/MemorySystemAI/
sudo cp prototypes/memory-node/*.py /opt/memorysystemai/
sudo cp -r prototypes/memory-node/ui /opt/memorysystemai/
sudo python3 -m venv /opt/memorysystemai/.venv
# optional:
sudo /opt/memorysystemai/.venv/bin/pip install -r prototypes/memory-node/requirements-optional.txt
sudo chown -R <SERVICE_USER>: /opt/memorysystemai
sudo chmod 700 /opt/memorysystemai/state
```

> Do **not** copy the repository-root `memory_index.json` if you want a blank
> slate: the node creates its own index on first start.

## 5. Configuration

```bash
sudo mkdir -p /etc/memory-node
sudo cp prototypes/memory-node/config.example.env /etc/memory-node/memory-node.env
sudo chmod 600 /etc/memory-node/memory-node.env
sudoedit /etc/memory-node/memory-node.env
```

Variables read by the code: `AGENT_PORT`, `OLLAMA_HOST`, `OLLAMA_MODEL`,
`OLLAMA_FALLBACK`, `NVIDIA_API_KEY`, `NVIDIA_TEXT_MODEL`, `PUTER_AUTH_TOKEN`,
`PUTER_MODEL`, `PUTER_VISION_MODEL`, `VISION_PROVIDER`, `VISION_FALLBACK_PUTER`,
`WHISPER_MODEL`, `VOICE_LOOP`, `AUTONOMY_LOOP`, `AUTONOMY_INTERVAL`; for the bridge:
`MEMORY_NODE_URL`, `ASK_POLLER_INTERVAL`, `ASK_POLLER_STATE`, `TELEGRAM_BOT_TOKEN`,
`TELEGRAM_CHAT_ID`, `OPENCLAW_CONFIG`.

Tokens: `state/nvidia_token.txt`, `state/puter_token.txt` (mode 600) — excluded by `.gitignore`.

> Always set `OLLAMA_FALLBACK`: its default value in the code points to an
> address on the prototype's local network.

## 6. Running

Manual:

```bash
cd /opt/memorysystemai
set -a; . /etc/memory-node/memory-node.env; set +a
.venv/bin/python organism.py
curl -s http://127.0.0.1:8765/status
```

systemd service (generic example:
[`systemd/memory-node.service.generic.example`](../../prototypes/memory-node/systemd/memory-node.service.generic.example)):

```bash
sudo cp prototypes/memory-node/systemd/memory-node.service.generic.example \
        /etc/systemd/system/memory-node.service
sudoedit /etc/systemd/system/memory-node.service    # <SERVICE_USER>
sudo systemctl daemon-reload
sudo systemctl enable --now memory-node
journalctl -u memory-node -f
```

Network safety: the API has no authentication. Restrict the port (e.g. `ufw allow
from <CONTROL_HOST_IP> to any port 8765`) and never expose the node to the Internet.

## 7. Tests on a real node

1. Backup: `tar czf backups/<name>_$(date +%Y%m%dT%H%M%S).tgz MemorySystemAI/memory_index.json state/`
2. Smoke test: `curl -s http://127.0.0.1:8765/status`
3. Contradiction protocol: [`TEST_PROTOCOL_CONTRADICTIONS.md`](TEST_PROTOCOL_CONTRADICTIONS.md)
4. Duplicate merge (copy first): see the
   [change record](changements/2026-10-25_detection-contradictions.md).
5. Automated tests: [`prototypes/memory-node/tests/`](../../prototypes/memory-node/tests/README.en.md).

## 8. Updates and rollback

Always: stop the service → back up → copy the files → restart → check `/status`
and `journalctl`. Each record in [`changements/`](changements/README.md) gives its rollback procedure.

---

See also: [prototype README](../../prototypes/memory-node/README.en.md) ·
[contradiction protocol](TEST_PROTOCOL_CONTRADICTIONS.md) ·
[change records](changements/README.md) · [CHANGELOG](../../CHANGELOG.en.md)
