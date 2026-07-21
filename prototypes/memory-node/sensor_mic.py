#!/usr/bin/env python3
"""
Capteur micro (sens O) — ALSA Capture / Mic Boost.

Comme la caméra : mesurer le niveau réel du WAV, proposer un réglage,
ré-écouter si besoin. La norme « quel gain marche » peut ensuite
vivre dans les mémoires (expérience O/P ou O/N).
"""
from __future__ import annotations

import math
import re
import struct
import subprocess
import wave
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Contrôles typiques Acer / Realtek nursery
CAPTURE_CTRL = "Capture"
BOOST_CANDIDATES = (
    "Internal Mic Boost",
    "Headset Mic Boost",
    "Mic Boost",
    "Mic",
)
SOURCE_CTRL = "Capture Source"


def _sh(cmd: List[str], timeout: int = 12) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def list_controls() -> Dict[str, Any]:
    try:
        p = _sh(["amixer", "scontrols"], timeout=10)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    names = re.findall(r"'([^']+)'", p.stdout or "")
    detail: Dict[str, Any] = {}
    for name in names:
        if name in ("Master", "PCM", "Speaker", "Headphone", "Beep") or name.startswith("IEC958"):
            continue
        try:
            sp = _sh(["amixer", "sget", name], timeout=8)
            out = sp.stdout or ""
        except Exception:
            continue
        pct = None
        m = re.search(r"\[(\d{1,3})%\]", out)
        if m:
            pct = int(m.group(1))
        on = "[on]" in out.lower() and "[off]" not in out.split(":")[-1].lower()
        detail[name] = {"percent": pct, "raw_tail": out[-180:], "capture_on": "[on]" in out}
    return {"ok": True, "names": names, "controls": detail}


def get_percent(control: str) -> Optional[int]:
    try:
        p = _sh(["amixer", "sget", control], timeout=8)
        m = re.search(r"\[(\d{1,3})%\]", p.stdout or "")
        return int(m.group(1)) if m else None
    except Exception:
        return None


def set_percent(control: str, percent: int, capture: bool = True) -> Dict[str, Any]:
    pct = max(0, min(100, int(percent)))
    args = ["amixer", "-q", "sset", control, f"{pct}%"]
    if capture:
        args.append("cap")
    try:
        p = _sh(args, timeout=10)
        return {
            "ok": p.returncode == 0,
            "control": control,
            "percent": pct,
            "error": (p.stderr or "")[-200:] if p.returncode else None,
        }
    except Exception as e:
        return {"ok": False, "control": control, "error": str(e)}


def set_delta(control: str, delta: int) -> Dict[str, Any]:
    d = int(delta)
    suf = f"{abs(d)}%+" if d >= 0 else f"{abs(d)}%-"
    try:
        p = _sh(["amixer", "-q", "sset", control, suf, "cap"], timeout=10)
        return {"ok": p.returncode == 0, "control": control, "delta": d, "percent": get_percent(control)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def active_boost_control() -> Optional[str]:
    listed = list_controls()
    names = set(listed.get("names") or [])
    for cand in BOOST_CANDIDATES:
        if cand in names:
            return cand
    return None


def measure_wav(path: str | Path) -> Dict[str, Any]:
    """RMS / peak sur WAV PCM16 (mono ou 1er canal)."""
    path = Path(path)
    if not path.exists():
        return {"ok": False, "error": "missing"}
    try:
        with wave.open(str(path), "rb") as f:
            n = f.getnframes()
            fr = f.readframes(n)
            ch = f.getnchannels()
            sw = f.getsampwidth()
            rate = f.getframerate()
        if sw != 2 or n == 0:
            return {"ok": False, "error": f"unsupported sw={sw} n={n}"}
        samples = struct.unpack("<" + "h" * (len(fr) // 2), fr)
        if ch == 2:
            samples = samples[::2]
        if not samples:
            return {"ok": False, "error": "empty"}
        rms = math.sqrt(sum(s * s for s in samples) / len(samples))
        peak = max(abs(s) for s in samples)
        # Fraction d'échantillons "actifs" (voix approximative)
        active = sum(1 for s in samples if abs(s) > 800) / len(samples)
        return {
            "ok": True,
            "rms": round(rms, 1),
            "peak": int(peak),
            "active_ratio": round(active, 3),
            "rate": rate,
            "n": len(samples),
            # Profils utiles pour décision
            "too_quiet": rms < 400 or (peak < 2000 and active < 0.02),
            "too_loud": peak >= 32000 or rms > 12000,
            "clipping": peak >= 32500,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def propose_adjust(level: Dict[str, Any], capture_pct: Optional[int], boost_pct: Optional[int]) -> Dict[str, int]:
    """Propose deltas % Capture / Boost selon mesure."""
    out: Dict[str, int] = {}
    cap = 70 if capture_pct is None else int(capture_pct)
    boost = 50 if boost_pct is None else int(boost_pct)

    if level.get("clipping") or level.get("too_loud"):
        # Saturation → baisser fort (souvent le vrai problème nursery)
        if cap > 40:
            out[CAPTURE_CTRL] = max(25, cap - 25)
        if boost_pct is not None and boost > 0:
            out["_boost"] = max(0, boost - 40)
    elif level.get("too_quiet"):
        if cap < 95:
            out[CAPTURE_CTRL] = min(100, cap + 20)
        if boost_pct is not None and boost < 100:
            out["_boost"] = min(100, boost + 35)
    elif level.get("ok") and level.get("rms", 0) < 900:
        # Un peu faible sans être silence total
        if cap < 90:
            out[CAPTURE_CTRL] = min(100, cap + 10)
        if boost_pct is not None and boost < 100:
            out["_boost"] = min(100, boost + 20)
    return out


def summary() -> Dict[str, Any]:
    listed = list_controls()
    boost = active_boost_control()
    return {
        "ok": bool(listed.get("ok")),
        "capture_percent": get_percent(CAPTURE_CTRL),
        "boost_control": boost,
        "boost_percent": get_percent(boost) if boost else None,
        "controls": {
            k: {"percent": v.get("percent")}
            for k, v in (listed.get("controls") or {}).items()
            if v.get("percent") is not None
        },
    }


def auto_tune_from_wav(
    wav_path: str | Path,
    rerecord: Optional[Callable[[], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Mesure le WAV, ajuste Capture/Boost si trop faible ou saturé.
    Si `rerecord` fourni et ajustement fait → 2e prise.
    """
    level = measure_wav(wav_path)
    before = summary()
    result: Dict[str, Any] = {
        "ok": bool(level.get("ok")),
        "level": level,
        "adjusted": False,
        "applied": {},
        "before": before,
        "path": str(wav_path),
    }
    if not level.get("ok"):
        result["error"] = level.get("error")
        return result

    boost_name = before.get("boost_control")
    proposed = propose_adjust(
        level,
        before.get("capture_percent"),
        before.get("boost_percent"),
    )
    result["proposed"] = dict(proposed)
    if not proposed:
        result["after"] = before
        return result

    applied: Dict[str, Any] = {}
    if CAPTURE_CTRL in proposed:
        r = set_percent(CAPTURE_CTRL, proposed[CAPTURE_CTRL], capture=True)
        applied[CAPTURE_CTRL] = r
    if "_boost" in proposed and boost_name:
        r = set_percent(boost_name, proposed["_boost"], capture=False)
        applied[boost_name] = r

    result["applied"] = applied
    result["adjusted"] = any(v.get("ok") for v in applied.values())
    result["after"] = summary()

    if result["adjusted"] and rerecord is not None:
        try:
            second = rerecord()
            result["rerecord"] = {
                "ok": bool(second.get("ok")),
                "path": second.get("wav") or second.get("path"),
            }
            if second.get("ok") and (second.get("wav") or second.get("path")):
                new_path = second.get("wav") or second.get("path")
                result["path"] = new_path
                result["level_after"] = measure_wav(new_path)
                result["text_after"] = second.get("text")
        except Exception as e:
            result["rerecord"] = {"ok": False, "error": str(e)}

    return result
