#!/usr/bin/env python3
"""
Mémoire vocale structurée (sens O) — empreintes voix → identité.

Empreinte légère : bandes spectrales (log-énergie) + stats énergie/pitch
sur WAV mono 16 kHz. Suffisant pour lier des prises micro successives
du même locuteur dans la nursery (ex. Vincent).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import struct
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional

MATCH_THRESHOLD = 0.78
MAX_EMBS_PER_PERSON = 10
N_BANDS = 32
MIN_SPEECH_SEC = 0.35


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _l2(vec: List[float]) -> List[float]:
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


def _load_wav_mono(path: Path) -> Optional[tuple]:
    """Retourne (sample_rate, samples float -1..1) ou None."""
    try:
        import numpy as np  # type: ignore

        with wave.open(str(path), "rb") as w:
            ch = w.getnchannels()
            sr = w.getframerate()
            sw = w.getsampwidth()
            n = w.getnframes()
            raw = w.readframes(n)
        if sw == 2:
            x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sw == 1:
            x = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            return None
        if ch > 1:
            x = x.reshape(-1, ch).mean(axis=1)
        return sr, x
    except Exception:
        return None


def _trim_speech(x, sr: int):
    import numpy as np  # type: ignore

    if x.size < int(MIN_SPEECH_SEC * sr):
        return x
    frame = max(1, int(0.02 * sr))
    hop = max(1, frame // 2)
    energies = []
    for i in range(0, len(x) - frame, hop):
        energies.append(float(np.mean(x[i : i + frame] ** 2)))
    if not energies:
        return x
    thr = max(float(np.median(energies)) * 0.4, 1e-5)
    keep = [i for i, e in enumerate(energies) if e >= thr]
    if not keep:
        return x
    start = keep[0] * hop
    end = min(len(x), keep[-1] * hop + frame)
    return x[start:end]


def embed_voice(wav_path: str | Path) -> Optional[List[float]]:
    """
    Empreinte vocale locale.
    Vecteur = mean+std des log-énergies par bande (N_BANDS*2)
            + pitch proxy + énergie globale (~ N_BANDS*2+4).
    """
    try:
        import numpy as np  # type: ignore
    except Exception:
        return None

    loaded = _load_wav_mono(Path(wav_path))
    if not loaded:
        return None
    sr, x = loaded
    if x.size < int(0.2 * sr):
        return None
    x = _trim_speech(x, sr)
    if x.size < int(MIN_SPEECH_SEC * sr):
        return None

    # Pre-emphasis
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])

    frame = int(0.025 * sr)
    hop = int(0.010 * sr)
    n_fft = 512
    window = np.hanning(frame)
    # Mel-ish band edges en Hz (lin → log)
    fmin, fmax = 80.0, min(7000.0, sr / 2 - 1)
    edges = np.exp(np.linspace(np.log(fmin), np.log(fmax), N_BANDS + 1))
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

    band_feats = []
    pitches = []
    energies = []
    for i in range(0, len(x) - frame, hop):
        seg = x[i : i + frame] * window
        # pad to n_fft
        if len(seg) < n_fft:
            seg = np.pad(seg, (0, n_fft - len(seg)))
        else:
            seg = seg[:n_fft]
        spec = np.abs(np.fft.rfft(seg)) ** 2
        energies.append(float(np.mean(seg**2) + 1e-12))
        bands = []
        for b0, b1 in zip(edges[:-1], edges[1:]):
            mask = (freqs >= b0) & (freqs < b1)
            bands.append(float(np.log(spec[mask].sum() + 1e-12)))
        band_feats.append(bands)
        # pitch proxy: argmax in 80-400 Hz
        pmask = (freqs >= 80) & (freqs <= 400)
        if pmask.any():
            pitches.append(float(freqs[pmask][int(np.argmax(spec[pmask]))]))

    if not band_feats:
        return None

    M = np.asarray(band_feats, dtype=np.float32)
    mean = M.mean(axis=0)
    std = M.std(axis=0)
    pitch_mean = float(np.mean(pitches)) if pitches else 0.0
    pitch_std = float(np.std(pitches)) if pitches else 0.0
    eng_mean = float(np.log(np.mean(energies) + 1e-12))
    eng_std = float(np.log(np.std(energies) + 1e-12))
    vec = np.concatenate([mean, std, [pitch_mean / 400.0, pitch_std / 100.0, eng_mean, eng_std]])
    return _l2(vec.tolist())


# Les fichiers de ma propre synthèse vocale commencent par « tts_self_ ».
# Pourquoi : ma voix de synthèse n'est pas une personne ; elle avait créé une
# fausse fiche voix (VP002). Tout clip ainsi nommé est donc ignoré.
TTS_SELF_PREFIX = "tts_self_"


def _is_tts_self(clip: Any) -> bool:
    """Clip de ma propre synthèse vocale : jamais une voix humaine."""
    return bool(clip) and Path(str(clip)).name.startswith(TTS_SELF_PREFIX)


class VoicePersonMemory:
    """Persistance JSON des identités vocales."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: Dict[str, Any] = {
            "schema": "voice_persons/v1",
            "persons": [],
            "pending": [],
            "last_seen": None,
        }
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        self.data.setdefault("persons", [])
        self.data.setdefault("pending", [])
        self.data.setdefault("last_seen", None)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _next_id(self, prefix: str) -> str:
        keys = [p["id"] for p in self.data["persons"]] + [p["id"] for p in self.data["pending"]]
        n = 1
        while f"{prefix}{n:03d}" in keys:
            n += 1
        return f"{prefix}{n:03d}"

    def _mean_emb(self, person: Dict[str, Any]) -> Optional[List[float]]:
        embs = person.get("embeddings") or []
        if not embs:
            return None
        dim = len(embs[0])
        acc = [0.0] * dim
        for e in embs:
            if len(e) != dim:
                continue
            for i, v in enumerate(e):
                acc[i] += float(v)
        return _l2([v / len(embs) for v in acc])

    def match(self, embedding: List[float]) -> Optional[Dict[str, Any]]:
        best = None
        best_score = 0.0
        for p in self.data["persons"]:
            mean = self._mean_emb(p)
            if not mean:
                continue
            sc = cosine(embedding, mean)
            for e in p.get("embeddings") or []:
                sc = max(sc, cosine(embedding, e))
            if sc > best_score:
                best_score = sc
                best = {"person": p, "score": round(sc, 4)}
        if best and best["score"] >= MATCH_THRESHOLD:
            return best
        return None

    def reinforce(self, person_id: str, embedding: List[float], wav: str, transcript: str = "") -> Dict[str, Any]:
        for p in self.data["persons"]:
            if p["id"] != person_id:
                continue
            embs = p.setdefault("embeddings", [])
            embs.append(embedding)
            if len(embs) > MAX_EMBS_PER_PERSON:
                p["embeddings"] = embs[-MAX_EMBS_PER_PERSON:]
            clips = p.setdefault("clips", [])
            name = Path(wav).name
            if name not in clips:
                clips.append(name)
                if len(clips) > 24:
                    p["clips"] = clips[-24:]
            p["seen_count"] = int(p.get("seen_count") or 0) + 1
            p["exposant"] = min(10, int(p.get("exposant") or 5) + 1)
            if transcript:
                p["last_transcript"] = transcript[:200]
            p["updated_at"] = _now()
            self.data["last_seen"] = {
                "kind": "person",
                "id": p["id"],
                "label": p.get("label"),
                "clip": name,
                "at": _now(),
            }
            self.save()
            return p
        raise KeyError(person_id)

    def create_pending(self, embedding: List[float], wav: str, transcript: str = "") -> Dict[str, Any]:
        name = Path(wav).name
        item = {
            "id": self._next_id("VU"),
            "embedding": embedding,
            "clip": name,
            "transcript": (transcript or "")[:200],
            "created_at": _now(),
        }
        self.data["pending"].append(item)
        self.data["pending"] = self.data["pending"][-12:]
        self.data["last_seen"] = {
            "kind": "pending",
            "id": item["id"],
            "label": None,
            "clip": name,
            "at": _now(),
        }
        self.save()
        return item

    def label_pending_or_last(self, label: str, exposant: int = 8) -> Optional[Dict[str, Any]]:
        self.load()
        label = (label or "").strip()
        if not label:
            return None
        last = self.data.get("last_seen") or {}
        if _is_tts_self(last.get("clip")):
            last = {}
        if last.get("kind") == "person" and last.get("id"):
            for p in self.data["persons"]:
                if p["id"] == last["id"]:
                    p["label"] = label
                    p["exposant"] = max(int(p.get("exposant") or 0), exposant)
                    p["updated_at"] = _now()
                    self.save()
                    return p

        pending = None
        if last.get("kind") == "pending" and last.get("id"):
            for u in self.data["pending"]:
                if u["id"] == last["id"]:
                    pending = u
                    break
        if pending is not None and _is_tts_self(pending.get("clip")):
            pending = None
        if pending is None:
            humans = [u for u in self.data["pending"] if not _is_tts_self(u.get("clip"))]
            if humans:
                pending = humans[-1]
        if pending is None:
            person = {
                "id": self._next_id("VP"),
                "label": label,
                "embeddings": [],
                "clips": [],
                "seen_count": 0,
                "exposant": exposant,
                "created_at": _now(),
                "updated_at": _now(),
            }
            self.data["persons"].append(person)
            self.save()
            return person

        existing = None
        for p in self.data["persons"]:
            if (p.get("label") or "").lower() == label.lower():
                existing = p
                break
        if existing is not None:
            embs = existing.setdefault("embeddings", [])
            if pending.get("embedding"):
                embs.append(pending["embedding"])
                existing["embeddings"] = embs[-MAX_EMBS_PER_PERSON:]
            clips = existing.setdefault("clips", [])
            if pending.get("clip") and pending["clip"] not in clips:
                clips.append(pending["clip"])
            existing["seen_count"] = int(existing.get("seen_count") or 0) + 1
            existing["exposant"] = max(int(existing.get("exposant") or 0), exposant)
            existing["updated_at"] = _now()
            self.data["pending"] = [u for u in self.data["pending"] if u["id"] != pending["id"]]
            self.data["last_seen"] = {
                "kind": "person",
                "id": existing["id"],
                "label": existing.get("label"),
                "clip": pending.get("clip"),
                "at": _now(),
            }
            self.save()
            return existing

        person = {
            "id": self._next_id("VP"),
            "label": label,
            "embeddings": [pending["embedding"]] if pending.get("embedding") else [],
            "clips": [pending["clip"]] if pending.get("clip") else [],
            "seen_count": 1,
            "exposant": exposant,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.data["persons"].append(person)
        self.data["pending"] = [u for u in self.data["pending"] if u["id"] != pending["id"]]
        self.data["last_seen"] = {
            "kind": "person",
            "id": person["id"],
            "label": label,
            "clip": pending.get("clip"),
            "at": _now(),
        }
        self.save()
        return person

    def process_wav(self, wav_path: str | Path, transcript: str = "") -> Dict[str, Any]:
        self.load()  # sync disque (inscription hors process / multi-outil)
        if _is_tts_self(wav_path):
            return {"ok": False, "error": "tts_self ignoré", "recognized": None, "unknown": None}
        emb = embed_voice(wav_path)
        if not emb:
            return {"ok": False, "error": "no voice embedding", "recognized": None, "unknown": None}
        m = self.match(emb)
        if m:
            person = self.reinforce(m["person"]["id"], emb, str(wav_path), transcript)
            return {
                "ok": True,
                "recognized": {
                    "id": person["id"],
                    "label": person.get("label"),
                    "score": m["score"],
                    "exposant": person.get("exposant"),
                    "seen_count": person.get("seen_count"),
                },
                "unknown": None,
            }
        pend = self.create_pending(emb, str(wav_path), transcript)
        return {
            "ok": True,
            "recognized": None,
            "unknown": {"id": pend["id"], "clip": pend["clip"], "transcript": pend.get("transcript")},
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "persons": [
                {
                    "id": p["id"],
                    "label": p.get("label"),
                    "exposant": p.get("exposant"),
                    "seen_count": p.get("seen_count"),
                    "clips": len(p.get("clips") or []),
                    "embeddings": len(p.get("embeddings") or []),
                }
                for p in self.data["persons"]
            ],
            "pending": len(self.data.get("pending") or []),
            "last_seen": self.data.get("last_seen"),
        }
