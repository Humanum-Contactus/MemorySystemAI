#!/usr/bin/env python3
"""
Gestion des capteurs caméra (sens V) — V4L2.

L'organisme peut lire / régler ses paramètres (brightness, gamma, exposure…)
et les auto-ajuster selon la luminosité réelle de la frame.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEVICE = "/dev/video0"

# Contrôles utiles pour la nursery (pièce sombre)
CTRL_KEYS = (
    "brightness",
    "contrast",
    "saturation",
    "gamma",
    "sharpness",
    "backlight_compensation",
    "auto_exposure",
    "exposure_time_absolute",
    "white_balance_automatic",
    "power_line_frequency",
)


def _sh(cmd: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def list_controls(device: str = DEVICE) -> Dict[str, Any]:
    """Parse `v4l2-ctl --list-ctrls` → {name: {min,max,step,default,value,flags}}."""
    try:
        p = _sh(["v4l2-ctl", "-d", device, "--list-ctrls"], timeout=10)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if p.returncode != 0:
        return {"ok": False, "error": (p.stderr or p.stdout or "")[-300:]}

    ctrls: Dict[str, Any] = {}
    # brightness 0x00980900 (int) : min=-64 max=64 step=1 default=0 value=0
    pat = re.compile(
        r"^\s*([a-z0-9_]+)\s+0x[0-9a-f]+\s+\(([^)]+)\)\s*:\s*(.*)$",
        re.I,
    )
    for line in (p.stdout or "").splitlines():
        m = pat.match(line)
        if not m:
            continue
        name, typ, rest = m.group(1), m.group(2), m.group(3)
        info: Dict[str, Any] = {"type": typ}
        for key in ("min", "max", "step", "default", "value"):
            km = re.search(rf"{key}=(-?\d+)", rest)
            if km:
                info[key] = int(km.group(1))
        if "flags=" in rest:
            info["flags"] = rest.split("flags=")[-1].strip()
        ctrls[name] = info
    return {"ok": True, "device": device, "controls": ctrls}


def get_control(name: str, device: str = DEVICE) -> Optional[int]:
    try:
        p = _sh(["v4l2-ctl", "-d", device, f"--get-ctrl={name}"], timeout=8)
        # brightness: 12
        m = re.search(r":\s*(-?\d+)", p.stdout or "")
        return int(m.group(1)) if m else None
    except Exception:
        return None


def set_control(name: str, value: int, device: str = DEVICE) -> Dict[str, Any]:
    try:
        p = _sh(
            ["v4l2-ctl", "-d", device, f"--set-ctrl={name}={int(value)}"],
            timeout=8,
        )
        if p.returncode != 0:
            return {"ok": False, "name": name, "error": (p.stderr or "")[-200:]}
        got = get_control(name, device)
        return {"ok": True, "name": name, "value": got if got is not None else value}
    except Exception as e:
        return {"ok": False, "name": name, "error": str(e)}


def set_controls(updates: Dict[str, int], device: str = DEVICE) -> Dict[str, Any]:
    applied = []
    errors = []
    for k, v in updates.items():
        r = set_control(k, int(v), device)
        if r.get("ok"):
            applied.append(r)
        else:
            errors.append(r)
    return {"ok": not errors, "applied": applied, "errors": errors}


def frame_luminance(image_path: str | Path) -> Optional[Dict[str, float]]:
    """Moyenne / percentiles de luminosité (0-255) d'une image JPEG/PNG."""
    path = Path(image_path)
    if not path.exists():
        return None
    try:
        import cv2  # type: ignore

        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        import numpy as np  # type: ignore

        mean = float(img.mean())
        flat = img.reshape(-1)
        p10 = float(np.percentile(flat, 10))
        p90 = float(np.percentile(flat, 90))
        # face-ish center crop mean
        h, w = img.shape[:2]
        y0, y1 = h // 5, 4 * h // 5
        x0, x1 = w // 5, 4 * w // 5
        center = float(img[y0:y1, x0:x1].mean())
        return {
            "mean": round(mean, 1),
            "center": round(center, 1),
            "p10": round(p10, 1),
            "p90": round(p90, 1),
        }
    except Exception:
        return None


def propose_auto_adjust(lum: Dict[str, float], ctrls: Dict[str, Any]) -> Dict[str, int]:
    """
    Propose des réglages selon la luminosité perçue.
    Cible nursery : visage lisible même en pièce sombre (écran = lumière).
    """
    mean = float(lum.get("center") or lum.get("mean") or 0)
    updates: Dict[str, int] = {}

    def clamp(name: str, value: int) -> Optional[int]:
        info = ctrls.get(name) or {}
        if "min" not in info or "max" not in info:
            return None
        return max(int(info["min"]), min(int(info["max"]), int(value)))

    cur_b = int((ctrls.get("brightness") or {}).get("value") or 0)
    cur_g = int((ctrls.get("gamma") or {}).get("value") or 300)
    cur_c = int((ctrls.get("contrast") or {}).get("value") or 50)

    if mean < 55:
        # Très sombre (nursery de nuit) — ouvrir au max utile d'un coup
        nb = clamp("brightness", 64)  # max UVC typique
        ng = clamp("gamma", 500)
        nc = clamp("contrast", max(cur_c, 68))
        if nb is not None:
            updates["brightness"] = nb
        if ng is not None:
            updates["gamma"] = ng
        if nc is not None:
            updates["contrast"] = nc
        if "backlight_compensation" in ctrls:
            updates["backlight_compensation"] = 1
        if "auto_exposure" in ctrls:
            updates["auto_exposure"] = 1  # Manual
        if "exposure_time_absolute" in ctrls:
            # Plus long = plus de lumière (risque flou si mouvement)
            ne = clamp("exposure_time_absolute", 1600 if mean < 35 else 1000)
            if ne is not None:
                updates["exposure_time_absolute"] = ne
    elif mean < 95:
        # Encore sombre — booster fort sans tout saturer
        nb = clamp("brightness", max(cur_b + 20, 40))
        ng = clamp("gamma", max(cur_g + 60, 380))
        if nb is not None:
            updates["brightness"] = nb
        if ng is not None:
            updates["gamma"] = ng
        if "backlight_compensation" in ctrls:
            updates["backlight_compensation"] = 1
        if "auto_exposure" in ctrls:
            updates["auto_exposure"] = 1
        if "exposure_time_absolute" in ctrls:
            ne = clamp("exposure_time_absolute", max(cur_e := int((ctrls.get("exposure_time_absolute") or {}).get("value") or 166), 700))
            if ne is not None:
                updates["exposure_time_absolute"] = ne
    elif mean > 200:
        # Trop clair
        nb = clamp("brightness", cur_b - 20)
        ng = clamp("gamma", cur_g - 40)
        if nb is not None:
            updates["brightness"] = nb
        if ng is not None:
            updates["gamma"] = ng
        if "auto_exposure" in ctrls:
            updates["auto_exposure"] = 3
    elif mean > 165:
        nb = clamp("brightness", cur_b - 8)
        if nb is not None and nb != cur_b:
            updates["brightness"] = nb

    # Filtrer no-ops
    out = {}
    for k, v in updates.items():
        cur = (ctrls.get(k) or {}).get("value")
        if cur is None or int(cur) != int(v):
            out[k] = int(v)
    return out


def auto_tune_from_frame(
    image_path: str | Path,
    device: str = DEVICE,
    recapture: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Analyse une frame, ajuste les contrôles si besoin.
    Si `recapture` est un callable () -> Dict path, reprend une 2e capture.
    """
    listed = list_controls(device)
    if not listed.get("ok"):
        return {"ok": False, "error": listed.get("error"), "adjusted": False}

    ctrls = listed.get("controls") or {}
    lum = frame_luminance(image_path)
    if not lum:
        return {"ok": False, "error": "luminance failed", "adjusted": False, "controls": _summary(ctrls)}

    proposed = propose_auto_adjust(lum, ctrls)
    result: Dict[str, Any] = {
        "ok": True,
        "luminance": lum,
        "proposed": proposed,
        "adjusted": False,
        "path": str(image_path),
        "controls_before": _summary(ctrls),
    }

    if not proposed:
        result["note"] = "luminosité OK — pas d'ajustement"
        result["controls"] = _summary(ctrls)
        return result

    applied = set_controls(proposed, device)
    result["applied"] = applied.get("applied")
    result["adjusted"] = bool(applied.get("applied"))
    result["errors"] = applied.get("errors")

    # Laisser la caméra stabiliser puis éventuellement recapturer (2 passes max)
    if result["adjusted"] and callable(recapture):
        import time

        time.sleep(0.55)
        second = recapture()
        if second and second.get("ok") and second.get("path"):
            result["path"] = second["path"]
            result["recaptured"] = True
            lum2 = frame_luminance(second["path"])
            result["luminance_after"] = lum2
            # 2e passe si encore trop sombre
            if lum2 and float(lum2.get("center") or lum2.get("mean") or 0) < 70:
                ctrls2 = (list_controls(device).get("controls") or {})
                prop2 = propose_auto_adjust(lum2, ctrls2)
                if prop2:
                    set_controls(prop2, device)
                    result["second_pass"] = prop2
                    time.sleep(0.5)
                    third = recapture()
                    if third and third.get("ok") and third.get("path"):
                        result["path"] = third["path"]
                        result["luminance_after"] = frame_luminance(third["path"])
        else:
            result["recaptured"] = False

    after = list_controls(device)
    result["controls"] = _summary((after.get("controls") or ctrls))
    return result


def _summary(ctrls: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k in CTRL_KEYS:
        if k in ctrls and "value" in ctrls[k]:
            out[k] = ctrls[k]["value"]
    return out
