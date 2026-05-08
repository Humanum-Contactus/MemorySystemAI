#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemorySystemAI — OpenClaw Integration Module
=============================================

Functions to integrate the memory system into OpenClaw sessions.
"""

import os
import sys
from typing import List, Dict, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from memory_system import MemorySystem, THRESHOLD_INJECT, THRESHOLD_BLOCK

DEFAULT_PATH = os.path.join(
    os.path.expanduser("~"), ".openclaw", "workspace",
    "MemorySystemAI", "memory_index.json"
)


def inject_context(path: str = None) -> str:
    """
    Call at the START of each OpenClaw session.
    Returns context text with active memories (exposant >= 7).
    """
    ms = MemorySystem(path or DEFAULT_PATH)
    return ms.injection_context()


def check_before_action(command: str, path: str = None) -> Dict[str, Any]:
    """
    Call BEFORE every destructive or risky action.

    Returns:
        {
            "blocked": bool,
            "messages": [str],
            "recommendation": str,
        }
    """
    ms = MemorySystem(path or DEFAULT_PATH)
    messages = ms.check_action(command)
    blocked = ms.is_blocked(command)

    if blocked:
        rec = "BLOCKED — human confirmation MANDATORY"
    elif messages:
        rec = "WARNED — verify before executing"
    else:
        rec = "OK — no inhibitions"

    return {"blocked": blocked, "messages": messages, "recommendation": rec}


def learn(fundamental: str, state: str, exposant: int, data: str,
          action_context: str = "", consequence: str = "",
          path: str = None) -> Dict[str, Any]:
    """Create a new memory entry from code."""
    ms = MemorySystem(path or DEFAULT_PATH)
    e = ms.create(fundamental, state, exposant, data,
                   action_context=action_context, consequence=consequence)
    return {"id": e.id, "exposant": e.exposant, "data": e.data}


def bulletin(path: str = None) -> str:
    """Summary for heartbeat."""
    ms = MemorySystem(path or DEFAULT_PATH)
    return ms.summary()


def prompt_context(path: str = None) -> str:
    """
    Generate a block ready to inject into an OpenClaw system prompt.
    """
    ms = MemorySystem(path or DEFAULT_PATH)
    inj = ms.injectable()
    if not inj:
        return ""
    inj.sort(key=lambda e: e.exposant, reverse=True)
    lines = [
        "== ACTIVE MEMORY SYSTEM ==",
        "",
        "These MEMORIES influence decisions:",
        "",
    ]
    for e in inj[:10]:
        st = "🔴" if e.state == "N" else "🟢" if e.state == "P" else "⚪"
        lines.append(f"  {st} [{e.id}] Exp.{e.exposant} ({e.fundamental}) {e.data[:60]}")
        if e.consequence:
            lines.append(f"       Consequence: {e.consequence[:70]}")
    lines.extend(["", "==" * 20])
    return "\n".join(lines)
