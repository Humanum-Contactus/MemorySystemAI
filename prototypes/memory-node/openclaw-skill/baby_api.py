#!/usr/bin/env python3
"""CLI bridge → Sensors&MemorySystemAI / MemorySystemAI organism (memory-node).

Configure:
  MEMORY_NODE_URL=http://HOST:8765
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("MEMORY_NODE_URL", "http://127.0.0.1:8765").rstrip("/")


def call(method: str, path: str, body: dict | None = None, timeout: int = 120) -> dict:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except Exception:
            return {"ok": False, "error": f"HTTP {e.code}", "body": raw[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main() -> int:
    p = argparse.ArgumentParser(description="Memory-node organism API")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("memories")
    sub.add_parser("ask")
    pe = sub.add_parser("perceive")
    pe.add_argument("text", nargs="+")
    pe.add_argument("--speak", action="store_true")
    an = sub.add_parser("answer")
    an.add_argument("text", nargs="+")
    se = sub.add_parser("see")
    se.add_argument("--speak", action="store_true")
    he = sub.add_parser("hear")
    he.add_argument("--seconds", type=float, default=4)
    sp = sub.add_parser("speak")
    sp.add_argument("text", nargs="+")
    args = p.parse_args()

    if args.cmd == "status":
        out = call("GET", "/status", timeout=15)
    elif args.cmd == "memories":
        out = call("GET", "/memories", timeout=20)
    elif args.cmd == "ask":
        out = call("GET", "/ask", timeout=15)
    elif args.cmd == "perceive":
        out = call("POST", "/perceive", {"text": " ".join(args.text), "speak": bool(args.speak)}, timeout=180)
    elif args.cmd == "answer":
        out = call("POST", "/ask/answer", {"answer": " ".join(args.text)}, timeout=30)
    elif args.cmd == "see":
        out = call("POST", "/see", {"speak": bool(args.speak)}, timeout=60)
    elif args.cmd == "hear":
        out = call("POST", "/hear", {"seconds": args.seconds, "speak": True}, timeout=90)
    elif args.cmd == "speak":
        out = call("POST", "/speak", {"text": " ".join(args.text)}, timeout=60)
    else:
        return 2

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
