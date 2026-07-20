#!/usr/bin/env python3
"""Poll organism /ask and notify a Telegram chat when pending.

Env:
  MEMORY_NODE_URL=http://HOST:8765
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=...
  OPENCLAW_CONFIG=path to openclaw.json (optional fallback for bot token)
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

ORG = os.environ.get("MEMORY_NODE_URL", "http://127.0.0.1:8765").rstrip("/")
STATE = Path(os.environ.get("ASK_POLLER_STATE", str(Path(__file__).with_name("ask_poller_state.json"))))
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
INTERVAL = int(os.environ.get("ASK_POLLER_INTERVAL", "20"))
OPENCLAW = Path(os.environ.get("OPENCLAW_CONFIG", ""))


def load_token() -> str:
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if tok:
        return tok
    if OPENCLAW.exists():
        cfg = json.loads(OPENCLAW.read_text(encoding="utf-8"))
        return str(cfg.get("channels", {}).get("telegram", {}).get("botToken") or "")
    raise SystemExit("Set TELEGRAM_BOT_TOKEN or OPENCLAW_CONFIG")


def get_json(url: str, timeout: int = 15) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def tg_send(token: str, text: str) -> None:
    if not CHAT_ID:
        raise SystemExit("Set TELEGRAM_CHAT_ID")
    q = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text})
    url = f"https://api.telegram.org/bot{token}/sendMessage?{q}"
    with urllib.request.urlopen(url, timeout=30) as r:
        r.read()


def main() -> None:
    token = load_token()
    last = ""
    if STATE.exists():
        try:
            last = json.loads(STATE.read_text(encoding="utf-8")).get("last_ts", "")
        except Exception:
            last = ""
    print("ask_poller started", ORG, flush=True)
    while True:
        try:
            ask = get_json(f"{ORG}/ask")
            if ask.get("status") == "pending" and ask.get("question"):
                ts = str(ask.get("ts") or ask.get("question"))
                if ts != last:
                    msg = (
                        "Bébé MemorySystemAI demande de l'aide:\n\n"
                        f"{ask.get('question')}\n\n"
                        "Réponds puis: réponds au bébé: <ta réponse>"
                    )
                    tg_send(token, msg)
                    last = ts
                    STATE.write_text(json.dumps({"last_ts": last}, indent=2), encoding="utf-8")
                    print("notified", ts, flush=True)
        except Exception as e:
            print("poll error:", e, flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
