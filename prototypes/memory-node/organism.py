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
import datetime as dt
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
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

STATE = ROOT / "state"
INDEX = ROOT / "MemorySystemAI" / "memory_index.json"
ASK = STATE / "ask_human.json"
LOG = STATE / "organism.log"
SNAPS = STATE / "snapshots"
UI_DIR = ROOT / "ui"
UI_INDEX = UI_DIR / "index.html"

OLLAMA_LOCAL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
OLLAMA_FALLBACK = os.environ.get("OLLAMA_FALLBACK", "")
PUTER_AUTH_TOKEN = os.environ.get("PUTER_AUTH_TOKEN", "").strip()
PUTER_MODEL = os.environ.get("PUTER_MODEL", "moonshotai/kimi-k2")
PUTER_BASE = os.environ.get(
    "PUTER_BASE",
    "https://api.puter.com/puterai/openai/v1",
).rstrip("/")
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
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty"}
    try:
        sh(["espeak-ng", "-v", "fr", "-s", "145", text[:500]], timeout=90)
        return {"ok": True, "said": text[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e), "said": text}


def tool_see() -> Dict[str, Any]:
    SNAPS.mkdir(parents=True, exist_ok=True)
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


def tool_hear(seconds: float = 4.0) -> Dict[str, Any]:
    STATE.mkdir(parents=True, exist_ok=True)
    wav = STATE / f"o_{int(time.time())}.wav"
    try:
        p = sh([
            "arecord", "-D", "plughw:0,0", "-f", "S16_LE", "-r", "16000", "-c", "1",
            "-d", str(max(1, int(seconds))), str(wav),
        ], timeout=int(seconds) + 15)
        if not (wav.exists() and wav.stat().st_size > 1000):
            return {"ok": False, "error": (p.stderr or "record failed")[-300:]}
        text = ""
        try:
            from faster_whisper import WhisperModel
            global _whisper
            if "_whisper" not in globals() or _whisper is None:
                globals()["_whisper"] = WhisperModel("tiny", device="cpu", compute_type="int8")
            segs, _ = globals()["_whisper"].transcribe(str(wav), language="fr", vad_filter=True)
            text = " ".join(s.text.strip() for s in segs).strip()
        except Exception as e:
            return {"ok": True, "wav": str(wav), "text": "", "stt_error": str(e)}
        return {"ok": True, "wav": str(wav), "text": text}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_consult_puter(prompt: str, system: str) -> Dict[str, Any]:
    """Consult Kimi (or other Puter models) via OpenAI-compatible Puter API."""
    token = _load_puter_token()
    if not token:
        return {"ok": False, "error": "no puter token", "text": ""}
    payload = {
        "model": PUTER_MODEL,
        "stream": False,
        "temperature": 0.4,
        "max_tokens": 400,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
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
                "source": f"puter:{PUTER_MODEL}",
                "text": content,
                "provider": "puter",
            }
        return {"ok": False, "error": "empty puter response", "text": "", "raw": body}
    except Exception as e:
        log(f"consult_puter fail: {e}")
        return {"ok": False, "error": str(e), "text": ""}


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
    """Consult external LLM(s) as a tool — not as identity. Prefer Puter/Kimi, then Ollama."""
    puter = tool_consult_puter(prompt, system)
    if puter.get("ok"):
        return puter
    return tool_consult_ollama(prompt, system, bases=bases)


def tool_ask_human(question: str, context: str = "") -> Dict[str, Any]:
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
        log("blank memory_index created")

    def _seed_bootstrap(self) -> None:
        for fund, state, exp, data in BOOTSTRAP:
            self.ms.create(fund, state, exp, data, source="bootstrap")
        self.ms.save()
        log(f"bootstrap seeded ({len(BOOTSTRAP)} meta entries)")

    def memory_only_inhibition(self, action_text: str) -> List[str]:
        """Inhibition uniquement via mémoires apprises (pas RISK_PATTERNS texte)."""
        msgs: List[str] = []
        for e in self.ms.entries.values():
            if e.exposant < THRESHOLD_INJECT:
                continue
            if e.matches_tags(action_text) or (
                e.data and any(tok in action_text.lower() for tok in e.data.lower().split() if len(tok) > 4)
            ):
                msg = e.inhibition_message(action_text)
                if msg:
                    msgs.append(msg)
                elif e.exposant >= THRESHOLD_BLOCK:
                    msgs.append(f"[BLOCK exposant {e.exposant}] {e.data}")
                else:
                    msgs.append(f"[ALERT exposant {e.exposant}] {e.data}")
        return msgs

    def recall(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        q = query.lower()
        q_toks = [tok for tok in q.replace("?", " ").replace("'", " ").split() if len(tok) > 2]
        scored = []
        for e in self.ms.entries.values():
            blob = f"{e.data} {' '.join(e.inhibition_tags or [])}".lower()
            score = 0.0
            for tok in q_toks:
                if tok in blob:
                    score += 1.0
                    if len(tok) > 8:
                        score += 1.5  # noms propres longs (ex. SatRadio…)
            score += e.exposant / 10.0
            src = (e.source or "").lower()
            data_l = (e.data or "").lower()
            if src == "human" or data_l.startswith("fait enseigné") or "réponse humaine intégrée" in data_l:
                score += 3.0
            # Déprioriser le bruit de journal
            if data_l.startswith(("message reçu:", "perçu:", "interprétation (", "inconnu rencontré:")):
                score -= 2.0
            if score > 0.5:
                scored.append((score, e))
        scored.sort(key=lambda x: -x[0])
        out = []
        for score, e in scored[:limit]:
            out.append({
                "id": e.id,
                "fundamental": e.fundamental,
                "state": e.state,
                "exposant": e.exposant,
                "data": e.data,
                "score": round(score, 2),
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
        )
        perc = perception.lower()
        candidates = []
        for m in memories:
            data = (m.get("data") or "").strip()
            low = data.lower()
            if any(low.startswith(p) for p in skip_prefixes):
                continue
            score = float(m.get("score") or 0)
            exp = int(m.get("exposant") or 0)
            # Au moins un ancrage lexical avec la question (évite de ressortir n'importe quelle mémoire e8)
            anchors = [t for t in perc.replace("?", " ").replace("'", " ").split() if len(t) > 4]
            hit = sum(1 for t in anchors if t in low)
            if hit < 1 and score < 2.5:
                continue
            if score < 1.4 and exp < THRESHOLD_INJECT:
                continue
            weight = score + exp / 10.0 + hit
            if exp >= THRESHOLD_INJECT:
                weight += 2
            if low.startswith("fait enseigné") or "réponse humaine intégrée" in low:
                weight += 2
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
            return {
                "action": "inhibit",
                "utterance": "Je ressens une inhibition forte issue de mes mémoires. Je m'abstiens.",
                "inhibitions": inhib,
                "source": "memory",
            }

        memories = self.recall(perception, limit=16)
        known = "\n".join(
            f"- [{m['fundamental']}/{m['state']}/e{m['exposant']}] {m['data']}" for m in memories
        ) or "(aucune mémoire pertinente — je suis encore presque vide)"

        # Mémoire d'abord — même si Kimi a proposé quelque chose côté navigateur
        memorized = self.usable_memory_answer(perception, memories)
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
                ask = tool_ask_human(perception, context=known)
                self.learn_perception(
                    channel if channel in FUNDAMENTALS else "I",
                    f"Inconnu rencontré: {perception[:240]}",
                    "X",
                    5,
                )
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
            "Réponds en français, factuel, court. "
            "Si les mémoires ci-dessous contiennent déjà la réponse, reformule UNIQUEMENT à partir d'elles. "
            "Si tu n'as pas assez d'info : réponds exactement JE NE SAIS PAS.\n"
            f"Mémoires déjà connues de l'organisme:\n{known}"
        )
        consult = tool_consult_llm(
            prompt=f"Canal sensoriel={channel}. Perception brute:\n{perception}\n\nQue puis-je en comprendre / apprendre ?",
            system=system,
        )

        if not consult.get("ok") or "JE NE SAIS PAS" in (consult.get("text") or "").upper():
            human = tool_read_human_answer(for_perception=perception)
            if human:
                self.learn_perception("C", f"Réponse humaine intégrée: {human}", "P", 8)
                return {
                    "action": "human",
                    "utterance": human,
                    "memories": memories,
                    "source": "human",
                }
            ask = tool_ask_human(perception, context=known)
            utterance = "Je ne connais pas encore cela. J'ai besoin d'un humain ou d'une autre source."
            self.learn_perception(channel if channel in FUNDAMENTALS else "I", f"Inconnu rencontré: {perception[:240]}", "X", 5)
            return {
                "action": "ask",
                "utterance": utterance,
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

    def cycle_hear(self, seconds: float = 4.0, speak: bool = True) -> Dict[str, Any]:
        heard = tool_hear(seconds)
        if not heard.get("ok"):
            return {"ok": False, "error": heard.get("error")}
        text = heard.get("text") or ""
        if not text:
            return {"ok": True, "heard": "", "note": "silence / STT vide", "wav": heard.get("wav")}
        self.learn_perception("O", f"Entendu: {text}", "X", 5)
        result = self.interpret_with_tools(text, "O")
        if speak:
            tool_speak(result.get("utterance", ""))
        return {"ok": True, "heard": text, "result": result}

    def cycle_see(self, speak: bool = False) -> Dict[str, Any]:
        seen = tool_see()
        if not seen.get("ok"):
            return seen
        raw = seen.get("raw", "")
        self.learn_perception("V", f"Vu: {raw}", "X", 5)
        result = self.interpret_with_tools(
            f"J'ai capturé une image caméra (fichier {seen.get('path')}). Données brutes: {raw}. "
            f"Sans modèle vision, indique seulement ce que cela implique pour un organisme qui apprend, "
            f"ou dis JE NE SAIS PAS si tu ne peux rien en dire.",
            "V",
        )
        if speak:
            tool_speak(result.get("utterance", ""))
        result["frame"] = seen
        return {"ok": True, "result": result}

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
        low = text.lower()
        # Enseignement factuel humain → exposant fort (apprentissage réel)
        if (" est " in low or " = " in low) and len(text) > 20 and "?" not in text:
            self.learn_perception("C", f"Fait enseigné par l'humain: {text[:400]}", "P", 8)
        if any(x in low for x in ("bien", "bravo", "correct", "merci", "oui c'est ça")):
            self.learn_from_feedback(text, True)
        # Ne pas traiter un rappel conceptuel contenant le mot "interdit" comme punition
        if any(x in low for x in ("non", "faux", "mal", "arrête", "erreur")) and "interdit texte" not in low:
            self.learn_from_feedback(text, False)
        self.learn_perception("C", f"Message reçu: {text[:300]}", "X", 5)
        result = self.interpret_with_tools(
            text,
            "C",
            external_interpretation=external_interpretation,
            external_source=external_source,
        )
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
        return {
            "role": "MemorySystemAI-organism",
            "not": "chatbot-with-text-rules",
            "memories": len(self.ms.entries),
            "bootstrap_only_meta": all(
                getattr(e, "source", "") == "bootstrap" for e in self.ms.entries.values()
            ),
            "tools": ["see", "hear", "speak", "consult_llm", "consult_puter_kimi", "ask_human"],
            "model_tool": PUTER_MODEL if puter_ready else OLLAMA_MODEL,
            "puter": {
                "enabled": puter_ready,
                "model": PUTER_MODEL,
                "browser_fallback": True,
                "docs": "https://developer.puter.com/ai/moonshotai/kimi-k3/",
            },
            "ask_pending": pending,
            "camera": os.path.exists("/dev/video0"),
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
        if path.startswith("/ask"):
            if ASK.exists():
                self._json(200, json.loads(ASK.read_text(encoding="utf-8")))
            else:
                self._json(200, {"status": "none"})
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
        if self.path.startswith("/see"):
            self._json(200, ORG.cycle_see(speak=bool(data.get("speak", False))))
            return
        if self.path.startswith("/hear") or self.path.startswith("/listen"):
            self._json(200, ORG.cycle_hear(seconds=float(data.get("seconds") or 4), speak=bool(data.get("speak", True))))
            return
        if self.path.startswith("/speak"):
            self._json(200, tool_speak(str(data.get("text") or "")))
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
