#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemorySystemAI — Sensory-Emotional Memory System for AI
Based on the MemorySystemAI v1 whitepaper (Vincent Vermeille & Volt)

Full loop: Reception -> Evaluation -> Recording -> Reinforcement -> Injection -> Decision
"""

import json
import datetime
import os
import sys
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS — From the whitepaper
# ═══════════════════════════════════════════════════════════════════════════

FUNDAMENTALS = {
    "V":  {"name": "Vision",     "channel": "visual"},
    "O":  {"name": "Hearing",    "channel": "auditory"},
    "T":  {"name": "Touch",      "channel": "tactile"},
    "G":  {"name": "Taste",      "channel": "gustatory"},
    "Od": {"name": "Smell",      "channel": "olfactory"},
    "I":  {"name": "Intuition",  "channel": "cognitive"},
    "C":  {"name": "Consciousness","channel": "meta"},
}

EMOTIONAL_STATES = {
    "P": {"name": "Positive", "effect": "light reinforcement or maintenance"},
    "N": {"name": "Negative", "effect": "strong reinforcement (+2 to +4)"},
    "X": {"name": "Unknown",  "effect": "maintenance or slight decay"},
}

THRESHOLD_RECORD  = 5   # Exposant >= 5 to record
THRESHOLD_INJECT  = 7   # Exposant >= 7 to inject proactively
THRESHOLD_BLOCK   = 9   # Exposant >= 9 to block action

RISK_PATTERNS = [
    "rm -rf", "sudo rm", "rm -r", "rm -f",
    "mkfs", "newfs", "format", "diskutil erase",
    "dd if=", "dd of=",
    "shutdown", "reboot", "halt",
    "sudo",
]

KEYWORD_GROUPS = {
    "partition": ["partition", "efi", "boot", "volumes"],
    "delete":    ["rm", "-rf", "delet", "eras", "remov", "wipe"],
    "format":    ["format", "mkfs", "newfs"],
    "elevated":  ["sudo", "su -", "root"],
}


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY ENTRY
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MemoryEntry:
    """Sensory-emotional memory entry — Schema MemorySystemAI/v1"""

    id: str
    date: str
    source: str                    # "human" | "experience" | "correlation"
    fundamental: str               # "V"|"O"|"T"|"G"|"Od"|"I"|"C"
    state: str                     # "P"|"N"|"X"
    exposant: int                  # 1-10
    data: str                      # What was learned
    correlations: List[str] = field(default_factory=list)

    # Optional fields (exposant >= 7)
    inhibition_tags: List[str] = field(default_factory=list)
    action_context: str = ""
    consequence: str = ""
    human_feedback: str = ""
    reinforcement_log: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        if not 1 <= self.exposant <= 10:
            raise ValueError(f"Exposant out of range (1-10): {self.exposant}")
        if self.fundamental not in FUNDAMENTALS:
            raise ValueError(f"Invalid fundamental: {self.fundamental}")
        if self.state not in EMOTIONAL_STATES:
            raise ValueError(f"Invalid state: {self.state}")
        # Auto-tag if exposant >= 7 and no tags defined
        if self.exposant >= 7 and not self.inhibition_tags:
            self.inhibition_tags = self._auto_tags()

    # --- Serialization ---

    def to_dict(self) -> dict:
        d = {
            "id": self.id, "date": self.date, "source": self.source,
            "fundamental": self.fundamental, "state": self.state,
            "exposant": self.exposant, "data": self.data,
            "correlations": self.correlations,
        }
        if self.inhibition_tags:
            d["inhibition_tags"] = self.inhibition_tags
        if self.action_context:
            d["action_context"] = self.action_context
        if self.consequence:
            d["consequence"] = self.consequence
        if self.human_feedback:
            d["human_feedback"] = self.human_feedback
        if self.reinforcement_log:
            d["reinforcement_log"] = self.reinforcement_log
        return d

    @classmethod
    def from_dict(cls, raw: dict) -> "MemoryEntry":
        """Create from a JSON dict. Handles both v1 and legacy field names."""
        # Map legacy French field names to English
        mapping = {
            "donnee": "data", "etat": "state",
            "tags_inhibition": "inhibition_tags",
            "contexte_action": "action_context",
            "retour_humain": "human_feedback",
            "renforcement_historique": "reinforcement_log",
            "fondamental": "fundamental",
        }
        d = {}
        for k, v in raw.items():
            key = mapping.get(k, k)
            d[key] = v
        # Required fields with defaults for legacy data
        return cls(
            id=d["id"],
            date=d.get("date", "2026-01-01"),
            source=d.get("source", "experience"),
            fundamental=d.get("fundamental", d.get("fondamental", "I")),
            state=d.get("state", d.get("etat", "X")),
            exposant=d.get("exposant", d.get("exponente", 5)),
            data=d.get("data", d.get("donnee", "")),
            correlations=d.get("correlations", d.get("correlaciones", [])),
            inhibition_tags=d.get("inhibition_tags", d.get("tags_inhibition", [])),
            action_context=d.get("action_context", d.get("contexte_action", "")),
            consequence=d.get("consequence", ""),
            human_feedback=d.get("human_feedback", d.get("retour_humain", "")),
            reinforcement_log=d.get("reinforcement_log", d.get("renforcement_historique", [])),
        )

    # --- Properties ---

    @property
    def is_critical(self) -> bool:
        return self.exposant >= THRESHOLD_BLOCK

    @property
    def should_inject(self) -> bool:
        return self.exposant >= THRESHOLD_INJECT

    @property
    def should_block(self) -> bool:
        return self.exposant >= THRESHOLD_BLOCK

    # --- Tags & Inhibition ---

    def _auto_tags(self) -> List[str]:
        tags = set()
        text = f"{self.data} {self.action_context} {self.consequence}".lower()
        for pattern in RISK_PATTERNS:
            if pattern.lower() in text:
                tags.add(pattern.lower())
        for group_name, keywords in KEYWORD_GROUPS.items():
            if any(kw in text for kw in keywords):
                tags.add(group_name)
        return sorted(tags)

    def matches_tags(self, text: str) -> bool:
        if not self.inhibition_tags:
            return False
        t = text.lower()
        return any(tag.lower() in t for tag in self.inhibition_tags)

    def inhibition_message(self, action_text: str) -> Optional[str]:
        """Return an inhibition message if this entry applies, None otherwise."""
        if not self.matches_tags(action_text):
            return None

        fund_name = FUNDAMENTALS[self.fundamental]["name"]
        state_name = EMOTIONAL_STATES[self.state]["name"]

        if self.should_block:
            header = f"[BLOCK - exposant {self.exposant}]"
        elif self.should_inject:
            header = f"[INJECT - exposant {self.exposant}]"
        else:
            header = f"[REMINDER - exposant {self.exposant}]"

        msg = f"{header}\n"
        msg += f"  Memory {self.id} | {fund_name}({self.fundamental}) | {state_name}({self.state})\n"
        msg += f"  Data: {self.data[:100]}\n"
        if self.consequence:
            msg += f"  Consequence: {self.consequence[:120]}\n"
        if self.should_block:
            msg += "  >>> ACTION BLOCKED — human confirmation required <<<\n"

        return msg

    # --- Reinforcement ---

    def reinforce(self, delta: int, reason: str) -> None:
        old = self.exposant
        new = max(1, min(10, old + delta))
        # Traumatic memories never drop below 7
        if old >= 9 and delta < 0:
            new = max(7, new)
        self.exposant = new
        self.reinforcement_log.append({
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "old_exposant": old,
            "new_exposant": new,
            "reason": reason,
        })


# ═══════════════════════════════════════════════════════════════════════════
# MAIN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

class MemorySystem:
    """
    MemorySystemAI — Sensory-Emotional Memory System.

    Full loop: Reception -> Evaluation -> Recording -> Reinforcement -> Injection -> Decision
    """

    def __init__(self, path: str = None):
        if path is None:
            path = os.path.join(
                os.path.expanduser("~"), ".openclaw", "workspace",
                "MemorySystemAI", "memory_index.json"
            )
        self.path = Path(path)
        self.entries: Dict[str, MemoryEntry] = {}
        self._counter = 0
        self._load()

    # --- Persistence ---

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Accept plain list or dict with "entries" key
            if isinstance(raw, list):
                items = raw
            elif isinstance(raw, dict):
                items = raw.get("entries", [])
            else:
                items = []

            for item in items:
                try:
                    e = MemoryEntry.from_dict(item)
                    self.entries[e.id] = e
                    try:
                        num = int(e.id.replace("M", ""))
                        self._counter = max(self._counter, num)
                    except ValueError:
                        pass
                except (ValueError, KeyError):
                    pass  # Skip malformed entries
        except (json.JSONDecodeError, Exception):
            pass

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        schema = {
            "schema": "MemorySystemAI/v1",
            "version": "1.0",
            "generated": datetime.datetime.now().isoformat(),
            "stats": self._stats(),
            "entries": [e.to_dict() for e in self.entries.values()],
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)

    def _next_id(self) -> str:
        self._counter += 1
        return f"M{self._counter:03d}"

    # --- Creation ---

    def create(self, fundamental: str, state: str, exposant: int, data: str,
               source: str = "experience", correlations: List[str] = None,
               inhibition_tags: List[str] = None, action_context: str = "",
               consequence: str = "", human_feedback: str = "") -> MemoryEntry:
        e = MemoryEntry(
            id=self._next_id(),
            date=datetime.datetime.now().strftime("%Y-%m-%d"),
            source=source, fundamental=fundamental, state=state,
            exposant=exposant, data=data,
            correlations=correlations or [],
            inhibition_tags=inhibition_tags or [],
            action_context=action_context,
            consequence=consequence,
            human_feedback=human_feedback,
        )
        self.entries[e.id] = e
        self.save()
        return e

    # --- Search ---

    def search(self, **filters) -> List[MemoryEntry]:
        results = list(self.entries.values())
        if "fundamental" in filters:
            results = [e for e in results if e.fundamental == filters["fundamental"]]
        if "state" in filters:
            results = [e for e in results if e.state == filters["state"]]
        if "exposant_min" in filters:
            results = [e for e in results if e.exposant >= filters["exposant_min"]]
        if "exposant_max" in filters:
            results = [e for e in results if e.exposant <= filters["exposant_max"]]
        if "tags" in filters:
            tags_q = [t.lower() for t in filters["tags"]]
            results = [e for e in results
                       if any(t in (tag.lower() for tag in e.inhibition_tags) for t in tags_q)]
        if "text" in filters:
            q = filters["text"].lower()
            results = [e for e in results
                       if q in e.data.lower() or q in e.consequence.lower()]
        return sorted(results, key=lambda e: e.exposant, reverse=True)

    def by_id(self, mid: str) -> Optional[MemoryEntry]:
        return self.entries.get(mid)

    def critical(self) -> List[MemoryEntry]:
        return self.search(exposant_min=THRESHOLD_BLOCK)

    def injectable(self) -> List[MemoryEntry]:
        return self.search(exposant_min=THRESHOLD_INJECT)

    # --- ACTIVE INJECTION (key mechanism) ---

    def check_action(self, action_text: str) -> List[str]:
        """
        Check if an action triggers any inhibitions.
        Returns inhibition messages. Empty list = OK to proceed.
        """
        messages = []
        for e in self.injectable():
            msg = e.inhibition_message(action_text)
            if msg:
                messages.append(msg)

        # If no tag matches, check generic risk patterns
        if not messages:
            messages.extend(self._check_risk_patterns(action_text))

        return messages

    def is_blocked(self, action_text: str) -> bool:
        """True if the action is blocked by a critical memory."""
        return any(
            e.matches_tags(action_text) and e.should_block
            for e in self.injectable()
        )

    def _check_risk_patterns(self, text: str) -> List[str]:
        """Check generic risk patterns even without matching tags."""
        messages = []
        t = text.lower()
        patterns = [
            ("rm -rf",        "Recursive forced deletion — CRITICAL RISK"),
            ("sudo rm",       "Deletion with elevated privileges — HIGH RISK"),
            ("mkfs",          "Filesystem formatting — IMMEDIATE DESTRUCTION"),
            ("newfs",         "Filesystem formatting — IMMEDIATE DESTRUCTION"),
            ("diskutil erase","Disk erasure — IMMEDIATE DESTRUCTION"),
            ("dd if=",        "Low-level disk copy — DANGER"),
            ("> /dev/disk",   "Direct device write — DESTRUCTION"),
        ]
        for pattern, desc in patterns:
            if pattern in t:
                messages.append(f"[ALERT - Pattern detected] {desc}\n  Command: {text[:80]}\n")
        return messages

    # --- REINFORCEMENT ---

    def reinforce(self, mid: str, delta: int, reason: str) -> Optional[MemoryEntry]:
        e = self.entries.get(mid)
        if not e:
            return None
        e.reinforce(delta, reason)
        self.save()
        return e

    # --- EVALUATION (full loop) ---

    def evaluate(self, text: str, fundamental: str = None, state: str = None) -> MemoryEntry:
        """Main loop entry point: evaluate, record or reinforce."""
        if fundamental is None:
            fundamental = self._detect_fundamental(text)
        if state is None:
            state = self._detect_state(text)

        similar = self._find_similar(text)
        if similar:
            delta = 3 if state == "N" else (1 if state == "P" else 0)
            if delta:
                similar.reinforce(delta, f"Reactivation: {text[:50]}")
            self.save()
            return similar
        else:
            exp = 7 if state == "N" else 5
            return self.create(fundamental, state, exp, text)

    def _detect_fundamental(self, text: str) -> str:
        t = text.lower()
        scores = {
            "C": sum(1 for w in ["learn", "reflex", "habit", "error", "understand", "conscious", "i "] if w in t),
            "I": sum(1 for w in ["analysis", "correlat", "deduc", "link", "cause", "pattern", "bug"] if w in t),
            "T": sum(1 for w in ["touch", "manipul", "action", "shock", "fear", "pain"] if w in t),
            "V": sum(1 for w in ["see", "observ", "visual", "text", "writ", "read"] if w in t),
            "O": sum(1 for w in ["hear", "audio", "sound", "speak"] if w in t),
            "G": sum(1 for w in ["test", "try", "taste", "check"] if w in t),
            "Od": sum(1 for w in ["feel", "perceiv", "pressent", "ambianc"] if w in t),
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "I"

    def _detect_state(self, text: str) -> str:
        t = text.lower()
        neg = sum(1 for w in ["error", "crash", "panic", "problem", "lost", "bad",
                              "fail", "broken", "block", "dead", "destroy", "delet", "wip"] if w in t)
        pos = sum(1 for w in ["success", "good", "great", "perfect", "done",
                              "correct", "well", "efficient", "awesome"] if w in t)
        if neg > 0 and neg >= pos:
            return "N"
        if pos > 0:
            return "P"
        return "X"

    def _find_similar(self, text: str) -> Optional[MemoryEntry]:
        words = set(text.lower().split())
        if len(words) < 2:
            return None
        for e in self.entries.values():
            common = words & set(e.data.lower().split())
            if len(common) >= 3:
                return e
        return None

    # --- OPENCLAW CONTEXT ---

    def injection_context(self, limit: int = 2000) -> str:
        """Generate context text to inject before each risky action."""
        inj = self.injectable()
        if not inj:
            return ""
        lines = ["== ACTIVE MEMORIES (MemorySystemAI) ==", ""]
        for e in sorted(inj, key=lambda x: x.exposant, reverse=True)[:8]:
            icon = "🚨" if e.is_critical else "⚠️"
            st = "🔴" if e.state == "N" else "🟢" if e.state == "P" else "⚪"
            lines.append(f"{icon} [{e.id}] {st} Exp.{e.exposant} ({e.fundamental}) {e.data[:70]}")
            if e.consequence:
                lines.append(f"    Consequence: {e.consequence[:80]}")
            lines.append("")
        return "\n".join(lines)

    def summary(self) -> str:
        """Summary bulletin for heartbeat."""
        s = self._stats()
        pe = s["by_state"]
        return (
            f"== MemorySystemAI ==\n"
            f"  {s['total']} entries | "
            f"🚨 {s['critical']} critical | ⚠️ {s['injectable']} injectable\n"
            f"  Emotions: 🔴N:{pe['N']} 🟢P:{pe['P']} ⚪X:{pe['X']}\n"
            f"  Avg exposant: {s['avg_exposant']}"
        )

    # --- Stats ---

    def _stats(self) -> dict:
        if not self.entries:
            return {"total": 0, "critical": 0, "injectable": 0,
                    "by_state": {"P": 0, "N": 0, "X": 0}, "avg_exposant": 0.0}
        pe = {"P": 0, "N": 0, "X": 0}
        pf = {}
        total_exp = 0
        for e in self.entries.values():
            pe[e.state] = pe.get(e.state, 0) + 1
            pf[e.fundamental] = pf.get(e.fundamental, 0) + 1
            total_exp += e.exposant
        crit = sum(1 for e in self.entries.values() if e.is_critical)
        inj = sum(1 for e in self.entries.values() if e.should_inject)
        return {
            "total": len(self.entries),
            "critical": crit,
            "injectable": inj,
            "by_state": pe,
            "by_fundamental": pf,
            "avg_exposant": round(total_exp / len(self.entries), 1),
        }

    def __repr__(self):
        s = self._stats()
        return f"MemorySystem({s['total']} entries, avg={s['avg_exposant']})"


# ═══════════════════════════════════════════════════════════════════════════
# OPENCLAW INTERFACE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_PATH = os.path.join(
    os.path.expanduser("~"), ".openclaw", "workspace",
    "MemorySystemAI", "memory_index.json"
)

def init(path: str = None) -> MemorySystem:
    """Initialize the system — call at the start of each session."""
    return MemorySystem(path or DEFAULT_PATH)

def check_before_action(command: str, path: str = None) -> List[str]:
    """Check inhibitions before an action. Empty list = OK."""
    ms = MemorySystem(path or DEFAULT_PATH)
    return ms.check_action(command)

def is_blocked(command: str, path: str = None) -> bool:
    """True if the action is blocked by a critical memory."""
    ms = MemorySystem(path or DEFAULT_PATH)
    return ms.is_blocked(command)

def learn(fundamental: str, state: str, exposant: int, data: str,
          action_context: str = "", consequence: str = "",
          path: str = None) -> MemoryEntry:
    """Create a new memory entry from code."""
    ms = MemorySystem(path or DEFAULT_PATH)
    return ms.create(fundamental, state, exposant, data,
                      action_context=action_context, consequence=consequence)

def context(path: str = None) -> str:
    """Generate context to inject into the system prompt."""
    ms = MemorySystem(path or DEFAULT_PATH)
    return ms.injection_context()

def bulletin(path: str = None) -> str:
    """Summary bulletin for heartbeat."""
    ms = MemorySystem(path or DEFAULT_PATH)
    return ms.summary()


# ═══════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("MemorySystemAI - Self-test")
    print("=" * 60)

    ms = init()
    print(f"\n{ms}\n")
    print(ms.summary())
    print()

    # Test risky action check
    cmd = "sudo rm -rf /Volumes/EFI_USB"
    print(f"Test: {cmd}")
    inhibitions = ms.check_action(cmd)
    if inhibitions:
        for i, msg in enumerate(inhibitions, 1):
            print(f"\n--- Inhibition #{i} ---")
            print(msg)
    else:
        print("  No inhibitions")

    # Test safe action
    print(f"\nTest: ls /tmp")
    result = ms.check_action("ls /tmp")
    print(f"  {'No inhibitions' if not result else f'{len(result)} inhibition(s)'}")

    # Test blocking
    print(f"\nBlock test '{cmd}': {ms.is_blocked(cmd)}")
    print(f"Block test 'ls /tmp': {ms.is_blocked('ls /tmp')}")

    print(f"\n{ms.summary()}")
