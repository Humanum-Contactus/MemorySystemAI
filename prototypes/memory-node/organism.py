#!/usr/bin/env python3
"""
memory-node — organisme MemorySystemAI (ardoise quasi vide)

Ce n'est PAS un chatbot avec règles texte.
C'est un système de mémoire sensorielle-émotionnelle qui :
  - démarre presque sans savoir
  - perçoit via des OUTILS (voir, entendre, parler)
  - consulte des LLM externes comme OUTILS pour interpréter
  - apprend (fondamentaux V/O/T/... + exposants)
  - inhibe seulement via des mémoires apprises (exposant élevé),
    pas via des interdits textuels hardcodés
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import request

ROOT = Path("/opt/memorysystemai")
sys.path.insert(0, str(ROOT))

from MemorySystemAI.memory_system import (  # noqa: E402
    FUNDAMENTALS,
    MemorySystem,
    THRESHOLD_BLOCK,
    THRESHOLD_INJECT,
    THRESHOLD_RECORD,
)

from visual_memory import (  # noqa: E402
    VisualPersonMemory,
    extract_identity_label,
    parse_auditory_correction,
)
from voice_memory import VoicePersonMemory  # noqa: E402
from sensor_camera import (  # noqa: E402
    auto_tune_from_frame,
    list_controls as camera_list_controls,
    set_controls as camera_set_controls,
    _summary as camera_summary,
)
from sensor_mic import (  # noqa: E402
    auto_tune_from_wav as mic_auto_tune_from_wav,
    measure_wav as mic_measure_wav,
    summary as mic_summary,
    set_percent as mic_set_percent,
    CAPTURE_CTRL as MIC_CAPTURE_CTRL,
)
from autonomy import AutonomyKit  # noqa: E402

STATE = ROOT / "state"
INDEX = ROOT / "MemorySystemAI" / "memory_index.json"
ASK = STATE / "ask_human.json"  # canal boîte aux lettres (pas la règle — la règle est en mémoire)
LOG = STATE / "organism.log"
SNAPS = STATE / "snapshots"
VISUAL_DB = STATE / "visual_persons.json"
VOICE_DB = STATE / "voice_persons.json"
TTS_DIR = ROOT / "tts"
PIPER_BIN = TTS_DIR / "piper" / "piper"
PIPER_VOICE = TTS_DIR / "fr_FR-siwis-medium.onnx"
UI_DIR = ROOT / "ui"
UI_INDEX = UI_DIR / "index.html"

OLLAMA_LOCAL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
OLLAMA_FALLBACK = os.environ.get("OLLAMA_FALLBACK", "http://192.168.50.48:11434")
PUTER_AUTH_TOKEN = os.environ.get("PUTER_AUTH_TOKEN", "").strip()
PUTER_MODEL = os.environ.get("PUTER_MODEL", "moonshotai/kimi-k2")
PUTER_VISION_MODEL = os.environ.get("PUTER_VISION_MODEL", "moonshotai/kimi-k3")
PUTER_BASE = os.environ.get(
    "PUTER_BASE",
    "https://api.puter.com/puterai/openai/v1",
).rstrip("/")
# NVIDIA NIM (même provider qu'OpenClaw Telegram) — vision sans crédits Puter
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()
NVIDIA_BASE = os.environ.get(
    "NVIDIA_BASE",
    "https://integrate.api.nvidia.com/v1",
).rstrip("/")
NVIDIA_VISION_MODEL = os.environ.get(
    "NVIDIA_VISION_MODEL",
    "google/gemma-4-31b-it",
)
NVIDIA_TOKEN_FILE = STATE / "nvidia_token.txt"
VISION_PROVIDER_FILE = STATE / "vision_provider.txt"
# Défaut: nvidia (crédits OpenClaw / build.nvidia) ; puter en secours
DEFAULT_VISION_PROVIDER = os.environ.get("VISION_PROVIDER", "nvidia").strip().lower()
PORT = int(os.environ.get("AGENT_PORT", "8765"))
PUTER_TOKEN_FILE = STATE / "puter_token.txt"


def _load_puter_token() -> str:
    if PUTER_AUTH_TOKEN:
        return PUTER_AUTH_TOKEN
    if PUTER_TOKEN_FILE.exists():
        try:
            return PUTER_TOKEN_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            return ""
    return ""


def _load_nvidia_token() -> str:
    if NVIDIA_API_KEY:
        return NVIDIA_API_KEY
    if NVIDIA_TOKEN_FILE.exists():
        try:
            return NVIDIA_TOKEN_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            return ""
    return ""


def get_vision_provider() -> str:
    """nvidia | puter — préférence persistée."""
    try:
        if VISION_PROVIDER_FILE.exists():
            v = VISION_PROVIDER_FILE.read_text(encoding="utf-8").strip().lower()
            if v in ("nvidia", "puter"):
                return v
    except Exception:
        pass
    return DEFAULT_VISION_PROVIDER if DEFAULT_VISION_PROVIDER in ("nvidia", "puter") else "nvidia"


def set_vision_provider(provider: str) -> str:
    p = (provider or "").strip().lower()
    if p not in ("nvidia", "puter"):
        raise ValueError("provider must be nvidia|puter")
    STATE.mkdir(parents=True, exist_ok=True)
    VISION_PROVIDER_FILE.write_text(p, encoding="utf-8")
    return p


def log(msg: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    line = f"{dt.datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def sh(cmd: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


# ─── OUTILS SENSORIELS ───────────────────────────────────────────────

def tool_speak(text: str) -> Dict[str, Any]:
    """TTS : Piper (naturel) > pico > mbrola > espeak."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty"}
    say = text[:500]
    STATE.mkdir(parents=True, exist_ok=True)
    wav = STATE / "tts_out.wav"

    # 1) Piper neural TTS (fr_FR-siwis) — le plus naturel en local
    if PIPER_BIN.exists() and PIPER_VOICE.exists():
        try:
            p = subprocess.run(
                [str(PIPER_BIN), "--model", str(PIPER_VOICE), "--output_file", str(wav)],
                input=say,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if p.returncode == 0 and wav.exists() and wav.stat().st_size > 100:
                sh(["aplay", "-q", str(wav)], timeout=90)
                return {"ok": True, "said": say, "engine": "piper:siwis"}
        except Exception:
            pass

    # 2) SVOX Pico
    try:
        p = sh(["pico2wave", "-l", "fr-FR", "-w", str(wav), say], timeout=30)
        if p.returncode == 0 and wav.exists() and wav.stat().st_size > 100:
            sh(["aplay", "-q", str(wav)], timeout=90)
            return {"ok": True, "said": say, "engine": "pico"}
    except Exception:
        pass

    # 3) eSpeak-NG + Mbrola / fr-ch
    for voice, speed in (("mb-fr4", 130), ("mb-fr1", 130), ("fr-ch", 135), ("fr", 140)):
        try:
            p = sh(
                ["espeak-ng", "-v", voice, "-s", str(speed), "-a", "180", say],
                timeout=90,
            )
            if p.returncode == 0:
                return {"ok": True, "said": say, "engine": f"espeak:{voice}"}
        except Exception:
            continue

    return {"ok": False, "error": "no tts engine", "said": say}


def tool_volume_get() -> Dict[str, Any]:
    """Lecture volume ALSA Master (pourcentage + mute)."""
    try:
        p = sh(["amixer", "sget", "Master"], timeout=10)
        out = (p.stdout or "") + (p.stderr or "")
        muted = "[off]" in out.lower()
        pct = None
        m = re.search(r"\[(\d{1,3})%\]", out)
        if m:
            pct = max(0, min(100, int(m.group(1))))
        return {"ok": True, "percent": pct, "muted": muted, "raw": out[-200:]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_volume_set(
    percent: Optional[int] = None,
    delta: Optional[int] = None,
    mute: Optional[bool] = None,
) -> Dict[str, Any]:
    """Réglage volume : percent absolu, delta relatif, ou mute on/off/toggle."""
    try:
        if mute is True:
            sh(["amixer", "-q", "sset", "Master", "mute"], timeout=10)
        elif mute is False:
            sh(["amixer", "-q", "sset", "Master", "unmute"], timeout=10)
        elif mute is None and percent is None and delta is None:
            # toggle
            cur = tool_volume_get()
            if cur.get("muted"):
                sh(["amixer", "-q", "sset", "Master", "unmute"], timeout=10)
            else:
                sh(["amixer", "-q", "sset", "Master", "mute"], timeout=10)

        if percent is not None:
            pct = max(0, min(100, int(percent)))
            sh(["amixer", "-q", "sset", "Master", f"{pct}%"], timeout=10)
            sh(["amixer", "-q", "sset", "Master", "unmute"], timeout=10)
        elif delta is not None:
            d = int(delta)
            if d >= 0:
                sh(["amixer", "-q", "sset", "Master", f"{abs(d)}%+"], timeout=10)
            else:
                sh(["amixer", "-q", "sset", "Master", f"{abs(d)}%-"], timeout=10)
            sh(["amixer", "-q", "sset", "Master", "unmute"], timeout=10)

        got = tool_volume_get()
        got["ok"] = True
        return got
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_see(auto_tune: bool = True) -> Dict[str, Any]:
    """Capture webcam ; auto-ajuste luminosité/gamma/exposition si trop sombre/clair."""
    SNAPS.mkdir(parents=True, exist_ok=True)

    def _capture() -> Dict[str, Any]:
        path = SNAPS / f"v_{int(time.time())}.jpg"
        try:
            p = sh([
                "ffmpeg", "-y", "-f", "v4l2", "-video_size", "640x480",
                "-i", "/dev/video0", "-frames:v", "1", str(path),
            ], timeout=25)
            if path.exists() and path.stat().st_size > 0:
                return {
                    "ok": True,
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "raw": f"frame 640x480 captured ({path.stat().st_size} bytes)",
                }
            return {"ok": False, "error": (p.stderr or "")[-300:]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    first = _capture()
    if not first.get("ok"):
        return first

    sensor: Dict[str, Any] = {"adjusted": False}
    if auto_tune:
        try:
            sensor = auto_tune_from_frame(first["path"], recapture=_capture)
            if sensor.get("recaptured") and sensor.get("path"):
                path = Path(sensor["path"])
                first = {
                    "ok": True,
                    "path": str(path),
                    "bytes": path.stat().st_size if path.exists() else 0,
                    "raw": f"frame 640x480 captured ({path.stat().st_size if path.exists() else 0} bytes) [auto-tuned]",
                }
        except Exception as e:
            sensor = {"ok": False, "error": str(e), "adjusted": False}

    first["sensor"] = sensor
    return first


def _record_wav(seconds: float) -> Dict[str, Any]:
    """Prise micro brute → WAV (sans STT)."""
    STATE.mkdir(parents=True, exist_ok=True)
    wav = STATE / f"o_{int(time.time())}.wav"
    try:
        p = sh([
            "arecord", "-D", "plughw:0,0", "-f", "S16_LE", "-r", "16000", "-c", "1",
            "-d", str(max(1, int(seconds))), str(wav),
        ], timeout=int(seconds) + 15)
        if not (wav.exists() and wav.stat().st_size > 1000):
            return {"ok": False, "error": (p.stderr or "record failed")[-300:]}
        return {"ok": True, "wav": str(wav), "path": str(wav)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _stt_wav(wav: str) -> Dict[str, Any]:
    try:
        from faster_whisper import WhisperModel
        global _whisper
        stt_model = os.environ.get("WHISPER_MODEL", "base")
        if "_whisper" not in globals() or _whisper is None or globals().get("_whisper_name") != stt_model:
            globals()["_whisper"] = WhisperModel(stt_model, device="cpu", compute_type="int8")
            globals()["_whisper_name"] = stt_model
        segs, _ = globals()["_whisper"].transcribe(
            str(wav),
            language="fr",
            vad_filter=True,
            beam_size=3,
            best_of=3,
            condition_on_previous_text=False,
        )
        text = " ".join(s.text.strip() for s in segs).strip()
        return {"ok": True, "text": text}
    except Exception as e:
        return {"ok": False, "text": "", "stt_error": str(e)}


def tool_hear(seconds: float = 4.0, auto_tune: bool = True) -> Dict[str, Any]:
    """
    Écoute micro + STT.
    Auto-ajuste Capture / Mic Boost selon le niveau réel du WAV
    (trop faible OU saturé — les deux empêchent de comprendre).
    """
    first = _record_wav(seconds)
    if not first.get("ok"):
        return first
    wav = first["wav"]
    sensor: Dict[str, Any] = {"adjusted": False, "level": mic_measure_wav(wav)}

    if auto_tune:
        try:
            sensor = mic_auto_tune_from_wav(
                wav,
                rerecord=lambda: _record_wav(seconds),
            )
            if sensor.get("adjusted") and sensor.get("path"):
                wav = str(sensor["path"])
        except Exception as e:
            sensor = {"ok": False, "error": str(e), "adjusted": False}

    stt = _stt_wav(wav)
    return {
        "ok": True,
        "wav": wav,
        "text": stt.get("text") or "",
        "stt_error": stt.get("stt_error"),
        "sensor": sensor,
        "level": sensor.get("level_after") or sensor.get("level") or mic_measure_wav(wav),
    }


def tool_consult_puter(
    prompt: str,
    system: str,
    image_path: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Consult Kimi via Puter OpenAI-compatible API. Optional local JPEG for vision."""
    token = _load_puter_token()
    if not token:
        return {"ok": False, "error": "no puter token", "text": ""}
    use_model = model or (PUTER_VISION_MODEL if image_path else PUTER_MODEL)

    user_content: Any
    if image_path and Path(image_path).exists():
        try:
            b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
            # Limiter ~1.5 Mo raw → déjà 640x480 ok
            user_content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                },
            ]
        except Exception as e:
            return {"ok": False, "error": f"image encode: {e}", "text": ""}
    else:
        user_content = prompt

    payload = {
        "model": use_model,
        "stream": False,
        "temperature": 0.3,
        "max_tokens": 450,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    }
    raw = json.dumps(payload).encode("utf-8")
    try:
        req = request.Request(
            f"{PUTER_BASE}/chat/completions",
            data=raw,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode())
        choices = body.get("choices") or []
        content = ""
        if choices:
            content = ((choices[0].get("message") or {}).get("content") or "").strip()
        if not content:
            content = (body.get("text") or body.get("response") or "").strip()
        if content:
            return {
                "ok": True,
                "source": f"puter:{use_model}",
                "text": content,
                "provider": "puter",
                "vision": bool(image_path),
            }
        return {"ok": False, "error": "empty puter response", "text": "", "raw": body}
    except Exception as e:
        log(f"consult_puter fail: {e}")
        return {"ok": False, "error": str(e), "text": ""}


def tool_consult_nvidia(
    prompt: str,
    system: str,
    image_path: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Consult NVIDIA NIM (OpenAI-compatible) — même stack qu'OpenClaw Telegram."""
    token = _load_nvidia_token()
    if not token:
        return {"ok": False, "error": "no nvidia token", "text": ""}
    use_model = model or NVIDIA_VISION_MODEL

    user_content: Any
    if image_path and Path(image_path).exists():
        try:
            b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
            user_content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                },
            ]
        except Exception as e:
            return {"ok": False, "error": f"image encode: {e}", "text": ""}
    else:
        user_content = prompt

    payload = {
        "model": use_model,
        "stream": False,
        "temperature": 0.3,
        "max_tokens": 450,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    }
    raw = json.dumps(payload).encode("utf-8")
    try:
        req = request.Request(
            f"{NVIDIA_BASE}/chat/completions",
            data=raw,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode())
        choices = body.get("choices") or []
        content = ""
        if choices:
            msg = choices[0].get("message") or {}
            content = (msg.get("content") or "").strip()
            if isinstance(content, list):
                # certains modèles renvoient des blocs
                content = " ".join(
                    (c.get("text") if isinstance(c, dict) else str(c)) for c in content
                ).strip()
        if content:
            return {
                "ok": True,
                "source": f"nvidia:{use_model}",
                "text": content,
                "provider": "nvidia",
                "vision": bool(image_path),
            }
        return {"ok": False, "error": "empty nvidia response", "text": "", "raw": str(body)[:400]}
    except Exception as e:
        log(f"consult_nvidia fail: {e}")
        return {"ok": False, "error": str(e), "text": ""}


def tool_consult_vision(image_path: str, prompt: str, system: str) -> Dict[str, Any]:
    """
    Vision multimodale avec switch de provider :
      nvidia (défaut, quota OpenClaw/build.nvidia) | puter (crédits Kimi)
    """
    provider = get_vision_provider()
    last: Dict[str, Any] = {"ok": False, "error": "no model", "text": ""}

    nvidia_models = (
        NVIDIA_VISION_MODEL,
        "google/gemma-4-31b-it",
        "qwen/qwen3.5-122b-a10b",
        "mistralai/mistral-small-4-119b-2603",
        # Llama 4 Maverick: vision OK mais souvent très lent / timeout
        "meta/llama-4-maverick-17b-128e-instruct",
    )
    puter_models = (PUTER_VISION_MODEL, "moonshotai/kimi-k3", "moonshotai/kimi-k2")
    # Ne PAS basculer auto vers Puter (crédits) sauf VISION_FALLBACK_PUTER=1
    allow_puter_fallback = os.environ.get("VISION_FALLBACK_PUTER", "0").strip() == "1"

    order: List[tuple] = []
    if provider == "nvidia":
        for m in nvidia_models:
            order.append(("nvidia", m))
        if allow_puter_fallback and _load_puter_token():
            for m in puter_models:
                order.append(("puter", m))
    else:
        for m in puter_models:
            order.append(("puter", m))
        if _load_nvidia_token():
            for m in nvidia_models:
                order.append(("nvidia", m))

    tried = set()
    for prov, model in order:
        key = f"{prov}:{model}"
        if key in tried:
            continue
        tried.add(key)
        if prov == "nvidia":
            last = tool_consult_nvidia(prompt, system, image_path=image_path, model=model)
        else:
            last = tool_consult_puter(prompt, system, image_path=image_path, model=model)
        if last.get("ok"):
            return last
        log(f"vision {key} fail: {last.get('error')}")
    return last


def tool_consult_ollama(prompt: str, system: str, bases: Optional[List[str]] = None) -> Dict[str, Any]:
    bases = bases or [OLLAMA_LOCAL, OLLAMA_FALLBACK]
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.4, "num_predict": 320},
    }
    raw = json.dumps(payload).encode()
    for base in bases:
        if not base:
            continue
        try:
            req = request.Request(
                f"{base.rstrip('/')}/api/chat",
                data=raw,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read().decode())
            content = (body.get("message") or {}).get("content") or body.get("response") or ""
            if content.strip():
                return {"ok": True, "source": f"ollama:{base}", "text": content.strip(), "provider": "ollama"}
        except Exception as e:
            log(f"consult_ollama fail {base}: {e}")
    return {"ok": False, "error": "no ollama available", "text": ""}


def tool_consult_llm(prompt: str, system: str, bases: Optional[List[str]] = None) -> Dict[str, Any]:
    """Consult external LLM(s) as a tool — not as identity.
    Ordre: Puter → NVIDIA (OpenClaw) → Ollama."""
    puter = tool_consult_puter(prompt, system)
    if puter.get("ok"):
        return puter
    # NVIDIA texte (même clé vision) — évite ask_human sur « salut / qui es-tu »
    if _load_nvidia_token():
        for model in (
            os.environ.get("NVIDIA_TEXT_MODEL", "deepseek-ai/deepseek-v4-flash"),
            "z-ai/glm-5.1",
            "google/gemma-4-31b-it",
        ):
            nv = tool_consult_nvidia(prompt, system, image_path=None, model=model)
            if nv.get("ok"):
                return nv
    return tool_consult_ollama(prompt, system, bases=bases)


def tool_ask_human(question: str, context: str = "") -> Dict[str, Any]:
    """Écriture brute ask_human.json — préférer Organism.request_human (inhibition)."""
    STATE.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "context": context,
        "status": "pending",
        "answer": None,
    }
    ASK.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "pending": True, "path": str(ASK), "question": question}


def _read_ask() -> Optional[Dict[str, Any]]:
    if not ASK.exists():
        return None
    try:
        return json.loads(ASK.read_text(encoding="utf-8"))
    except Exception:
        return None


# Action = ce que l'organisme *fait* quand il relance sans réponse.
# Les tags de la mémoire apprise (harceler, sans_attendre, …) matchent ceci.
ASK_HARASS_ACTION = (
    "harceler sans_attendre relancer questions_humaines "
    "adresser_humain telegram en_attente"
)


def tool_read_human_answer(for_perception: str = "", consume: bool = True) -> Optional[str]:
    """Ne réutilise une réponse humaine que si elle est fraîche (status=answered)
    et pertinente pour la perception en cours — jamais un vieux 'yes' orphelin."""
    if not ASK.exists():
        return None
    try:
        data = json.loads(ASK.read_text(encoding="utf-8"))
    except Exception:
        return None
    if data.get("status") != "answered" or not data.get("answer"):
        return None
    ans = str(data["answer"]).strip()
    q = str(data.get("question") or "").lower()
    perc = (for_perception or "").lower()
    # Pertinence minimale : au moins un token significatif en commun avec la question posée
    if perc and q:
        q_toks = {t for t in q.replace("?", " ").split() if len(t) > 4}
        p_toks = {t for t in perc.replace("?", " ").split() if len(t) > 4}
        if q_toks and p_toks and not (q_toks & p_toks):
            return None
    # Réponses trop génériques / tests anciens
    if ans.lower() in {"yes", "no", "oui", "non", "ok", "test"}:
        if consume:
            data["status"] = "consumed"
            ASK.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return None
    if consume:
        data["status"] = "consumed"
        ASK.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ans


# ─── ORGANISME ───────────────────────────────────────────────────────

BOOTSTRAP = [
    # Uniquement du méta structurel — pas de savoir du monde, pas d'interdits texte
    ("C", "X", 6, "Je suis un système de mémoire sensorielle-émotionnelle (MemorySystemAI). Je commence presque vide."),
    ("C", "X", 6, "Mes seuls accès au monde sont des outils : voir (caméra), entendre (micro), parler (haut-parleur)."),
    ("C", "X", 6, "Pour comprendre ce que je perçois, je peux consulter un modèle LLM externe ou interroger un humain."),
    ("C", "X", 5, "Les 7 fondamentaux : V vue, O ouïe, T toucher, G goût, Od odorat, I intuition, C conscience."),
    ("C", "X", 5, "L'exposant (1-10) est le poids émotionnel d'une mémoire. >=7 injection, >=9 inhibition forte apprise."),
    ("C", "X", 5, "J'apprends seulement par expérience, corrélation, retour humain — jamais par règles texte figées."),
]

class Organism:
    """Ardoise quasi vide + outils + apprentissage."""

    def __init__(self, reset: bool = False) -> None:
        STATE.mkdir(parents=True, exist_ok=True)
        SNAPS.mkdir(parents=True, exist_ok=True)
        if reset or not INDEX.exists() or INDEX.stat().st_size < 50:
            self._init_blank()
        self.ms = MemorySystem(str(INDEX))
        if len(self.ms.entries) == 0:
            self._seed_bootstrap()
        # Mémoires sensorielles natives (visage + voix → identité)
        if reset and VISUAL_DB.exists():
            VISUAL_DB.unlink()
        if reset and VOICE_DB.exists():
            VOICE_DB.unlink()
        self.visual = VisualPersonMemory(VISUAL_DB)
        self.voice = VoicePersonMemory(VOICE_DB)
        self.autonomy = AutonomyKit(self, STATE)

    def known_identity_labels(self) -> List[str]:
        """Noms déjà ancrés (visage + voix)."""
        labels: List[str] = []
        for p in (self.visual.summary().get("persons") or []):
            lab = (p.get("label") or "").strip()
            if lab and lab not in labels:
                labels.append(lab)
        for p in (self.voice.summary().get("persons") or []):
            lab = (p.get("label") or "").strip()
            if lab and lab not in labels:
                labels.append(lab)
        return labels

    def cycle_explore(
        self,
        steps: Optional[List[str]] = None,
        ask_if_stuck: bool = True,
        speak: bool = False,
    ) -> Dict[str, Any]:
        """Exploration autonome : chaque outil = inhibition + mémoire + exposant."""

        def _cap() -> Dict[str, Any]:
            return tool_see(auto_tune=True)

        def _rec(seconds: float) -> Dict[str, Any]:
            return _record_wav(seconds)

        out = self.autonomy.explore_cycle(
            capture_fn=_cap,
            record_fn=_rec,
            mic_summary_fn=mic_summary,
            mic_set_fn=lambda p: mic_set_percent(MIC_CAPTURE_CTRL, int(p), capture=True),
            steps=steps,
            ask_if_stuck=ask_if_stuck,
        )
        if speak and out.get("utterance"):
            tool_speak(str(out["utterance"]))
        return {"ok": True, "result": out}

    def cycle_autonomy_tool(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        """Exécute un seul outil d'autonomie (toujours via mémoire)."""
        name = (name or "").strip().lower()
        a = self.autonomy
        if name in ("probe", "probe_sensors"):
            r = a.probe_sensors()
        elif name in ("body", "body_map"):
            r = a.body_map()
        elif name in ("look", "look_around"):
            r = a.look_around(lambda: tool_see(auto_tune=True))
        elif name in ("listen", "listen_ambient"):
            r = a.listen_ambient(_record_wav, float(kwargs.get("seconds") or 2.5))
        elif name in ("reach", "reach_local"):
            r = a.reach_local()
        elif name == "wonder":
            r = a.wonder()
        elif name == "correlate":
            r = a.correlate()
        elif name in ("experiment", "experiment_safe"):
            r = a.experiment_safe(
                mic_summary,
                lambda p: mic_set_percent(MIC_CAPTURE_CTRL, int(p), capture=True),
            )
        elif name in ("craft", "craft_tool"):
            r = a.craft_tool(str(kwargs.get("idea") or ""))
        elif name in ("ask", "ask_when_stuck"):
            r = a.ask_when_stuck(str(kwargs.get("question") or "Je suis bloqué — aide-moi."))
        else:
            return {"ok": False, "error": f"unknown autonomy tool: {name}"}
        if kwargs.get("speak") and r.get("utterance"):
            tool_speak(str(r["utterance"]))
        return {"ok": True, "result": r}

    def auditory_corrections_from_memory(self) -> List[Tuple[str, str, Any]]:
        """Paires (entendu, voulu, entry) issues UNIQUEMENT du memory_index."""
        out: List[Tuple[str, str, Any]] = []
        for e in self.ms.entries.values():
            tags = {t.lower() for t in (e.inhibition_tags or [])}
            data = e.data or ""
            if "correction_auditive" not in tags and "correction auditive" not in data.lower():
                continue
            pair = parse_auditory_correction(data)
            if pair:
                out.append((pair[0], pair[1], e))
        # Plus long « entendu » d'abord (évite sous-match)
        out.sort(key=lambda x: -len(x[0]))
        return out

    def repair_heard_from_memory(self, text: str) -> Tuple[str, Optional[str], List[str]]:
        """
        Corrige ce qui a été entendu en consultant les mémoires
        « Correction auditive: « … » → « … » » — pas une table dans le .py.
        """
        raw = (text or "").strip()
        if not raw:
            return raw, None, []
        t = raw
        used: List[str] = []
        note = None
        low = t.lower()
        for heard, wanted, entry in self.auditory_corrections_from_memory():
            h = heard.strip()
            if not h:
                continue
            if h.lower() in low:
                t2 = re.sub(re.escape(h), wanted, t, count=1, flags=re.I)
                if t2 != t:
                    t = t2
                    low = t.lower()
                    used.append(entry.id)
                    note = f"mémoire {entry.id}: « {heard} » → « {wanted} »"
                    try:
                        entry.reinforce(1, f"correction STT appliquée sur: {raw[:80]}")
                    except Exception:
                        entry.exposant = min(10, int(entry.exposant) + 1)
        if used:
            self.ms.save()
        return t, note, used

    def learn_auditory_correction(self, heard: str, wanted: str, exposant: int = 8) -> Any:
        """Enregistre une nouvelle correction auditive DANS le memory_index."""
        heard = (heard or "").strip()
        wanted = (wanted or "").strip()
        if not heard or not wanted or heard.lower() == wanted.lower():
            return None
        # Éviter doublon exact
        for h, w, e in self.auditory_corrections_from_memory():
            if h.lower() == heard.lower() and w.lower() == wanted.lower():
                try:
                    e.reinforce(1, "ré-enseignement correction auditive")
                except Exception:
                    e.exposant = min(10, int(e.exposant) + 1)
                self.ms.save()
                return e
        return self.ms.create(
            "O",
            "P",
            exposant,
            f"Correction auditive: « {heard} » → « {wanted} »",
            source="human",
            inhibition_tags=["correction_auditive", "stt", "ouie"],
            action_context="entendre / STT",
            consequence="Sans cette mémoire je confonds les mots entendus",
            human_feedback="enseignement tuteur",
        )

    def _init_blank(self) -> None:
        INDEX.parent.mkdir(parents=True, exist_ok=True)
        blank = {
            "schema": "MemorySystemAI/v1",
            "version": "1.0",
            "generated": dt.datetime.now().isoformat(),
            "stats": {"total": 0},
            "entries": [],
        }
        INDEX.write_text(json.dumps(blank, ensure_ascii=False, indent=2), encoding="utf-8")
        if ASK.exists():
            ASK.unlink()
        if VISUAL_DB.exists():
            VISUAL_DB.unlink()
        if VOICE_DB.exists():
            VOICE_DB.unlink()
        log("blank memory_index created")

    def _seed_bootstrap(self) -> None:
        for fund, state, exp, data in BOOTSTRAP:
            self.ms.create(fund, state, exp, data, source="bootstrap")
        self.ms.save()
        log(f"bootstrap seeded ({len(BOOTSTRAP)} meta entries)")

    def memories_matching_action(self, action_text: str, min_exp: int = THRESHOLD_INJECT) -> List[Any]:
        """Mémoires dont les inhibition_tags matchent l'action (cœur MemorySystemAI)."""
        out = []
        for e in self.ms.entries.values():
            if e.exposant < min_exp:
                continue
            if e.matches_tags(action_text):
                out.append(e)
        return out

    def request_human(self, question: str, context: str = "") -> Dict[str, Any]:
        """
        Poser une question à l'humain.
        La norme « ne pas harceler si pas de réponse » vit dans memory_index
        (mémoire C/N à exposant élevé + tags), pas dans un rate-limit Python.
        """
        existing = _read_ask()

        # Relancer alors qu'une question attend déjà → action « harceler »
        if existing and existing.get("status") == "pending" and existing.get("question"):
            matched = self.memories_matching_action(ASK_HARASS_ACTION)
            inhib: List[str] = []
            for e in matched:
                msg = e.inhibition_message(ASK_HARASS_ACTION)
                if msg:
                    inhib.append(msg)
                elif e.exposant >= THRESHOLD_BLOCK:
                    inhib.append(f"[BLOCK exposant {e.exposant}] {e.data}")
                else:
                    inhib.append(f"[ALERT exposant {e.exposant}] {e.data}")
                # Renforcement par expérience : j'ai ressenti l'inhibition
                try:
                    e.reinforce(1, "tentative de relance sans attendre la réponse humaine")
                except Exception:
                    e.exposant = min(10, int(e.exposant) + 1)
            if matched:
                self.ms.save()
                self.learn_perception(
                    "C",
                    "Expérience: je voulais relancer l'humain sans sa réponse — "
                    "ma mémoire m'inhibe (ne pas harceler).",
                    "N",
                    7,
                )
                # L'utterance vient de la mémoire, pas d'une phrase figée dans le code
                top = max(matched, key=lambda x: x.exposant)
                hint = (top.data or "").strip()
                if len(hint) > 220:
                    hint = hint[:217] + "…"
                log(f"ask inhibited by memory {[e.id for e in matched]}: {question[:80]!r}")
                return {
                    "ok": True,
                    "pending": True,
                    "reused": True,
                    "inhibited": True,
                    "question": existing.get("question"),
                    "existing": existing,
                    "inhibitions": inhib,
                    "memory_ids": [e.id for e in matched],
                    "utterance_hint": hint,
                }
            # Pas encore de mémoire sur ce sujet → l'organisme ne « sait » pas s'abstenir
            # (il pourra l'apprendre). On n'écrase quand même pas la boîte : canal unique.
            log(f"ask pending kept (no social memory yet): {question[:80]!r}")
            return {
                "ok": True,
                "pending": True,
                "reused": True,
                "inhibited": False,
                "question": existing.get("question"),
                "existing": existing,
                "inhibitions": [],
                "utterance_hint": existing.get("question"),
            }

        # Première demande (rien en attente) : autorisée — ce n'est pas du harcèlement
        ask = tool_ask_human(question, context=context)
        ask["inhibitions"] = []
        return ask

    def memory_only_inhibition(self, action_text: str) -> List[str]:
        """
        Inhibition via mémoires à tags (MemorySystemAI) — pas le chevauchement
        de mots sur toutes les mémoires e>=7 (sinon « Vincent » bloquait tout).
        """
        msgs: List[str] = []
        for e in self.ms.entries.values():
            if e.exposant < THRESHOLD_INJECT:
                continue
            if not e.inhibition_tags:
                continue
            if not e.matches_tags(action_text):
                continue
            msg = e.inhibition_message(action_text)
            if msg:
                msgs.append(msg)
            elif e.exposant >= THRESHOLD_BLOCK:
                msgs.append(f"[BLOCK exposant {e.exposant}] {e.data}")
            else:
                msgs.append(f"[ALERT exposant {e.exposant}] {e.data}")
        return msgs

    def inhibition_reason(self, action_text: str) -> Optional[Dict[str, Any]]:
        """Mémoire qui bloque vraiment (tags + e>=9), pour une utterance claire."""
        best = None
        for e in self.ms.entries.values():
            if e.exposant < THRESHOLD_BLOCK:
                continue
            if not e.inhibition_tags or not e.matches_tags(action_text):
                continue
            if best is None or e.exposant > best.exposant:
                best = e
        if not best:
            return None
        return {
            "id": best.id,
            "exposant": best.exposant,
            "data": (best.data or "").strip(),
            "tags": list(best.inhibition_tags or []),
        }

    @staticmethod
    def _content_tokens(text: str, min_len: int = 4) -> List[str]:
        """Tokens utiles — pas de stopwords, pas de sous-chaînes parasites (es⊂Electrons)."""
        stop = {
            "alors", "avec", "bien", "bonjour", "cela", "cette", "comme", "comment",
            "dans", "donc", "elle", "elles", "est", "etes", "etre", "fait", "fais",
            "leur", "mais", "merci", "mes", "moi", "mon", "notre", "nous", "oui",
            "non", "pas", "plus", "pour", "quoi", "salut", "sans", "sont", "sur",
            "ton", "tous", "tout", "tres", "une", "vais", "vers", "vos", "votre",
            "vous", "yes", "the", "and", "qui", "que", "des", "les", "aux", "par",
            "ces", "ses", "son", "sa", "du", "au", "la", "le", "un", "de", "en",
            "ce", "ca", "ça", "il", "je", "tu", "on", "ne", "se", "si", "ou", "où",
            "ai", "as", "a", "ont", "ete", "été", "cest", "qu", "d", "l", "n", "m",
            "humain", "enseigne", "reponse", "réponse", "integree", "intégrée",
            "message", "recu", "reçu", "entendu", "percu", "perçu",
        }
        raw = re.findall(r"[a-zàâäéèêëïîôùûüç0-9]{2,}", (text or "").lower())
        out = []
        for t in raw:
            if t in stop or len(t) < min_len:
                continue
            out.append(t)
        return out

    @staticmethod
    def _word_set(text: str) -> set:
        return set(re.findall(r"[a-zàâäéèêëïîôùûüç0-9]{2,}", (text or "").lower()))

    def recall(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        q_toks = self._content_tokens(query, min_len=4)
        # Si la question n'a aucun ancrage (salut / qui es tu), ne pas injecter de faits lourds
        scored = []
        for e in self.ms.entries.values():
            data_l = (e.data or "").lower()
            # Poubelle : vieux "yes" / réponses génériques
            if re.search(r"réponse humaine intégrée:\s*(yes|no|oui|non|ok|test)\s*$", data_l):
                continue
            words = self._word_set(f"{e.data} {' '.join(e.inhibition_tags or [])}")
            score = 0.0
            hits = 0
            for tok in q_toks:
                if tok in words:  # mot entier, pas sous-chaîne
                    hits += 1
                    score += 1.2
                    if len(tok) > 8:
                        score += 1.5  # noms propres longs (SatRadio…)
            if hits == 0:
                continue
            score += e.exposant / 12.0
            src = (e.source or "").lower()
            if src == "human" or data_l.startswith("fait enseigné") or "réponse humaine intégrée" in data_l:
                score += 2.0
            if data_l.startswith(("message reçu:", "perçu:", "interprétation (", "inconnu rencontré:", "entendu:", "vu:")):
                score -= 2.5
            if score > 1.0:
                scored.append((score, hits, e))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        out = []
        for score, hits, e in scored[:limit]:
            out.append({
                "id": e.id,
                "fundamental": e.fundamental,
                "state": e.state,
                "exposant": e.exposant,
                "data": e.data,
                "score": round(score, 2),
                "hits": hits,
                "source": e.source,
            })
        return out

    def learn_perception(self, fundamental: str, data: str, state: str = "X", exposant: int = 5) -> None:
        if exposant >= THRESHOLD_RECORD:
            self.ms.create(fundamental, state, exposant, data[:500], source="experience")

    def learn_from_feedback(self, text: str, positive: bool) -> None:
        delta = 2 if positive else 3
        state = "P" if positive else "N"
        # reinforce most recent related or create
        self.ms.create("C", state, 5 + delta, f"Feedback humain: {text[:300]}", source="human")

    def usable_memory_answer(self, perception: str, memories: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Choisit une mémoire apprise assez pertinente pour répondre SANS reconsulter Kimi."""
        skip_prefixes = (
            "message reçu:",
            "feedback humain:",
            "interprétation (",
            "inconnu rencontré:",
            "perçu:",
            "entendu:",
            "vu:",
            "scène vue:",
            "visage reconnu:",
            "voix reconnue:",
            "voix inconnue",
        )
        anchors = self._content_tokens(perception, min_len=4)
        # Pas d'ancrage fort → pas de rappel mémoire (évite Starlink sur « qui es tu »)
        if not anchors:
            return None
        candidates = []
        for m in memories:
            data = (m.get("data") or "").strip()
            low = data.lower()
            if any(low.startswith(p) for p in skip_prefixes):
                continue
            # Ignorer réponses humaines génériques
            body = data
            for pref in ("fait enseigné par l'humain:", "réponse humaine intégrée:"):
                if low.startswith(pref):
                    body = data.split(":", 1)[-1].strip()
                    break
            if body.lower() in {"yes", "no", "oui", "non", "ok", "test", "y", "n"}:
                continue
            words = self._word_set(body)
            hit = sum(1 for t in anchors if t in words)
            # OBLIGATOIRE : au moins 1 mot-contenu en commun (mot entier)
            if hit < 1:
                continue
            score = float(m.get("score") or 0)
            exp = int(m.get("exposant") or 0)
            hits_recall = int(m.get("hits") or hit)
            if score < 1.2 and exp < THRESHOLD_INJECT:
                continue
            # Faits WiFi/Starlink : exiger un ancrage thématique explicite
            topic = {"starlink", "satradio", "satradioelectronslibres", "wifi", "wlan", "ssid"}
            mem_topic = bool(words & topic) or "satradio" in low.replace(" ", "")
            if mem_topic and not (set(anchors) & topic) and not any(
                "satradio" in a or "starlink" in a or a == "wifi" for a in anchors
            ):
                continue
            weight = score + exp / 12.0 + hit * 2.0 + hits_recall
            if exp >= THRESHOLD_INJECT:
                weight += 1.5
            if low.startswith("fait enseigné") or "réponse humaine intégrée" in low:
                weight += 1.5
            # Exiger 2 hits si le fait est long (évite 1 mot faible)
            if len(body) > 80 and hit < 2 and not (set(anchors) & topic):
                weight -= 3
                if hit < 2:
                    continue
            candidates.append((weight, m))
        if not candidates:
            return None
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]

    def interpret_with_tools(
        self,
        perception: str,
        channel: str,
        external_interpretation: Optional[str] = None,
        external_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Boucle cognitive :
        1) rappel mémoire (prioritaire si fait déjà appris)
        2) sinon consulter LLM (outil) — Puter/Kimi puis Ollama
           ou utiliser une interprétation fournie (ex. Puter.js nursery)
        3) si encore insuffisant → demander humain
        4) enregistrer ce qui est appris
        """
        inhib = self.memory_only_inhibition(perception)
        if any("BLOCK" in m for m in inhib):
            why = self.inhibition_reason(perception)
            if why:
                snippet = why["data"]
                if len(snippet) > 180:
                    snippet = snippet[:177] + "…"
                utter = (
                    f"Je m'abstiens de poursuivre cette action "
                    f"(« {perception[:80]} »). "
                    f"Ma mémoire {why['id']} (e{why['exposant']}) m'inhibe : {snippet}"
                )
            else:
                utter = (
                    f"Je m'abstiens de poursuivre « {perception[:80]} » — "
                    f"inhibition forte issue de mes mémoires."
                )
            return {
                "action": "inhibit",
                "utterance": utter,
                "inhibitions": inhib,
                "inhibition_of": why,
                "source": "memory",
            }

        memories = self.recall(perception, limit=16)
        known = "\n".join(
            f"- [{m['fundamental']}/{m['state']}/e{m['exposant']}] {m['data']}" for m in memories
        ) or "(aucune mémoire pertinente — je suis encore presque vide)"

        # Mémoire d'abord — même si Kimi a proposé quelque chose côté navigateur
        # Exception: capture caméra brute (bytes) → toujours consulter un outil, pas un fait WiFi hors sujet
        skip_memory = (
            channel == "V"
            and "caméra" in perception.lower()
            and ("bytes" in perception.lower() or "frame" in perception.lower())
        )
        memorized = None if skip_memory else self.usable_memory_answer(perception, memories)
        if memorized and channel in ("O", "I", "C", "V"):
            # Ne pas répondre à une perception V avec une mémoire purement C hors ancrage fort
            if channel == "V" and memorized.get("fundamental") == "C" and float(memorized.get("score") or 0) < 4:
                memorized = None
        if memorized and channel in ("O", "I", "C", "V"):
            data = memorized["data"]
            low = data.lower()
            if low.startswith("réponse humaine intégrée:"):
                data = data.split(":", 1)[-1].strip()
            elif low.startswith("fait enseigné par l'humain:"):
                data = data.split(":", 1)[-1].strip()
            return {
                "action": "recall",
                "utterance": data,
                "memories": memories,
                "inhibitions": inhib,
                "source": "memory",
                "recalled_id": memorized.get("id"),
            }

        if external_interpretation and external_interpretation.strip():
            interpretation = external_interpretation.strip()
            if "JE NE SAIS PAS" in interpretation.upper():
                ask = self.request_human(perception, context=known)
                self.learn_perception(
                    channel if channel in FUNDAMENTALS else "I",
                    f"Inconnu rencontré: {perception[:240]}",
                    "X",
                    5,
                )
                if ask.get("inhibited"):
                    return {
                        "action": "wait",
                        "utterance": ask.get("utterance_hint")
                        or "J'attends déjà une réponse de toi — je ne te relance pas.",
                        "ask": ask,
                        "memories": memories,
                        "inhibitions": ask.get("inhibitions") or inhib,
                        "source": "ask-inhibited",
                        "llm_source": external_source or "external",
                    }
                return {
                    "action": "ask",
                    "utterance": "Je ne connais pas encore cela. J'ai besoin d'un humain ou d'une autre source.",
                    "ask": ask,
                    "memories": memories,
                    "source": "ask-human",
                    "llm_source": external_source or "external",
                }
            self.learn_perception("I", f"Interprétation ({channel}): {interpretation[:400]}", "X", 6)
            self.learn_perception(
                channel if channel in FUNDAMENTALS else "I",
                f"Perçu: {perception[:300]}",
                "X",
                5,
            )
            return {
                "action": "interpret",
                "utterance": interpretation,
                "memories": memories,
                "inhibitions": inhib,
                "llm_source": external_source or "external",
                "source": "llm-tool",
            }

        system = (
            "Tu es un OUTIL de consultation pour un organisme mémoire quasi vide. "
            "Tu n'es PAS l'organisme. Tu aides à INTERPRÉTER une perception. "
            "Réponds en français, factuel, court (2-4 phrases max). "
            "Si les mémoires ci-dessous contiennent déjà la réponse factuelle, reformule UNIQUEMENT à partir d'elles. "
            "Pour une salutation / politesse / « qui es-tu » : réponds brièvement sans inventer de faits du monde. "
            "JE NE SAIS PAS uniquement pour une question FACTUELLE précise absente des mémoires "
            "(pas pour bonjour, salut, comment ça va).\n"
            f"Mémoires déjà connues de l'organisme:\n{known}"
        )
        consult = tool_consult_llm(
            prompt=f"Canal sensoriel={channel}. Perception brute:\n{perception}\n\nQue puis-je en comprendre / apprendre ?",
            system=system,
        )

        text_up = (consult.get("text") or "").upper()
        is_jnsp = "JE NE SAIS PAS" in text_up
        # Salutations : ne jamais escalader vers ask_human
        social = bool(re.search(
            r"\b(bonjour|salut|hello|coucou|bonsoir|merci|ça\s*va|ca\s*va|qui\s+es[- ]?tu|comment\s+tu\s+t)\b",
            perception,
            re.I,
        ))
        if social and (not consult.get("ok") or is_jnsp):
            return {
                "action": "interpret",
                "utterance": (
                    "Bonjour. Je suis un organisme mémoire encore presque vide : "
                    "j'apprends par ce que tu me montres, me dis, et me corriges."
                ),
                "memories": memories,
                "inhibitions": inhib,
                "source": "social-default",
            }

        if not consult.get("ok") or is_jnsp:
            human = tool_read_human_answer(for_perception=perception)
            if human:
                self.learn_perception("C", f"Réponse humaine intégrée: {human}", "P", 8)
                return {
                    "action": "human",
                    "utterance": human,
                    "memories": memories,
                    "source": "human",
                }
            ask = self.request_human(perception, context=known)
            self.learn_perception(channel if channel in FUNDAMENTALS else "I", f"Inconnu rencontré: {perception[:240]}", "X", 5)
            if ask.get("inhibited"):
                return {
                    "action": "wait",
                    "utterance": ask.get("utterance_hint")
                    or "J'attends déjà une réponse de toi — je ne te relance pas.",
                    "ask": ask,
                    "memories": memories,
                    "inhibitions": ask.get("inhibitions") or inhib,
                    "source": "ask-inhibited",
                }
            return {
                "action": "ask",
                "utterance": "Je ne connais pas encore cela. J'ai besoin d'un humain ou d'une autre source.",
                "ask": ask,
                "memories": memories,
                "source": "ask-human",
            }

        interpretation = consult["text"]
        self.learn_perception("I", f"Interprétation ({channel}): {interpretation[:400]}", "X", 6)
        self.learn_perception(channel if channel in FUNDAMENTALS else "I", f"Perçu: {perception[:300]}", "X", 5)

        return {
            "action": "interpret",
            "utterance": interpretation,
            "memories": memories,
            "inhibitions": inhib,
            "llm_source": consult.get("source"),
            "source": "llm-tool",
        }

    def cycle_hear(self, seconds: float = 4.0, speak: bool = True, auto_tune: bool = True) -> Dict[str, Any]:
        heard = tool_hear(seconds, auto_tune=auto_tune)
        if not heard.get("ok"):
            return {"ok": False, "error": heard.get("error")}
        text = heard.get("text") or ""
        wav = heard.get("wav") or ""
        sensor = heard.get("sensor") or {}
        level = heard.get("level") or {}
        stt_raw = text

        # Correction via mémoires « Correction auditive » (memory_index), pas table .py
        if text:
            repaired, stt_note, mem_ids = self.repair_heard_from_memory(text)
            if repaired != text:
                text = repaired
                self.learn_perception(
                    "O",
                    f"Expérience: « {stt_raw} » entendu au micro, corrigé en « {text} » "
                    f"par mémoires {mem_ids} ({stt_note or ''})",
                    "P",
                    6,
                )
                log(f"stt repair(memory): {stt_raw!r} → {text!r} via {mem_ids}")

        # Expérience capteur : j'ai adapté mon oreille (gain) selon ce que j'ai mesuré
        if sensor.get("adjusted"):
            before = (sensor.get("before") or {}).get("capture_percent")
            after = (sensor.get("after") or {}).get("capture_percent")
            why = "saturation" if (sensor.get("level") or {}).get("too_loud") else "signal faible"
            self.learn_perception(
                "O",
                f"Expérience micro: niveau {why} — Capture {before}%→{after}% "
                f"rms={level.get('rms')} peak={level.get('peak')} "
                f"(j'adapte mon gain pour mieux entendre)",
                "P" if text else "X",
                7 if text else 6,
            )
        elif level.get("ok") and not text and (level.get("too_quiet") or level.get("clipping")):
            self.learn_perception(
                "O",
                f"Expérience micro: STT vide avec rms={level.get('rms')} "
                f"peak={level.get('peak')} clipping={level.get('clipping')} — "
                "je dois encore apprendre à régler mon oreille",
                "N",
                6,
            )

        # Empreinte vocale (même sans STT — inscription / reconnaissance locuteur)
        voice_info: Dict[str, Any] = {"ok": False}
        if wav and Path(wav).exists():
            try:
                voice_info = self.voice.process_wav(wav, transcript=text)
            except Exception as e:
                voice_info = {"ok": False, "error": str(e)}
                log(f"voice_memory error: {e}")

        if voice_info.get("recognized"):
            r = voice_info["recognized"]
            self.learn_perception(
                "O",
                f"Voix reconnue: {r.get('label')} [{r.get('id')}] "
                f"similarité={r.get('score')} clip={Path(wav).name}",
                "P",
                min(10, int(r.get("exposant") or 6)),
            )
        elif voice_info.get("unknown"):
            u = voice_info["unknown"]
            self.learn_perception(
                "O",
                f"Voix inconnue rencontrée: {u.get('id')} clip={u.get('clip')} — à identifier",
                "X",
                6,
            )

        if not text:
            note = "silence / STT vide"
            utter = None
            if voice_info.get("recognized"):
                lab = voice_info["recognized"].get("label") or voice_info["recognized"].get("id")
                utter = f"J'entends une voix que je reconnais : {lab}. (mots non déchiffrés)"
                note = "voix reconnue sans STT"
            elif voice_info.get("unknown"):
                utter = "J'entends une voix nouvelle — dis-moi qui tu es, j'apprendrai ton empreinte."
                note = "voix inconnue sans STT"
            elif level.get("clipping") or level.get("too_loud"):
                utter = "J'entends quelque chose mais mon micro sature — j'essaie de baisser mon gain."
                note = "micro saturé"
            elif level.get("too_quiet"):
                utter = "Le signal micro est trop faible — j'essaie d'augmenter mon gain."
                note = "micro trop faible"
            if speak and utter:
                tool_speak(utter)
            return {
                "ok": True,
                "heard": "",
                "note": note,
                "wav": wav,
                "voice": voice_info,
                "sensor": sensor,
                "level": level,
                "result": {"utterance": utter, "source": "mic-sensor"} if utter else None,
            }

        # Même boucle que le texte (identité / corrections / crible mémoire)
        wrapped = self.cycle_text(text, speak=False)
        result = wrapped.get("result") or {}
        # Préfixer reconnaissance locuteur
        if voice_info.get("recognized"):
            lab = voice_info["recognized"].get("label") or voice_info["recognized"].get("id")
            result["utterance"] = f"Je reconnais ta voix, {lab}. {result.get('utterance') or ''}".strip()
            if result.get("source") in ("llm-tool", "memory"):
                result["source"] = "voice+" + str(result.get("source"))
            result["voice"] = voice_info
        elif voice_info.get("unknown"):
            result["utterance"] = (
                f"{result.get('utterance') or ''} "
                f"(Voix nouvelle pour moi — dis « c'est moi Vincent » pour lier l'empreinte.)"
            ).strip()
            result["voice"] = voice_info
        else:
            result["voice"] = voice_info
        if speak:
            tool_speak(result.get("utterance", ""))
        return {
            "ok": True,
            "heard": text,
            "result": result,
            "voice": voice_info,
            "wav": wav,
            "sensor": sensor,
            "level": level,
        }

    def cycle_capture(self, auto_tune: bool = True) -> Dict[str, Any]:
        """Capture seule (+ auto capteurs) — pour affichage immédiat UI."""
        seen = tool_see(auto_tune=auto_tune)
        if not seen.get("ok"):
            return seen
        path = str(seen.get("path") or "")
        name = Path(path).name if path else ""
        return {
            "ok": True,
            "path": path,
            "preview": f"/snapshot/{name}" if name else None,
            "sensor": seen.get("sensor"),
            "frame": seen,
        }

    def cycle_see(self, speak: bool = False, path: Optional[str] = None) -> Dict[str, Any]:
        # Réutiliser une capture déjà affichée (évite double flash + preview immédiate)
        if path and Path(path).exists():
            seen = {
                "ok": True,
                "path": path,
                "bytes": Path(path).stat().st_size,
                "raw": f"frame reuse ({Path(path).stat().st_size} bytes)",
                "sensor": {"adjusted": False, "reused": True},
            }
        else:
            seen = tool_see(auto_tune=True)
        if not seen.get("ok"):
            return seen
        path = str(seen.get("path") or "")
        raw = seen.get("raw", "")
        self.learn_perception("V", f"Vu: capture caméra {path} ({raw})", "X", 5)

        # Auto-gestion capteur V (luminosité / gamma / exposition)
        sensor = seen.get("sensor") or {}
        if sensor.get("adjusted"):
            lum = sensor.get("luminance") or {}
            lum_after = sensor.get("luminance_after") or {}
            applied = sensor.get("applied") or []
            names = ", ".join(
                f"{a.get('name')}={a.get('value')}" for a in applied if isinstance(a, dict)
            )
            self.learn_perception(
                "V",
                f"Auto-réglage capteur caméra (scène trop sombre/claire): "
                f"luminosité {lum.get('center')}/{lum.get('mean')} → "
                f"{lum_after.get('center') or '?'} ; réglages: {names or sensor.get('proposed')}",
                "P",
                6,
            )

        # ── Mémoire visuelle native (empreintes) avant / en plus du LLM ──
        visual_info: Dict[str, Any] = {"ok": False}
        try:
            visual_info = self.visual.process_snapshot(path)
        except Exception as e:
            visual_info = {"ok": False, "error": str(e)}
            log(f"visual_memory error: {e}")

        recog_bits: List[str] = []
        for r in visual_info.get("recognized") or []:
            label = r.get("label") or r.get("id")
            score = r.get("score")
            exp = r.get("exposant")
            recog_bits.append(f"{label} (similarité {score}, exposant {exp})")
            self.learn_perception(
                "V",
                f"Visage reconnu: {label} [{r.get('id')}] similarité={score} snapshot={Path(path).name}",
                "P",
                min(10, int(exp or 6)),
            )
        for u in visual_info.get("unknown") or []:
            self.learn_perception(
                "V",
                f"Visage inconnu rencontré: {u.get('id')} snapshot={u.get('snapshot')} — à identifier",
                "X",
                6,
            )

        system = (
            "Tu es un OUTIL de vision pour un organisme mémoire quasi vide. "
            "Tu n'es PAS l'organisme. Décris CE QUE TU VOIS dans l'image, en français, "
            "factuel et court (2-5 phrases). "
            "Si tu vois un visage / personne / objet / lieu, dis-le clairement. "
            "Si l'image est noire / floue / illisible : dis exactement JE NE SAIS PAS."
        )
        prompt = (
            "Voici une photo prise par la webcam du portable-organisme. "
            "Que vois-tu ? Qu'est-ce que l'organisme peut en apprendre ?"
        )
        if recog_bits:
            prompt += (
                "\nContexte mémoire visuelle déjà connue (ne contredis pas sans raison) : "
                + "; ".join(recog_bits)
            )
        consult = tool_consult_vision(path, prompt, system)

        if consult.get("ok") and "JE NE SAIS PAS" not in (consult.get("text") or "").upper():
            interpretation = consult["text"]
            self.learn_perception("I", f"Interprétation (V): {interpretation[:400]}", "X", 6)
            self.learn_perception("V", f"Scène vue: {interpretation[:300]}", "X", 6)
            # Préfixer reconnaissance native si on a un label
            if recog_bits:
                names = ", ".join(
                    (r.get("label") or r.get("id") or "?")
                    for r in (visual_info.get("recognized") or [])
                )
                utterance = f"Je reconnais : {names}. {interpretation}"
            elif visual_info.get("unknown"):
                utterance = (
                    f"{interpretation} "
                    f"(Visage nouveau pour moi — dis-moi qui c'est, j'apprendrai le lien.)"
                )
            else:
                utterance = interpretation
            result = {
                "action": "interpret",
                "utterance": utterance,
                "source": "llm-tool" if not recog_bits else "visual+llm",
                "llm_source": consult.get("source"),
                "vision": True,
                "visual": visual_info,
            }
        elif recog_bits:
            # Vision LLM fail mais empreinte connue → répondre depuis mémoire visuelle
            names = ", ".join(
                (r.get("label") or r.get("id") or "?")
                for r in (visual_info.get("recognized") or [])
            )
            utterance = f"Je reconnais ce visage : {names}."
            result = {
                "action": "recall",
                "utterance": utterance,
                "source": "visual-memory",
                "llm_source": consult.get("source") or consult.get("error"),
                "vision": True,
                "visual": visual_info,
            }
        else:
            # Pas d'image comprise → demander humain (inhibé si déjà pending / spam)
            q = "J'ai capturé une image caméra mais je ne sais pas encore la décrire. Que vois-tu ?"
            if visual_info.get("unknown"):
                q = "Je vois un visage que je ne connais pas encore. Qui est-ce ?"
            ask = self.request_human(q, context=path)
            if ask.get("inhibited"):
                result = {
                    "action": "wait",
                    "utterance": ask.get("utterance_hint")
                    or (
                        "J'ai regardé, mais j'attends déjà une réponse de toi — "
                        "je ne te relance pas sur Telegram."
                    ),
                    "ask": ask,
                    "source": "ask-inhibited",
                    "llm_source": consult.get("source") or consult.get("error"),
                    "vision": True,
                    "visual": visual_info,
                }
            else:
                result = {
                    "action": "ask",
                    "utterance": (
                        "J'ai regardé (photo prise) mais je ne reconnais pas encore clairement. "
                        "Dis-moi qui c'est / ce que tu vois — j'apprendrai le lien visage→identité."
                    ),
                    "ask": ask,
                    "source": "ask-human",
                    "llm_source": consult.get("source") or consult.get("error"),
                    "vision": True,
                    "visual": visual_info,
                }

        if speak:
            tool_speak(result.get("utterance", ""))
        result["frame"] = seen
        result["sensor"] = sensor
        # URL locale pour l'UI kiosk
        name = Path(path).name if path else ""
        result["preview"] = f"/snapshot/{name}" if name else None
        return {"ok": True, "result": result}

    def _camera_status(self) -> Dict[str, Any]:
        listed = camera_list_controls()
        last_preview = None
        try:
            snaps = sorted(SNAPS.glob("v_*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
            if snaps:
                last_preview = f"/snapshot/{snaps[0].name}"
        except Exception:
            pass
        if not listed.get("ok"):
            return {
                "ok": False,
                "error": listed.get("error"),
                "present": os.path.exists("/dev/video0"),
                "last_preview": last_preview,
            }
        return {
            "ok": True,
            "present": True,
            "device": listed.get("device"),
            "controls": camera_summary(listed.get("controls") or {}),
            "auto_tune": True,
            "last_preview": last_preview,
        }

    def cycle_text(
        self,
        text: str,
        speak: bool = False,
        external_interpretation: Optional[str] = None,
        external_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Entrée texte = comme une perception 'I' / message humain (outil de liaison)."""
        text = (text or "").strip()
        if not text:
            return {"ok": False, "error": "empty"}
        repaired, _stt_note, _mem_ids = self.repair_heard_from_memory(text)
        if repaired != text:
            log(f"text repair(memory): {text!r} → {repaired!r}")
            text = repaired
        low = text.lower()
        # Enseignement explicite d'une correction auditive :
        # « quand tu entends X ça veut dire Y » / « X veut dire Y »
        m_corr = re.search(
            r"(?:quand\s+tu\s+entends|tu\s+entends|entendu)\s+[«\"]?(.+?)[»\"]?\s+"
            r"(?:ça\s+veut\s+dire|veut\s+dire|égal|=|→)\s+[«\"]?(.+?)[»\"]?\s*$",
            text,
            re.I,
        )
        if m_corr:
            self.learn_auditory_correction(m_corr.group(1).strip(), m_corr.group(2).strip(), 8)
        # Enseignement factuel humain → exposant fort (apprentissage réel)
        if (" est " in low or " = " in low) and len(text) > 20 and "?" not in text:
            self.learn_perception("C", f"Fait enseigné par l'humain: {text[:400]}", "P", 8)
        # Lien visage / voix → identité (mémoires sensorielles)
        visual_label = extract_identity_label(text)
        visual_person = None
        voice_person = None
        if visual_label:
            visual_person = self.visual.label_pending_or_last(visual_label, exposant=8)
            voice_person = self.voice.label_pending_or_last(visual_label, exposant=8)
            if visual_person:
                self.learn_perception(
                    "V",
                    f"Identité visuelle enseignée: {visual_person.get('label')} "
                    f"[{visual_person.get('id')}] (empreintes={len(visual_person.get('embeddings') or [])})",
                    "P",
                    8,
                )
                self.learn_perception(
                    "C",
                    f"Fait enseigné par l'humain: Le visage vu à la caméra est {visual_person.get('label')}.",
                    "P",
                    8,
                )
            if voice_person and (voice_person.get("embeddings") or voice_person.get("clips")):
                self.learn_perception(
                    "O",
                    f"Identité vocale enseignée: {voice_person.get('label')} "
                    f"[{voice_person.get('id')}] (empreintes={len(voice_person.get('embeddings') or [])})",
                    "P",
                    8,
                )
                self.learn_perception(
                    "C",
                    f"Fait enseigné par l'humain: La voix entendue au micro est {voice_person.get('label')}.",
                    "P",
                    8,
                )
        if any(x in low for x in ("bien", "bravo", "correct", "merci", "oui c'est ça")):
            self.learn_from_feedback(text, True)
        # Feedback négatif pendant une ask en attente → renforce les mémoires qui matchent
        elif any(x in low for x in ("non", "faux", "mal", "arrête", "erreur")) and "interdit texte" not in low:
            self.learn_from_feedback(text, False)
            pending = _read_ask()
            if pending and pending.get("status") == "pending":
                for e in self.memories_matching_action(ASK_HARASS_ACTION, min_exp=THRESHOLD_RECORD):
                    try:
                        e.reinforce(2, f"retour tuteur: {text[:120]}")
                        e.state = "N"
                        e.human_feedback = text[:200]
                    except Exception:
                        e.exposant = min(10, int(e.exposant) + 2)
                        e.state = "N"
                self.ms.save()
        self.learn_perception("C", f"Message reçu: {text[:300]}", "X", 5)
        result = self.interpret_with_tools(
            text,
            "C",
            external_interpretation=external_interpretation,
            external_source=external_source,
        )
        # Enseignement identité : prioritaire même si une autre mémoire inhibe la suite
        if visual_person or voice_person:
            bits = []
            if visual_person:
                result["visual_taught"] = {
                    "id": visual_person.get("id"),
                    "label": visual_person.get("label"),
                    "exposant": visual_person.get("exposant"),
                }
                bits.append(f"visage→{visual_person.get('label')} ({visual_person.get('id')})")
            if voice_person and (voice_person.get("embeddings") or voice_person.get("clips") or voice_person.get("seen_count")):
                result["voice_taught"] = {
                    "id": voice_person.get("id"),
                    "label": voice_person.get("label"),
                    "exposant": voice_person.get("exposant"),
                }
                bits.append(f"voix→{voice_person.get('label')} ({voice_person.get('id')})")
            if bits:
                result["utterance"] = (
                    "J'ai lié : " + " · ".join(bits) + ". Je m'en souviendrai."
                )
                result["source"] = "sensor-memory"
                result["action"] = "teach-identity"
        if speak:
            tool_speak(result.get("utterance", ""))
        return {"ok": True, "result": result}

    def status(self) -> Dict[str, Any]:
        pending = None
        if ASK.exists():
            try:
                pending = json.loads(ASK.read_text(encoding="utf-8"))
            except Exception:
                pending = {"error": "unreadable"}
        puter_ready = bool(_load_puter_token())
        vol = tool_volume_get()
        return {
            "role": "MemorySystemAI-organism",
            "not": "chatbot-with-text-rules",
            "memories": len(self.ms.entries),
            "bootstrap_only_meta": all(
                getattr(e, "source", "") == "bootstrap" for e in self.ms.entries.values()
            ),
            "tools": [
                "see", "hear", "speak", "volume", "camera", "mic",
                "consult_llm", "consult_puter_kimi", "ask_human",
                "visual_memory", "voice_memory",
                "autonomy:probe", "autonomy:look", "autonomy:listen",
                "autonomy:reach", "autonomy:wonder", "autonomy:correlate",
                "autonomy:experiment", "autonomy:craft", "autonomy:explore",
            ],
            "visual": self.visual.summary(),
            "voice": self.voice.summary(),
            "tts": {
                "piper": PIPER_BIN.exists() and PIPER_VOICE.exists(),
                "engine_pref": ["piper:siwis", "pico", "mbrola", "espeak"],
            },
            "camera_sensor": self._camera_status(),
            "mic_sensor": mic_summary(),
            "body_map": (
                self.autonomy._load_json(self.autonomy.body_path, {})
                if getattr(self, "autonomy", None)
                else {}
            ),
            "vision": {
                "provider": get_vision_provider(),
                "nvidia": {
                    "enabled": bool(_load_nvidia_token()),
                    "model": NVIDIA_VISION_MODEL,
                    "base": NVIDIA_BASE,
                },
                "puter": {
                    "enabled": puter_ready,
                    "model": PUTER_VISION_MODEL,
                },
            },
            "model_tool": PUTER_MODEL if puter_ready else OLLAMA_MODEL,
            "puter": {
                "enabled": puter_ready,
                "model": PUTER_MODEL,
                "browser_fallback": True,
                "docs": "https://developer.puter.com/ai/moonshotai/kimi-k3/",
            },
            "ask_pending": pending,
            "ask_social_memories": [
                {
                    "id": e.id,
                    "exposant": e.exposant,
                    "state": e.state,
                    "tags": list(e.inhibition_tags or []),
                    "data": (e.data or "")[:160],
                }
                for e in self.memories_matching_action(ASK_HARASS_ACTION, min_exp=THRESHOLD_RECORD)
            ],
            "camera": os.path.exists("/dev/video0"),
            "volume": {
                "percent": vol.get("percent"),
                "muted": vol.get("muted"),
            } if vol.get("ok") else {"error": vol.get("error")},
            "time": dt.datetime.now().isoformat(timespec="seconds"),
        }


ORG: Optional[Organism] = None
VOICE_STOP = threading.Event()
VOICE_THREAD: Optional[threading.Thread] = None


def start_voice_loop() -> Dict[str, Any]:
    global VOICE_THREAD
    if VOICE_THREAD and VOICE_THREAD.is_alive():
        return {"ok": True, "voice": True, "note": "already running"}
    VOICE_STOP.clear()

    def loop() -> None:
        while not VOICE_STOP.is_set():
            try:
                if ORG is not None:
                    ORG.cycle_hear(seconds=3.5, speak=True)
            except Exception as e:
                log(f"voice loop error: {e}")
            VOICE_STOP.wait(0.4)

    VOICE_THREAD = threading.Thread(target=loop, daemon=True, name="voice-loop")
    VOICE_THREAD.start()
    return {"ok": True, "voice": True}


def stop_voice_loop() -> Dict[str, Any]:
    VOICE_STOP.set()
    return {"ok": True, "voice": False}


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, obj: Any) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _bytes(self, code: int, data: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> Dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def _serve_ui(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/ui", "/ui/"):
            target = UI_INDEX
            ctype = "text/html; charset=utf-8"
        else:
            rel = path[len("/ui/") :] if path.startswith("/ui/") else path.lstrip("/")
            target = (UI_DIR / rel).resolve()
            if not str(target).startswith(str(UI_DIR.resolve())):
                self._json(403, {"error": "forbidden"})
                return
            if target.suffix == ".css":
                ctype = "text/css; charset=utf-8"
            elif target.suffix == ".js":
                ctype = "application/javascript; charset=utf-8"
            elif target.suffix == ".svg":
                ctype = "image/svg+xml"
            else:
                ctype = "application/octet-stream"
        if not target.exists():
            self._json(404, {"error": "ui missing", "path": str(target)})
            return
        self._bytes(200, target.read_bytes(), ctype)

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):  # noqa: N802
        assert ORG is not None
        path = self.path.split("?", 1)[0]
        if path in ("/", "/ui", "/ui/") or path.startswith("/ui/"):
            self._serve_ui()
            return
        if path.startswith("/status"):
            st = ORG.status()
            st["voice_loop"] = bool(VOICE_THREAD and VOICE_THREAD.is_alive() and not VOICE_STOP.is_set())
            st["ui"] = f"http://127.0.0.1:{PORT}/"
            self._json(200, st)
            return
        if path.startswith("/memories"):
            entries = [
                {
                    "id": e.id,
                    "fundamental": e.fundamental,
                    "state": e.state,
                    "exposant": e.exposant,
                    "data": e.data,
                    "source": e.source,
                }
                for e in ORG.ms.entries.values()
            ]
            self._json(200, {"count": len(entries), "entries": entries})
            return
        if path.startswith("/faces") or path.startswith("/visual"):
            self._json(200, ORG.visual.summary())
            return
        if path.startswith("/voices") or path.startswith("/speakers"):
            self._json(200, ORG.voice.summary())
            return
        if path.startswith("/ask"):
            if ASK.exists():
                self._json(200, json.loads(ASK.read_text(encoding="utf-8")))
            else:
                self._json(200, {"status": "none"})
            return
        if path.startswith("/volume"):
            self._json(200, tool_volume_get())
            return
        if path.startswith("/camera"):
            self._json(200, ORG._camera_status())
            return
        if path.startswith("/mic"):
            self._json(200, mic_summary())
            return
        if path.startswith("/vision"):
            self._json(
                200,
                {
                    "provider": get_vision_provider(),
                    "nvidia_ready": bool(_load_nvidia_token()),
                    "puter_ready": bool(_load_puter_token()),
                    "nvidia_model": NVIDIA_VISION_MODEL,
                    "puter_model": PUTER_VISION_MODEL,
                },
            )
            return
        if path.startswith("/snapshot/"):
            name = path.split("/snapshot/", 1)[-1]
            name = Path(name).name  # anti path traversal
            target = (SNAPS / name).resolve()
            if not str(target).startswith(str(SNAPS.resolve())) or not target.exists():
                self._json(404, {"error": "snapshot not found"})
                return
            self._bytes(200, target.read_bytes(), "image/jpeg")
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        global ORG
        data = self._body()
        if ORG is None:
            self._json(503, {"error": "organism not ready"})
            return
        if self.path.startswith("/perceive") or self.path.startswith("/chat"):
            text = str(data.get("text") or data.get("message") or "").strip()
            speak = bool(data.get("speak", False))
            ext = str(data.get("interpretation") or data.get("external_interpretation") or "").strip() or None
            src = str(data.get("llm_source") or data.get("external_source") or "").strip() or None
            self._json(
                200,
                ORG.cycle_text(
                    text,
                    speak=speak,
                    external_interpretation=ext,
                    external_source=src,
                ),
            )
            return
        if self.path.startswith("/capture"):
            self._json(200, ORG.cycle_capture(auto_tune=bool(data.get("auto_tune", True))))
            return
        if self.path.startswith("/see"):
            reuse = str(data.get("path") or "").strip() or None
            self._json(
                200,
                ORG.cycle_see(
                    speak=bool(data.get("speak", False)),
                    path=reuse,
                ),
            )
            return
        if self.path.startswith("/hear") or self.path.startswith("/listen"):
            self._json(
                200,
                ORG.cycle_hear(
                    seconds=float(data.get("seconds") or 4),
                    speak=bool(data.get("speak", True)),
                    auto_tune=bool(data.get("auto_tune", True)),
                ),
            )
            return
        if self.path.startswith("/explore") or self.path.startswith("/autonomy/cycle"):
            steps = data.get("steps")
            if isinstance(steps, str):
                steps = [s.strip() for s in steps.split(",") if s.strip()]
            if steps is not None and not isinstance(steps, list):
                steps = None
            self._json(
                200,
                ORG.cycle_explore(
                    steps=steps,
                    ask_if_stuck=bool(data.get("ask_if_stuck", True)),
                    speak=bool(data.get("speak", False)),
                ),
            )
            return
        if self.path.startswith("/autonomy"):
            tool = str(data.get("tool") or data.get("name") or "").strip()
            if not tool:
                self._json(
                    400,
                    {
                        "error": "tool required",
                        "tools": [
                            "probe_sensors", "body_map", "look_around", "listen_ambient",
                            "reach_local", "wonder", "correlate", "experiment",
                            "craft_tool", "ask_when_stuck", "explore",
                        ],
                    },
                )
                return
            if tool in ("explore", "explore_cycle", "cycle"):
                self._json(
                    200,
                    ORG.cycle_explore(
                        ask_if_stuck=bool(data.get("ask_if_stuck", True)),
                        speak=bool(data.get("speak", False)),
                    ),
                )
                return
            self._json(
                200,
                ORG.cycle_autonomy_tool(
                    tool,
                    speak=bool(data.get("speak", False)),
                    seconds=data.get("seconds"),
                    idea=data.get("idea"),
                    question=data.get("question"),
                ),
            )
            return
        if self.path.startswith("/speak"):
            self._json(200, tool_speak(str(data.get("text") or "")))
            return
        if self.path.startswith("/volume"):
            percent = data.get("percent")
            delta = data.get("delta")
            mute = data.get("mute")
            self._json(
                200,
                tool_volume_set(
                    percent=int(percent) if percent is not None else None,
                    delta=int(delta) if delta is not None else None,
                    mute=None if mute is None else bool(mute),
                ),
            )
            return
        if self.path.startswith("/mic"):
            # POST {capture:70} | {auto:true} + optional wav path | {percent:N}
            if data.get("auto"):
                wav = str(data.get("wav") or data.get("path") or "").strip()
                if not wav:
                    rec = _record_wav(float(data.get("seconds") or 2))
                    if not rec.get("ok"):
                        self._json(200, rec)
                        return
                    wav = rec["wav"]
                self._json(200, mic_auto_tune_from_wav(wav))
                return
            if data.get("capture") is not None or data.get("percent") is not None:
                pct = int(data.get("capture") if data.get("capture") is not None else data.get("percent"))
                self._json(200, mic_set_percent(MIC_CAPTURE_CTRL, pct, capture=True))
                return
            self._json(200, mic_summary())
            return
        if self.path.startswith("/vision"):
            prov = str(data.get("provider") or "").strip().lower()
            if not prov:
                self._json(400, {"error": "provider=nvidia|puter required"})
                return
            try:
                set_vision_provider(prov)
            except ValueError as e:
                self._json(400, {"error": str(e)})
                return
            self._json(
                200,
                {
                    "ok": True,
                    "provider": get_vision_provider(),
                    "nvidia_ready": bool(_load_nvidia_token()),
                    "puter_ready": bool(_load_puter_token()),
                    "nvidia_model": NVIDIA_VISION_MODEL,
                    "puter_model": PUTER_VISION_MODEL,
                },
            )
            return
        if self.path.startswith("/camera"):
            # Réglage manuel ou auto: {brightness: N, gamma: N, auto: true}
            if data.get("auto"):
                # Capture + auto-tune sans vision LLM
                seen = tool_see(auto_tune=True)
                self._json(200, {"ok": bool(seen.get("ok")), "frame": seen, "sensor": seen.get("sensor")})
                return
            allowed = {
                "brightness", "contrast", "saturation", "gamma", "sharpness",
                "backlight_compensation", "auto_exposure", "exposure_time_absolute",
            }
            updates = {k: int(v) for k, v in data.items() if k in allowed}
            if not updates:
                self._json(400, {"error": "no controls", "allowed": sorted(allowed), "hint": "or auto:true"})
                return
            applied = camera_set_controls(updates)
            st = ORG._camera_status()
            st["applied"] = applied
            self._json(200, st)
            return
        if self.path.startswith("/voice"):
            enabled = bool(data.get("enabled", True))
            self._json(200, start_voice_loop() if enabled else stop_voice_loop())
            return
        if self.path.startswith("/ask/answer"):
            answer = str(data.get("answer") or "").strip()
            if not answer:
                self._json(400, {"error": "answer required"})
                return
            payload = {}
            if ASK.exists():
                try:
                    payload = json.loads(ASK.read_text(encoding="utf-8"))
                except Exception:
                    payload = {}
            payload.update({
                "status": "answered",
                "answer": answer,
                "answered_at": dt.datetime.now().isoformat(timespec="seconds"),
            })
            ASK.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            ORG.learn_perception("C", f"Réponse humaine intégrée: {answer[:400]}", "P", 8)
            # Attendre sans harceler = expérience positive (renforce le vivant mémoire)
            ORG.learn_perception(
                "C",
                "Expérience: j'ai attendu la réponse de l'humain sans le harceler de questions — bien.",
                "P",
                7,
            )
            self._json(200, {"ok": True})
            return
        if self.path.startswith("/reset"):
            confirm = str(data.get("confirm") or "")
            if confirm != "RESET_ORGANISM":
                self._json(400, {"error": "confirm=RESET_ORGANISM required"})
                return
            ORG = Organism(reset=True)
            self._json(200, {"ok": True, "status": ORG.status()})
            return
        self._json(404, {"error": "not found"})

    def log_message(self, fmt: str, *args: Any) -> None:
        log("HTTP " + (fmt % args))


def main() -> None:
    global ORG
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="wipe memories to bootstrap-only")
    parser.add_argument("--voice", action="store_true")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    ORG = Organism(reset=args.reset)
    log(f"organism online memories={len(ORG.ms.entries)} port={args.port} ui={UI_INDEX.exists()}")
    tool_speak("Organisme mémoire prêt. Interface nursery disponible.")

    if args.voice or os.environ.get("VOICE_LOOP") == "1":
        start_voice_loop()

    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
