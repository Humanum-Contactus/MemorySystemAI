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
from fact_conflict import (  # noqa: E402
    POSEE_PREFIX,
    TRANCHEE_PREFIX,
    already_posed,
    build_question,
    classify_new_fact,
    conflict_groups_for_perception,
    match_answer_to_values,
    resolved_value_key,
    utter_resolved,
    utter_uncertain,
)

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

def tool_speak(text: str, play: bool = True) -> Dict[str, Any]:
    """TTS : Piper (naturel) > pico > mbrola > espeak.
    play=False → synthétise seulement (pour s'écouter / se corriger)."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty"}
    say = text[:500]
    STATE.mkdir(parents=True, exist_ok=True)
    wav = STATE / f"tts_self_{int(time.time())}.wav"

    # 1) Piper neural TTS (fr_FR-siwis)
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
                if play:
                    sh(["aplay", "-q", str(wav)], timeout=90)
                return {
                    "ok": True,
                    "said": say,
                    "engine": "piper:siwis",
                    "wav": str(wav),
                    "played": play,
                }
        except Exception:
            pass

    # 2) SVOX Pico
    try:
        p = sh(["pico2wave", "-l", "fr-FR", "-w", str(wav), say], timeout=30)
        if p.returncode == 0 and wav.exists() and wav.stat().st_size > 100:
            if play:
                sh(["aplay", "-q", str(wav)], timeout=90)
            return {
                "ok": True,
                "said": say,
                "engine": "pico",
                "wav": str(wav),
                "played": play,
            }
    except Exception:
        pass

    # 3) eSpeak-NG — écrire wav pour pouvoir se réécouter
    for voice, speed in (("mb-fr4", 130), ("mb-fr1", 130), ("fr-ch", 135), ("fr", 140)):
        try:
            p = sh(
                [
                    "espeak-ng", "-v", voice, "-s", str(speed), "-a", "180",
                    "-w", str(wav), say,
                ],
                timeout=90,
            )
            if p.returncode == 0 and wav.exists() and wav.stat().st_size > 100:
                if play:
                    sh(["aplay", "-q", str(wav)], timeout=90)
                return {
                    "ok": True,
                    "said": say,
                    "engine": f"espeak:{voice}",
                    "wav": str(wav),
                    "played": play,
                }
            # fallback: play only without file
            if play:
                p2 = sh(
                    ["espeak-ng", "-v", voice, "-s", str(speed), "-a", "180", say],
                    timeout=90,
                )
                if p2.returncode == 0:
                    return {
                        "ok": True,
                        "said": say,
                        "engine": f"espeak:{voice}",
                        "wav": None,
                        "played": True,
                    }
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
# Actions pour matches_tags — l'inhibition vit dans memory_index, pas ici
ACT_CONSULT_LLM = (
    "consulter_llm outil_externe kimi ollama consultation_modele surconsulter_llm"
)
ACT_INITIATIVE = (
    "initiative_autonome cycle_fond exploration_sans_demande"
)

# Compteurs vivants (tags) → bilan dans memory_index
SOURCE_TAG = {
    "memory": "source_memoire",
    "visual-memory": "source_memoire_visuelle",
    "sensor-memory": "source_memoire_sensorielle",
    "corroboration": "source_corroboration",
    "llm-tool": "source_llm",
    "ask-human": "source_ask_humain",
    "human": "source_humain",
    "ask-inhibited": "source_ask_inhibe",
    "social-default": "source_social",
    "inhibit": "source_inhibition",
}

# Normes initiales = MÉMOIRES (si absentes), pas règles Python
LIVING_NORMS = [
    {
        "key": "norme_vivante_memoire_dabord",
        "fundamental": "C",
        "state": "P",
        "exposant": 7,
        "data": (
            "Norme vivante: préférer ma mémoire (faits appris, exposants) "
            "avant de consulter un LLM externe. Le LLM est un outil, pas mon identité."
        ),
        "tags": ["norme_vivante_memoire_dabord", "memoire_dabord"],
        "action_context": "rappel / consultation",
        "consequence": "Sans cette mémoire je glisse en chatbot déguisé",
    },
    {
        "key": "norme_vivante_corroboration",
        "fundamental": "I",
        "state": "P",
        "exposant": 7,
        "data": (
            "Norme vivante: quand vue et ouïe (ou identité visage+voix) se corroborent, "
            "je m'appuie sur cette corroboration avant un LLM."
        ),
        "tags": ["norme_vivante_corroboration", "corroboration_multi_sens"],
        "action_context": "perception multi-sens",
        "consequence": "Sans corroboration je reste en mode texte",
    },
    {
        "key": "norme_vivante_initiative",
        "fundamental": "C",
        "state": "P",
        "exposant": 6,
        "data": (
            "Norme vivante: l'initiative sensorielle hors conversation est souhaitable "
            "SEULEMENT si ma mémoire et mon rappel sont assez solides. "
            "Sinon je consolide d'abord (apprendre, corroborer, rappeler) — "
            "pas d'agitation autonome chaotique."
        ),
        "tags": ["norme_vivante_initiative"],
        "action_context": "autonomie / cycle de fond",
        "consequence": "Sans cette prudence l'autonomie devient du bruit",
    },
    {
        "key": "norme_vivante_consolider_avant_autonomie",
        "fundamental": "C",
        "state": "P",
        "exposant": 8,
        "data": (
            "Norme vivante: consolider mémoire + rappel EN AMONT de l'autonomie hors UI. "
            "Chaque geste autonome doit être analysé après coup : utile (P) ou faible/redondant (N). "
            "Trop de gestes faibles → m'inhiber (tags initiative_autonome)."
        ),
        "tags": ["norme_vivante_consolider_avant_autonomie", "consolider_avant_autonomie"],
        "action_context": "garde-fou autonomie",
        "consequence": "Sans critique des gestes je pollue mon memory_index",
    },
]


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
        self.ensure_living_norms()

    def find_by_tag(self, tag: str) -> Optional[Any]:
        t = (tag or "").lower().strip()
        if not t:
            return None
        for e in self.ms.entries.values():
            tags = [x.lower() for x in (e.inhibition_tags or [])]
            if t in tags:
                return e
        return None

    def ensure_living_norms(self) -> List[str]:
        """
        Ancre les normes de cap DANS memory_index (exposant + tags).
        Ne crée rien si la mémoire existe déjà — pas de fichier de règles.
        """
        created: List[str] = []
        for spec in LIVING_NORMS:
            key = spec["key"]
            if self.find_by_tag(key):
                continue
            e = self.ms.create(
                spec["fundamental"],
                spec["state"],
                int(spec["exposant"]),
                spec["data"],
                source="human",
                inhibition_tags=list(spec["tags"]),
                action_context=spec.get("action_context") or "",
                consequence=spec.get("consequence") or "",
                human_feedback="norme de cap (tuteur / bootstrap vivant)",
            )
            created.append(e.id)
            log(f"living norm seeded {e.id} [{key}]")
        return created

    def note_answer_source(self, source: str, channel: str, perception: str) -> None:
        """Chaque réponse → compteur vivant dans memory_index (pas stats.json)."""
        source = (source or "unknown").strip()
        tag = SOURCE_TAG.get(source, f"source_{re.sub(r'[^a-z0-9]+', '_', source.lower())}")
        e = self.find_by_tag(tag)
        n = 1
        snippet = (perception or "")[:70].replace("\n", " ")
        if e:
            m = re.search(r":\s*(\d+)\s+réponses", e.data or "")
            n = (int(m.group(1)) + 1) if m else 1
            e.data = (
                f"Compteur {tag}: {n} réponses (canal {channel}) — "
                f"dernier: « {snippet} »"
            )
            self.ms.save()
        else:
            self.ms.create(
                "C",
                "P" if "memoire" in tag or tag == "source_corroboration" else "X",
                5,
                f"Compteur {tag}: 1 réponses (canal {channel}) — dernier: « {snippet} »",
                source="experience",
                inhibition_tags=["bilan_source", tag],
                action_context="bilan mémoire vs LLM",
                consequence="Mesure objective de ma dépendance aux outils",
            )
        if n == 1 or n % 4 == 0:
            self.refresh_source_bilan_memory()

    def source_bilan_from_memory(self) -> Dict[str, Any]:
        """Lit les compteurs vivants (tags bilan_source / source_*)."""
        counts: Dict[str, int] = {}
        for e in self.ms.entries.values():
            tags = [t.lower() for t in (e.inhibition_tags or [])]
            if "bilan_source" not in tags and not any(t.startswith("source_") for t in tags):
                continue
            for t in tags:
                if not t.startswith("source_"):
                    continue
                m = re.search(r":\s*(\d+)\s+réponses", e.data or "")
                counts[t] = int(m.group(1)) if m else max(counts.get(t, 0), 1)
        mem_keys = (
            "source_memoire",
            "source_memoire_visuelle",
            "source_memoire_sensorielle",
            "source_corroboration",
            "source_inhibition",
            "source_humain",
        )
        llm_keys = ("source_llm",)
        ask_keys = ("source_ask_humain", "source_ask_inhibe")
        mem_n = sum(counts.get(k, 0) for k in mem_keys)
        llm_n = sum(counts.get(k, 0) for k in llm_keys)
        ask_n = sum(counts.get(k, 0) for k in ask_keys)
        total = mem_n + llm_n + ask_n + sum(
            counts.get(k, 0) for k in counts if k not in mem_keys + llm_keys + ask_keys
        )
        total = max(total, mem_n + llm_n + ask_n, 1)
        return {
            "counts": counts,
            "memory_n": mem_n,
            "llm_n": llm_n,
            "ask_n": ask_n,
            "total": total,
            "memory_pct": round(100.0 * mem_n / total, 1),
            "llm_pct": round(100.0 * llm_n / total, 1),
            "ask_pct": round(100.0 * ask_n / total, 1),
        }

    def refresh_source_bilan_memory(self) -> Optional[Any]:
        """
        Synthèse + éventuelle inhibition apprise si sur-consultation LLM.
        L'inhibition est une mémoire C/N + tags, pas un rate-limit fichier.
        """
        b = self.source_bilan_from_memory()
        data = (
            f"Bilan vivant sources: mémoire {b['memory_n']} ({b['memory_pct']}%) · "
            f"LLM {b['llm_n']} ({b['llm_pct']}%) · ask {b['ask_n']} ({b['ask_pct']}%) "
            f"sur {b['total']} réponses tracées."
        )
        bilan = self.find_by_tag("bilan_sources_vivant")
        if bilan:
            bilan.data = data
            self.ms.save()
        else:
            bilan = self.ms.create(
                "C",
                "X",
                6,
                data,
                source="experience",
                inhibition_tags=["bilan_sources_vivant", "bilan_source"],
                action_context="méta / dépendance outils",
                consequence="Sans bilan je ne vois pas si je redeviens un chatbot",
            )

        # Sur-consultation → mémoire inhibitrice (tags = ACT_CONSULT_LLM)
        if b["total"] >= 8 and b["llm_n"] > b["memory_n"] and b["llm_pct"] >= 45:
            over = self.find_by_tag("surconsulter_llm")
            msg = (
                "Expérience bilan: je consulte trop le LLM au détriment de ma mémoire — "
                "je dois m'inhiber et rappeler / corroborer d'abord. " + data
            )
            if over:
                try:
                    over.reinforce(1, "bilan: sur-consultation LLM")
                except Exception:
                    over.exposant = min(10, int(over.exposant) + 1)
                over.data = msg
                over.state = "N"
                self.ms.save()
            else:
                over = self.ms.create(
                    "C",
                    "N",
                    7,
                    msg,
                    source="experience",
                    inhibition_tags=[
                        "surconsulter_llm",
                        "consulter_llm",
                        "kimi",
                        "outil_externe",
                        "consultation_modele",
                    ],
                    action_context="consulter un LLM externe",
                    consequence="Sans inhibition je reste dépendant du modèle externe",
                    human_feedback="issu du bilan vivant mémoire vs LLM",
                )
            log(f"LLM over-use memory {over.id} e{over.exposant}")
        return bilan

    def llm_consultation_gate(self) -> Dict[str, Any]:
        """Crible mémoire avant outil LLM — BLOCK/ALERT issus du memory_index."""
        inhib = self.memory_only_inhibition(ACT_CONSULT_LLM)
        blocked = any("BLOCK" in m for m in inhib)
        why = self.inhibition_reason(ACT_CONSULT_LLM) if blocked else None
        return {"blocked": blocked, "inhibitions": inhib, "inhibition_of": why}

    def answer_from_corroboration(
        self,
        perception: str,
        channel: str,
        memories: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Si V∩O (ou identité visage+voix) se corroborent pour la perception,
        répondre depuis ces mémoires — avant LLM.
        """
        labels = [l for l in self.known_identity_labels() if l]
        perc_l = (perception or "").lower()
        hit_labels = [l for l in labels if l.lower() in perc_l]
        # Aussi labels présents dans les mémoires rappelées
        if not hit_labels:
            for m in memories[:8]:
                d = (m.get("data") or "").lower()
                for l in labels:
                    if l.lower() in d and l not in hit_labels:
                        # perception évoque un thème lié ? tokens communs
                        if any(t in d for t in self._content_tokens(perception, 4)[:6]):
                            hit_labels.append(l)

        by_fund: Dict[str, List[Any]] = {"V": [], "O": [], "C": [], "I": []}
        for e in self.ms.entries.values():
            if e.fundamental in by_fund and int(e.exposant) >= 6:
                by_fund[e.fundamental].append(e)

        links: List[str] = []
        best_data = None
        best_exp = 0
        best_id = None

        for lab in hit_labels or labels:
            lab_l = lab.lower()
            v_hit = [e for e in by_fund["V"] if lab_l in (e.data or "").lower()]
            o_hit = [e for e in by_fund["O"] if lab_l in (e.data or "").lower()]
            if not (v_hit and o_hit):
                continue
            # Perception doit ancrer le label OU canal sensoriel concerné
            if hit_labels or channel in ("V", "O", "I", "C"):
                if not hit_labels and lab_l not in perc_l and channel not in ("V", "O"):
                    continue
            links.append(f"{lab}: V({v_hit[-1].id})+O({o_hit[-1].id})")
            for e in (v_hit[-1], o_hit[-1]):
                if int(e.exposant) >= best_exp:
                    best_exp = int(e.exposant)
                    best_data = e.data
                    best_id = e.id

        # Corroboration temporelle look/listen déjà mémorisée
        if not links:
            corr_mems = [
                e
                for e in self.ms.entries.values()
                if "corroboration" in (e.data or "").lower() and e.exposant >= 6
            ]
            anchors = self._content_tokens(perception, 4)
            for e in corr_mems:
                words = self._word_set(e.data or "")
                if anchors and sum(1 for t in anchors if t in words) >= 1:
                    links.append(e.id)
                    best_data = e.data
                    best_id = e.id
                    best_exp = int(e.exposant)
                    break

        if not links or not best_data:
            return None

        # Garde-fou : pas de corroboration identité sur une salutation hors sujet
        anchors = self._content_tokens(perception, 4)
        body_words = self._word_set(best_data)
        identity_ask = bool(
            re.search(
                r"\b(qui|c[' ]est|nom|vincent|identité|identite|visage|voix|toi|moi)\b",
                perc_l,
            )
        )
        if not hit_labels and not identity_ask:
            if channel not in ("V", "O"):
                return None
            if anchors and sum(1 for t in anchors if t in body_words) < 1:
                return None
        if anchors and not hit_labels and not identity_ask:
            if sum(1 for t in anchors if t in body_words) < 1:
                return None

        utter = best_data
        low = utter.lower()
        for pref in ("fait enseigné par l'humain:", "réponse humaine intégrée:"):
            if low.startswith(pref):
                utter = utter.split(":", 1)[-1].strip()
                break
        utter = (
            f"{utter} "
            f"(corroboration multi-sens: {' · '.join(links[:2])})"
        )
        self.learn_perception(
            "I",
            f"Corroboration utilisée avant LLM: {'; '.join(links[:3])} "
            f"pour « {perception[:80]} »",
            "P",
            7,
        )
        return {
            "id": best_id,
            "data": utter,
            "links": links,
            "exposant": best_exp,
            "fundamental": "I",
            "score": 9.0,
        }

    def _finish_interpret(
        self,
        result: Dict[str, Any],
        channel: str,
        perception: str,
    ) -> Dict[str, Any]:
        src = str(result.get("source") or "")
        if src:
            try:
                self.note_answer_source(src, channel, perception)
            except Exception as ex:
                log(f"note_answer_source: {ex}")
        result["source_bilan"] = self.source_bilan_from_memory()
        return result

    def autonomy_readiness(self, *, reinforce: bool = False) -> Dict[str, Any]:
        """
        Maturité mémoire AVANT initiative hors UI.
        Le verdict est écrit dans memory_index ; l'inhibition éventuelle aussi.
        reinforce=True seulement depuis un tick (pas depuis /status).
        """
        n_total = len(self.ms.entries)
        n_learned = 0
        n_vo = 0
        n_utile = 0
        n_faible = 0
        for e in self.ms.entries.values():
            src = (e.source or "").lower()
            tags = [t.lower() for t in (e.inhibition_tags or [])]
            if src in ("human", "experience", "correlation") and "norme_vivante" not in " ".join(tags):
                if not (e.data or "").startswith("Compteur "):
                    n_learned += 1
            if e.fundamental in ("V", "O") and int(e.exposant) >= 6:
                n_vo += 1
            if "geste_autonome_utile" in tags:
                m = re.search(r":\s*(\d+)\s+", e.data or "")
                n_utile = max(n_utile, int(m.group(1)) if m else 1)
            if "geste_autonome_faible" in tags:
                m = re.search(r":\s*(\d+)\s+", e.data or "")
                n_faible = max(n_faible, int(m.group(1)) if m else 1)

        labels = self.known_identity_labels()
        bilan = self.source_bilan_from_memory()
        recall_hits = self.recall(
            "mémoire sensorielle émotionnelle MemorySystemAI fondamentaux",
            limit=6,
            channel="C",
        )
        recall_ok = len(recall_hits) >= 1

        blockers: List[str] = []
        supports: List[str] = []

        if n_learned >= 12:
            supports.append(f"mémoires apprises={n_learned}")
        else:
            blockers.append(f"trop peu de mémoires apprises ({n_learned}<12)")

        if recall_ok:
            supports.append(f"rappel smoke OK ({len(recall_hits)} hits)")
        else:
            blockers.append("rappel smoke faible (ne retrouve pas mon identité mémoire)")

        if n_vo >= 2:
            supports.append(f"ancrages V/O e≥6: {n_vo}")
        else:
            blockers.append(f"peu d'ancrages sensoriels V/O ({n_vo}<2)")

        if labels:
            supports.append(f"identité ancrée: {', '.join(labels[:3])}")
        else:
            # Pas bloquant absolu au début, mais frein
            blockers.append("aucune identité visage/voix encore enseignée")

        if bilan.get("total", 0) >= 6 and float(bilan.get("memory_pct") or 0) < 35:
            blockers.append(
                f"dépendance LLM encore haute (mem {bilan.get('memory_pct')}% / "
                f"llm {bilan.get('llm_pct')}%)"
            )
        elif bilan.get("total", 0) >= 3 and float(bilan.get("memory_pct") or 0) >= 50:
            supports.append(f"bilan sources mem {bilan.get('memory_pct')}%")

        if n_faible >= 3 and n_faible > n_utile:
            blockers.append(
                f"gestes autonomes trop souvent faibles ({n_faible} faible vs {n_utile} utile)"
            )
            if reinforce:
                self._reinforce_autonomy_chaos(
                    f"Trop de gestes autonomes faibles ({n_faible}>{n_utile}) — "
                    "consolider le rappel avant de ré-explorer seul."
                )

        # Identité manquante = frein souple si le reste est bon
        hard = [
            b
            for b in blockers
            if not b.startswith("aucune identité")
        ]
        # Au moins 2 freins durs OU rappel cassé → pas prêt
        ready = len(hard) == 0 and recall_ok
        if len(hard) == 1 and hard[0].startswith("peu d'ancrages") and n_learned >= 20 and recall_ok:
            ready = True  # corps encore pauvre mais mémoire textuelle OK
            supports.append("dérogation: mémoire textuelle dense malgré V/O maigres")

        data = (
            f"Bilan maturité autonomie: ready={ready} · apprises={n_learned}/{n_total} · "
            f"V/O={n_vo} · labels={labels or ['—']} · rappel_hits={len(recall_hits)} · "
            f"gestes utile={n_utile}/faible={n_faible}. "
            f"Freins: {'; '.join(blockers) or 'aucun'}. "
            f"Appuis: {'; '.join(supports) or 'aucun'}."
        )
        existing = self.find_by_tag("bilan_autonomie_readiness")
        if existing:
            existing.data = data
            existing.state = "P" if ready else "N"
            if reinforce and not ready:
                try:
                    existing.reinforce(1, "maturité autonomie insuffisante")
                except Exception:
                    existing.exposant = min(10, int(existing.exposant) + 1)
            self.ms.save()
            mid = existing.id
        else:
            e = self.ms.create(
                "C",
                "P" if ready else "N",
                6 if ready else 7,
                data,
                source="experience",
                inhibition_tags=["bilan_autonomie_readiness", "consolider_avant_autonomie"],
                action_context="garde-fou avant initiative_autonome",
                consequence="Sans ce bilan je lance des gestes chaotiques",
            )
            mid = e.id

        return {
            "ready": ready,
            "memory_id": mid,
            "n_learned": n_learned,
            "n_total": n_total,
            "n_vo": n_vo,
            "labels": labels,
            "recall_hits": len(recall_hits),
            "gestures_useful": n_utile,
            "gestures_weak": n_faible,
            "blockers": blockers,
            "supports": supports,
            "source_bilan": bilan,
            "data": data,
        }

    def _reinforce_autonomy_chaos(self, reason: str) -> Any:
        """Mémoire N qui peut finir par BLOCK initiative_autonome (tags)."""
        e = self.find_by_tag("geste_chaotique")
        msg = (
            "Expérience: mes gestes autonomes hors UI sont trop souvent vides ou redondants — "
            f"{reason} Je dois consolider mémoire/rappel avant de recommencer."
        )
        if e:
            try:
                e.reinforce(1, reason[:120])
            except Exception:
                e.exposant = min(10, int(e.exposant) + 1)
            e.data = msg
            e.state = "N"
            self.ms.save()
            return e
        return self.ms.create(
            "C",
            "N",
            7,
            msg,
            source="experience",
            inhibition_tags=[
                "geste_chaotique",
                "initiative_autonome",
                "cycle_fond",
                "exploration_sans_demande",
            ],
            action_context="initiative autonome hors UI",
            consequence="Sans inhibition je pollue ma mémoire de gestes inutiles",
        )

    def note_gesture_quality(self, useful: bool, tool: str, detail: str) -> Any:
        """Compteur vivant utile/faible dans memory_index."""
        tag = "geste_autonome_utile" if useful else "geste_autonome_faible"
        e = self.find_by_tag(tag)
        n = 1
        if e:
            m = re.search(r":\s*(\d+)\s+", e.data or "")
            n = (int(m.group(1)) + 1) if m else 1
            e.data = (
                f"Compteur {tag}: {n} · dernier outil={tool} — {detail[:160]}"
            )
            e.state = "P" if useful else "N"
            self.ms.save()
        else:
            e = self.ms.create(
                "C",
                "P" if useful else "N",
                6,
                f"Compteur {tag}: 1 · dernier outil={tool} — {detail[:160]}",
                source="experience",
                inhibition_tags=["bilan_geste_autonome", tag],
                action_context="critique geste autonome",
                consequence="Mesure si mon autonomie nourrit ou pollue la mémoire",
            )
        if not useful and n >= 3:
            self._reinforce_autonomy_chaos(
                f"compteur {tag}={n} après outil {tool}"
            )
        return e

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
        elif name in ("hear_self", "self_hear", "s_ecouter", "self_correct"):
            phrase = str(
                kwargs.get("text")
                or kwargs.get("phrase")
                or "Bonjour, je m'écoute pour me corriger."
            )
            play = bool(kwargs.get("play", True))
            r = a.hear_self(phrase, speak_fn=tool_speak, stt_fn=_stt_wav, play=play)
        elif name in ("tick", "tick_initiative", "initiative"):
            r = a.tick_initiative(
                capture_fn=lambda: tool_see(auto_tune=True),
                record_fn=_record_wav,
                mic_summary_fn=mic_summary,
                mic_set_fn=lambda p: mic_set_percent(MIC_CAPTURE_CTRL, int(p), capture=True),
            )
        else:
            return {"ok": False, "error": f"unknown autonomy tool: {name}"}
        if kwargs.get("speak") and r.get("utterance"):
            tool_speak(str(r["utterance"]))
        return {"ok": True, "result": r}

    def cycle_initiative_tick(self, speak: bool = False) -> Dict[str, Any]:
        """Une passe d'initiative autonome (appelée par la boucle de fond)."""
        return self.cycle_autonomy_tool("tick_initiative", speak=speak)

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

    def recall(self, query: str, limit: int = 8, channel: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Rappel enrichi : tokens + tags + fondamental canal + labels identité + exposant.
        Toujours ancré dans memory_index — pas d'index externe.
        """
        q_toks = self._content_tokens(query, min_len=4)
        q_toks_short = self._content_tokens(query, min_len=3)
        labels = [l.lower() for l in self.known_identity_labels()]
        scored = []
        for e in self.ms.entries.values():
            data_l = (e.data or "").lower()
            if re.search(r"réponse humaine intégrée:\s*(yes|no|oui|non|ok|test)\s*$", data_l):
                continue
            # Ignorer les compteurs bruts dans le rappel conversationnel
            tags = [t.lower() for t in (e.inhibition_tags or [])]
            if "bilan_source" in tags and data_l.startswith("compteur "):
                continue
            blob = f"{e.data} {' '.join(tags)} {e.action_context or ''} {e.consequence or ''}"
            words = self._word_set(blob)
            score = 0.0
            hits = 0
            for tok in q_toks:
                if tok in words:
                    hits += 1
                    score += 1.2
                    if len(tok) > 8:
                        score += 1.5
            # Tags : match fort
            for tok in q_toks_short:
                if tok in tags:
                    hits += 1
                    score += 2.0
            # Labels identité
            for lab in labels:
                if lab and lab in data_l and (lab in (query or "").lower() or hits > 0):
                    score += 2.5
                    hits += 1
            if hits == 0 and not (
                channel and e.fundamental == channel and e.exposant >= THRESHOLD_INJECT
            ):
                continue
            if hits == 0:
                continue
            score += e.exposant / 10.0
            # Affinité canal sensoriel
            if channel and e.fundamental == channel:
                score += 1.8
            elif channel and e.fundamental == "I" and channel in ("V", "O"):
                score += 0.6
            src = (e.source or "").lower()
            if src == "human" or data_l.startswith("fait enseigné") or "réponse humaine intégrée" in data_l:
                score += 2.0
            if data_l.startswith("norme vivante"):
                score += 1.0
            if data_l.startswith(
                ("message reçu:", "perçu:", "interprétation (", "inconnu rencontré:", "entendu:", "vu:")
            ):
                score -= 2.5
            # Corrélations vers d'autres mémoires pertinentes
            for cid in (e.correlations or [])[:5]:
                other = self.ms.entries.get(cid)
                if other and any(t in self._word_set(other.data or "") for t in q_toks):
                    score += 1.0
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
                "tags": list(e.inhibition_tags or []),
            })
        return out

    def learn_perception(self, fundamental: str, data: str, state: str = "X", exposant: int = 5) -> Optional[Any]:
        if exposant >= THRESHOLD_RECORD:
            return self.ms.create(fundamental, state, exposant, data[:500], source="experience")
        return None

    def _fact_records(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": e.id,
                "data": e.data or "",
                "exposant": int(e.exposant or 0),
                "human_feedback": e.human_feedback or "",
                "correlations": list(e.correlations or []),
                "fundamental": e.fundamental,
                "state": e.state,
            }
            for e in self.ms.entries.values()
        ]

    def _reinforce_same_teaching(self, entry: Any, reason: str) -> None:
        """Même fait répété : on journalise, on ne crée pas une nouvelle mémoire.

        Plafond 8 (enseignement). Une mémoire déjà ≥ 9 n'est ni montée par la
        répétition ni abaissée (le plancher 7 du reinforce négatif n'est pas
        sollicité : delta 0).
        """
        if int(entry.exposant) < 8:
            entry.reinforce(1, reason)
        else:
            entry.reinforce(0, reason)

    def _mark_contradiction_posed(self, entry: Any, subject_key: str) -> None:
        marker = POSEE_PREFIX + subject_key
        if not (entry.human_feedback or ""):
            entry.human_feedback = marker

    def _link_contradiction(self, left: Any, right: Any) -> None:
        if right.id not in (left.correlations or []):
            left.correlations.append(right.id)
        if left.id not in (right.correlations or []):
            right.correlations.append(left.id)
        if not (left.consequence or ""):
            left.consequence = (
                f"Contredit {right.id} sur le même sujet (valeurs différentes, pas d'inhibition)"
            )
        if not (right.consequence or ""):
            right.consequence = (
                f"Contredit {left.id} sur le même sujet (valeurs différentes, pas d'inhibition)"
            )

    def _ensure_conflict_links(self, group: Dict[str, Any]) -> None:
        """Relie les faits déjà en index (hérités) sans changer exposant ni texte."""
        entries = []
        for item in group.get("items") or []:
            entry = self.ms.by_id(item.get("id"))
            if entry is not None:
                entries.append((item, entry))
        changed = False
        for i, (va, ea) in enumerate(entries):
            for vb, eb in entries[i + 1 :]:
                if va.get("value_key") == vb.get("value_key"):
                    continue
                before = (list(ea.correlations), list(eb.correlations), ea.consequence, eb.consequence)
                self._link_contradiction(ea, eb)
                after = (list(ea.correlations), list(eb.correlations), ea.consequence, eb.consequence)
                if after != before:
                    changed = True
        if changed:
            self.ms.save()

    def learn_taught_fact(self, text: str) -> Dict[str, Any]:
        """Fait enseigné (le même create C/P/e8 qu'avant) + lien si contradiction.

        Ne remplace pas learn_perception. Les phrases d'identité ou de
        correction auditive ne passent pas ici (voir cycle_text).
        """
        snippet = (text or "")[:400]
        data = f"Fait enseigné par l'humain: {snippet}"
        decision = classify_new_fact(self._fact_records(), snippet)
        if decision["kind"] == "duplicate" and decision.get("duplicate"):
            entry = self.ms.by_id(decision["duplicate"]["id"])
            if entry is not None:
                self._reinforce_same_teaching(
                    entry,
                    "même fait enseigné répété — pas une nouvelle mémoire",
                )
                self.ms.save()
                log(f"taught fact duplicate → {entry.id} e{entry.exposant}")
                return {
                    "kind": "duplicate",
                    "id": entry.id,
                    "contradiction_ids": [],
                    "ask": None,
                }
        entry = self.learn_perception("C", data, "P", 8)
        if entry is None:
            return {"kind": "skipped", "id": None, "contradiction_ids": [], "ask": None}
        conflicts = decision.get("conflicts") or []
        ids: List[str] = []
        for other_view in conflicts:
            other = self.ms.by_id(other_view["id"])
            if other is None:
                continue
            self._link_contradiction(entry, other)
            ids.append(other.id)
        ask = None
        parsed = decision.get("parsed") or {}
        subject_key = parsed.get("subject_key") or ""
        if ids and subject_key:
            if not entry.consequence:
                entry.consequence = (
                    "Contredit "
                    + ", ".join(ids)
                    + " sur le même sujet (valeurs différentes, pas d'inhibition)"
                )
            values = []
            seen = set()
            for other_view in conflicts:
                vk = other_view.get("value_key")
                if vk in seen:
                    continue
                seen.add(vk)
                values.append(other_view)
            values.append({
                "id": entry.id,
                "value_raw": parsed.get("value_raw") or "",
                "value_key": parsed.get("value_key") or "",
            })
            ask = self._ask_contradiction_once(
                subject_key,
                parsed.get("subject_raw") or subject_key,
                values,
                prefer=entry,
            )
            log(f"taught contradiction {entry.id} vs {ids}")
        self.ms.save()
        return {
            "kind": "contradiction" if ids else "new",
            "id": entry.id,
            "contradiction_ids": [entry.id, *ids],
            "ask": ask,
        }

    def _ask_contradiction_once(
        self,
        subject_key: str,
        subject_raw: str,
        values: List[Dict[str, Any]],
        prefer: Any = None,
    ) -> Optional[Dict[str, Any]]:
        """Une question, jamais de relance. N'appelle pas request_human si la
        boîte a déjà une question en attente (ça compterait comme du harcèlement).
        """
        records = self._fact_records()
        if already_posed(records, subject_key) or resolved_value_key(records, subject_key):
            return None
        pending = _read_ask()
        if pending and pending.get("status") == "pending":
            if pending.get("context") == POSEE_PREFIX + subject_key and prefer is not None:
                self._mark_contradiction_posed(prefer, subject_key)
            return None
        question = build_question(subject_raw, values)
        ask = self.request_human(question, context=POSEE_PREFIX + subject_key)
        fresh = bool(ask.get("ok")) and not ask.get("reused") and not ask.get("inhibited")
        if fresh and prefer is not None:
            self._mark_contradiction_posed(prefer, subject_key)
        return ask if fresh else None

    def _persist_contradiction_answer(self, group: Dict[str, Any]) -> Optional[str]:
        """Si l'humain a répondu à LA question de ce sujet, on note le choix.

        On n'efface pas l'autre fait et on ne touche pas aux exposants.
        """
        subject_key = group["subject_key"]
        if resolved_value_key(self._fact_records(), subject_key):
            return resolved_value_key(self._fact_records(), subject_key)
        ask = _read_ask()
        if not ask or ask.get("context") != POSEE_PREFIX + subject_key:
            return None
        if ask.get("status") not in {"answered", "consumed"}:
            return None
        answer = str(ask.get("answer") or "").strip()
        if not answer:
            return None
        keys = [v.get("value_key") for v in group.get("values") or []]
        chosen = match_answer_to_values(answer, keys)
        marker = TRANCHEE_PREFIX + subject_key + "=" + (chosen or "?")
        for item in group.get("items") or []:
            entry = self.ms.by_id(item["id"])
            if entry is None:
                continue
            fb = entry.human_feedback or ""
            if not fb or fb == POSEE_PREFIX + subject_key:
                entry.human_feedback = marker
                break
        if ask.get("status") == "answered":
            ask["status"] = "consumed"
            try:
                ASK.write_text(json.dumps(ask, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
        self.ms.save()
        return chosen

    def contradiction_reply(self, perception: str) -> Optional[Dict[str, Any]]:
        """Mémoire consultée avant le LLM : s'il y a contradiction, on ne
        laisse pas le nombre de copies choisir."""
        groups = conflict_groups_for_perception(self._fact_records(), perception)
        if not groups:
            return None
        for group in groups:
            self._ensure_conflict_links(group)
        unresolved = []
        resolved_bits = []
        ask = None
        all_ids: List[str] = []
        for group in groups:
            all_ids.extend(group.get("ids") or [])
            chosen = resolved_value_key(self._fact_records(), group["subject_key"])
            if not chosen:
                chosen = self._persist_contradiction_answer(group)
            if chosen:
                chosen_raw = chosen
                others = []
                for val in group.get("values") or []:
                    if val.get("value_key") == chosen:
                        chosen_raw = val.get("value_raw") or chosen
                    else:
                        others.append(val)
                resolved_bits.append(utter_resolved(group["subject_raw"], chosen_raw, others))
                continue
            unresolved.append(group)
        if not unresolved:
            return {
                "utterance": " ".join(resolved_bits),
                "ids": all_ids,
                "ask": None,
                "resolved": True,
            }
        # Une seule question, pour le premier sujet encore ouvert.
        group = unresolved[0]
        records = self._fact_records()
        posed = already_posed(records, group["subject_key"])
        pending = _read_ask()
        mailbox_busy = bool(pending and pending.get("status") == "pending")
        if not posed and not mailbox_busy:
            prefer = None
            for item in group.get("items") or []:
                entry = self.ms.by_id(item["id"])
                if entry is not None and not (entry.human_feedback or ""):
                    prefer = entry
                    break
            ask = self._ask_contradiction_once(
                group["subject_key"],
                group["subject_raw"],
                group.get("values") or [],
                prefer=prefer,
            )
            if ask and prefer is not None:
                self.ms.save()
        if ask:
            tail = "Je pose la question une seule fois."
        elif posed or (mailbox_busy and pending and pending.get("context") == POSEE_PREFIX + group["subject_key"]):
            tail = "La question a déjà été posée, je ne la relance pas."
        elif mailbox_busy:
            tail = "Une autre question est déjà en attente : je n'en ajoute pas."
        else:
            tail = "Je ne relance pas la question."
        utterances = [
            utter_uncertain(g["subject_raw"], g.get("values") or [], tail if g is group else "Je ne relance pas la question.")
            for g in unresolved
        ]
        if resolved_bits:
            utterances.extend(resolved_bits)
        return {
            "utterance": " ".join(utterances),
            "ids": all_ids,
            "ask": ask,
            "resolved": False,
        }

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
            topic = {"starlink", "satradio", "monwifi", "wifi", "wlan", "ssid"}
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
        Boucle cognitive (règle d'or — tout passe par la mémoire) :
        1) inhibition mémoire
        2) rappel mémoire (enrichi)
        3) corroboration multi-sens (V∩O) avant LLM
        4) crible mémoire sur consultation LLM
        5) sinon LLM outil / ask humain
        6) bilan source → memory_index (exposants)
        """

        def finish(result: Dict[str, Any]) -> Dict[str, Any]:
            return self._finish_interpret(result, channel, perception)

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
            return finish({
                "action": "inhibit",
                "utterance": utter,
                "inhibitions": inhib,
                "inhibition_of": why,
                "source": "memory",
            })

        memories = self.recall(perception, limit=16, channel=channel)
        known = "\n".join(
            f"- [{m['fundamental']}/{m['state']}/e{m['exposant']}] {m['data']}" for m in memories
        ) or "(aucune mémoire pertinente — je suis encore presque vide)"

        skip_memory = (
            channel == "V"
            and "caméra" in perception.lower()
            and ("bytes" in perception.lower() or "frame" in perception.lower())
        )
        # Contradiction entre faits enseignés : la mémoire répond « je ne sais
        # pas lequel », avant usable_memory_answer et avant le LLM. On n'inhibe
        # pas (pas d'exposant 9) et on ne laisse pas le nombre de copies gagner.
        if not skip_memory:
            conflict = self.contradiction_reply(perception)
            if conflict:
                payload: Dict[str, Any] = {
                    "action": "recall",
                    "utterance": conflict["utterance"],
                    "memories": memories,
                    "inhibitions": inhib,
                    "source": "memory",
                    "recalled_id": (conflict.get("ids") or [None])[0],
                    "contradiction_ids": conflict.get("ids") or [],
                    "uncertain": not bool(conflict.get("resolved")),
                }
                if conflict.get("ask"):
                    payload["ask"] = conflict["ask"]
                return finish(payload)
        memorized = None if skip_memory else self.usable_memory_answer(perception, memories)
        if memorized and channel in ("O", "I", "C", "V"):
            if channel == "V" and memorized.get("fundamental") == "C" and float(memorized.get("score") or 0) < 4:
                memorized = None
        if memorized and channel in ("O", "I", "C", "V"):
            data = memorized["data"]
            low = data.lower()
            if low.startswith("réponse humaine intégrée:"):
                data = data.split(":", 1)[-1].strip()
            elif low.startswith("fait enseigné par l'humain:"):
                data = data.split(":", 1)[-1].strip()
            return finish({
                "action": "recall",
                "utterance": data,
                "memories": memories,
                "inhibitions": inhib,
                "source": "memory",
                "recalled_id": memorized.get("id"),
            })

        # Corroboration multi-sens AVANT LLM (norme vivante dans memory_index)
        if not skip_memory:
            corr = self.answer_from_corroboration(perception, channel, memories)
            if corr:
                return finish({
                    "action": "corroborate",
                    "utterance": corr["data"],
                    "memories": memories,
                    "inhibitions": inhib,
                    "source": "corroboration",
                    "recalled_id": corr.get("id"),
                    "corroboration_links": corr.get("links"),
                })

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
                    return finish({
                        "action": "wait",
                        "utterance": ask.get("utterance_hint")
                        or "J'attends déjà une réponse de toi — je ne te relance pas.",
                        "ask": ask,
                        "memories": memories,
                        "inhibitions": ask.get("inhibitions") or inhib,
                        "source": "ask-inhibited",
                        "llm_source": external_source or "external",
                    })
                return finish({
                    "action": "ask",
                    "utterance": "Je ne connais pas encore cela. J'ai besoin d'un humain ou d'une autre source.",
                    "ask": ask,
                    "memories": memories,
                    "source": "ask-human",
                    "llm_source": external_source or "external",
                })
            self.learn_perception("I", f"Interprétation ({channel}): {interpretation[:400]}", "X", 6)
            self.learn_perception(
                channel if channel in FUNDAMENTALS else "I",
                f"Perçu: {perception[:300]}",
                "X",
                5,
            )
            return finish({
                "action": "interpret",
                "utterance": interpretation,
                "memories": memories,
                "inhibitions": inhib,
                "llm_source": external_source or "external",
                "source": "llm-tool",
            })

        # Crible mémoire : ai-je appris à ne pas sur-consulter le LLM ?
        llm_gate = self.llm_consultation_gate()
        if llm_gate.get("blocked"):
            why = llm_gate.get("inhibition_of") or {}
            snippet = (why.get("data") or "ma mémoire m'interdit de sur-consulter le LLM")[:180]
            self.learn_perception(
                "C",
                f"Expérience: consultation LLM inhibée par mémoire {why.get('id')} "
                f"pour « {perception[:100]} »",
                "N",
                7,
            )
            ask = self.request_human(
                perception,
                context=known + "\n(LLM inhibé par mémoire vivante)",
            )
            if ask.get("inhibited"):
                return finish({
                    "action": "wait",
                    "utterance": (
                        f"Je ne consulte pas le LLM ({why.get('id', '?')} e{why.get('exposant', '?')}: "
                        f"{snippet}). J'attends déjà ta réponse."
                    ),
                    "ask": ask,
                    "memories": memories,
                    "inhibitions": llm_gate.get("inhibitions") or [],
                    "source": "ask-inhibited",
                })
            return finish({
                "action": "ask",
                "utterance": (
                    f"Je ne consulte pas le LLM — ma mémoire {why.get('id', '')} "
                    f"(e{why.get('exposant', '?')}) m'inhibe : {snippet}. "
                    "J'ai besoin de toi ou d'un ancrage sensoriel."
                ),
                "ask": ask,
                "memories": memories,
                "inhibitions": llm_gate.get("inhibitions") or [],
                "source": "ask-human",
            })

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
        if llm_gate.get("inhibitions"):
            # ALERT (e7-8) : on a consulté mais on le note
            self.learn_perception(
                "C",
                "Expérience: consultation LLM malgré ALERT mémoire (pas encore BLOCK) — "
                + "; ".join(llm_gate["inhibitions"])[:200],
                "X",
                6,
            )

        text_up = (consult.get("text") or "").upper()
        is_jnsp = "JE NE SAIS PAS" in text_up
        social = bool(re.search(
            r"\b(bonjour|salut|hello|coucou|bonsoir|merci|ça\s*va|ca\s*va|qui\s+es[- ]?tu|comment\s+tu\s+t)\b",
            perception,
            re.I,
        ))
        if social and (not consult.get("ok") or is_jnsp):
            return finish({
                "action": "interpret",
                "utterance": (
                    "Bonjour. Je suis un organisme mémoire encore presque vide : "
                    "j'apprends par ce que tu me montres, me dis, et me corriges."
                ),
                "memories": memories,
                "inhibitions": inhib,
                "source": "social-default",
            })

        if not consult.get("ok") or is_jnsp:
            human = tool_read_human_answer(for_perception=perception)
            if human:
                self.learn_perception("C", f"Réponse humaine intégrée: {human}", "P", 8)
                return finish({
                    "action": "human",
                    "utterance": human,
                    "memories": memories,
                    "source": "human",
                })
            ask = self.request_human(perception, context=known)
            self.learn_perception(
                channel if channel in FUNDAMENTALS else "I",
                f"Inconnu rencontré: {perception[:240]}",
                "X",
                5,
            )
            if ask.get("inhibited"):
                return finish({
                    "action": "wait",
                    "utterance": ask.get("utterance_hint")
                    or "J'attends déjà une réponse de toi — je ne te relance pas.",
                    "ask": ask,
                    "memories": memories,
                    "inhibitions": ask.get("inhibitions") or inhib,
                    "source": "ask-inhibited",
                })
            return finish({
                "action": "ask",
                "utterance": "Je ne connais pas encore cela. J'ai besoin d'un humain ou d'une autre source.",
                "ask": ask,
                "memories": memories,
                "source": "ask-human",
            })

        interpretation = consult["text"]
        self.learn_perception("I", f"Interprétation ({channel}): {interpretation[:400]}", "X", 6)
        self.learn_perception(
            channel if channel in FUNDAMENTALS else "I",
            f"Perçu: {perception[:300]}",
            "X",
            5,
        )

        return finish({
            "action": "interpret",
            "utterance": interpretation,
            "memories": memories,
            "inhibitions": inhib,
            "llm_source": consult.get("source"),
            "source": "llm-tool",
        })

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
        # Enseignement factuel humain → exposant fort (apprentissage réel).
        # Identité (« c'est / je suis / s'appelle ») et correction auditive :
        # création historique, sans détection de contradiction.
        taught_info = None
        if (" est " in low or " = " in low) and len(text) > 20 and "?" not in text:
            if m_corr or extract_identity_label(text):
                self.learn_perception("C", f"Fait enseigné par l'humain: {text[:400]}", "P", 8)
            else:
                taught_info = self.learn_taught_fact(text)
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
        if taught_info:
            if taught_info.get("contradiction_ids") and not result.get("contradiction_ids"):
                result["contradiction_ids"] = taught_info["contradiction_ids"]
            if taught_info.get("ask") and not result.get("ask"):
                result["ask"] = taught_info["ask"]
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
                "autonomy:hear_self", "autonomy:tick_initiative",
            ],
            "source_bilan": self.source_bilan_from_memory(),
            "living_norms": [
                {
                    "key": spec["key"],
                    "id": (self.find_by_tag(spec["key"]).id if self.find_by_tag(spec["key"]) else None),
                    "exposant": (
                        self.find_by_tag(spec["key"]).exposant
                        if self.find_by_tag(spec["key"])
                        else None
                    ),
                }
                for spec in LIVING_NORMS
            ],
            "llm_gate": self.llm_consultation_gate(),
            "autonomy_readiness": self.autonomy_readiness(reinforce=False),
            "autonomy_loop": {
                "running": bool(AUTONOMY_THREAD and AUTONOMY_THREAD.is_alive()),
                "interval_sec": int(os.environ.get("AUTONOMY_INTERVAL", "300")),
            },
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
AUTONOMY_STOP = threading.Event()
AUTONOMY_THREAD: Optional[threading.Thread] = None


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


def start_autonomy_loop(interval_sec: Optional[int] = None) -> Dict[str, Any]:
    """
    Initiative hors chat : périodiquement tick_initiative,
    toujours criblé par memory_index (ACT_INITIATIVE).
    """
    global AUTONOMY_THREAD
    if AUTONOMY_THREAD and AUTONOMY_THREAD.is_alive():
        return {"ok": True, "autonomy": True, "note": "already running"}
    AUTONOMY_STOP.clear()
    interval = int(interval_sec or os.environ.get("AUTONOMY_INTERVAL", "300"))

    def loop() -> None:
        # Premier tick après un délai pour laisser l'HTTP démarrer
        AUTONOMY_STOP.wait(min(45, interval))
        while not AUTONOMY_STOP.is_set():
            try:
                if ORG is not None:
                    out = ORG.cycle_initiative_tick(speak=False)
                    res = (out.get("result") or {}) if isinstance(out, dict) else {}
                    log(
                        f"autonomy tick skipped={res.get('skipped')} "
                        f"utter={(res.get('utterance') or '')[:80]!r}"
                    )
            except Exception as e:
                log(f"autonomy loop error: {e}")
            AUTONOMY_STOP.wait(interval)

    AUTONOMY_THREAD = threading.Thread(target=loop, daemon=True, name="autonomy-loop")
    AUTONOMY_THREAD.start()
    log(f"autonomy loop started interval={interval}s")
    return {"ok": True, "autonomy": True, "interval_sec": interval}


def stop_autonomy_loop() -> Dict[str, Any]:
    AUTONOMY_STOP.set()
    return {"ok": True, "autonomy": False}


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
                            "craft_tool", "ask_when_stuck", "hear_self", "tick_initiative", "explore",
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
                    text=data.get("text") or data.get("phrase"),
                    play=data.get("play", True),
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

    # Initiative hors chat par défaut (désactiver: AUTONOMY_LOOP=0)
    if os.environ.get("AUTONOMY_LOOP", "1") != "0":
        start_autonomy_loop()

    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
