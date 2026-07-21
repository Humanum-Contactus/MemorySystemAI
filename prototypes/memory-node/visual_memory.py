#!/usr/bin/env python3
"""
Mémoire visuelle structurée (sens V) — empreintes visage → identité.

Pas un réseau de reconnaissance facial commercial : empreinte locale légère
(grille luminance + histogramme) sur crop visage (OpenCV Haar si dispo,
sinon crop central). Suffisant pour lier des captures successives du même
visage dans la nursery, et ancrer un label enseigné (ex. Vincent).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Similarité cosine minimale pour considérer « même visage »
MATCH_THRESHOLD = 0.82
# Moyenne glissante des embeddings (max gardés)
MAX_EMBS_PER_PERSON = 8
GRID = 8
HIST_BINS = 16


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _l2(vec: List[float]) -> List[float]:
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


def _load_gray(path: Path) -> Optional[Any]:
    """Charge image en niveaux de gris (numpy array)."""
    try:
        import cv2  # type: ignore

        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        return img
    except Exception:
        pass
    try:
        from PIL import Image  # type: ignore
        import numpy as np  # type: ignore

        im = Image.open(path).convert("L")
        return np.asarray(im)
    except Exception:
        return None


def _detect_faces(gray: Any) -> List[Tuple[int, int, int, int]]:
    """Retourne liste (x, y, w, h), plus grand d'abord."""
    h, w = int(gray.shape[0]), int(gray.shape[1])
    faces: List[Tuple[int, int, int, int]] = []
    try:
        import cv2  # type: ignore

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        casc = cv2.CascadeClassifier(cascade_path)
        detected = casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(48, 48))
        for (x, y, fw, fh) in detected:
            faces.append((int(x), int(y), int(fw), int(fh)))
    except Exception:
        faces = []

    if not faces:
        # Fallback : zone centrale (souvent le visage webcam)
        side = min(w, h) * 55 // 100
        x = (w - side) // 2
        y = max(0, (h - side) // 2 - h // 12)
        faces = [(x, y, side, side)]

    faces.sort(key=lambda t: t[2] * t[3], reverse=True)
    return faces


def embed_face_crop(gray: Any, box: Tuple[int, int, int, int]) -> List[float]:
    """Empreinte locale : grille GRID×GRID + histogramme HIST_BINS."""
    x, y, w, h = box
    crop = gray[y : y + h, x : x + w]
    if crop is None or getattr(crop, "size", 0) == 0:
        return []

    try:
        import cv2  # type: ignore

        small = cv2.resize(crop, (GRID, GRID), interpolation=cv2.INTER_AREA)
        hist = cv2.calcHist([crop], [0], None, [HIST_BINS], [0, 256]).flatten()
        grid = small.astype(float).flatten() / 255.0
        hist = (hist / (hist.sum() or 1.0)).tolist()
        return _l2(grid.tolist() + hist)
    except Exception:
        pass

    try:
        import numpy as np  # type: ignore
        from PIL import Image  # type: ignore

        im = Image.fromarray(crop.astype("uint8"))
        small = im.resize((GRID, GRID))
        arr = np.asarray(small, dtype=float).flatten() / 255.0
        flat = np.asarray(crop, dtype=float).flatten()
        hist, _ = np.histogram(flat, bins=HIST_BINS, range=(0, 256), density=True)
        return _l2(arr.tolist() + hist.tolist())
    except Exception:
        return []


def extract_face_embeddings(image_path: str | Path) -> List[Dict[str, Any]]:
    """
    Extrait 0..N visages d'une image.
    Chaque item: {embedding, box, method}
    """
    path = Path(image_path)
    gray = _load_gray(path)
    if gray is None:
        return []
    faces = _detect_faces(gray)
    out: List[Dict[str, Any]] = []
    method = "haar" if len(faces) > 1 or True else "center"
    # Distinguer Haar vs fallback : si un seul et central large → marquer
    try:
        import cv2  # type: ignore

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        casc = cv2.CascadeClassifier(cascade_path)
        detected = casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(48, 48))
        method = "haar" if len(detected) else "center_crop"
    except Exception:
        method = "center_crop"

    for box in faces[:3]:
        emb = embed_face_crop(gray, box)
        if emb:
            out.append({"embedding": emb, "box": list(box), "method": method})
    return out


class VisualPersonMemory:
    """Persistance JSON des identités visuelles."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: Dict[str, Any] = {"schema": "visual_persons/v1", "persons": [], "pending": [], "last_seen": None}
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

    def _person_mean_emb(self, person: Dict[str, Any]) -> Optional[List[float]]:
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
        n = float(len(embs))
        return _l2([v / n for v in acc])

    def match(self, embedding: List[float]) -> Optional[Dict[str, Any]]:
        best: Optional[Dict[str, Any]] = None
        best_score = 0.0
        for p in self.data["persons"]:
            mean = self._person_mean_emb(p)
            if not mean:
                continue
            sc = cosine(embedding, mean)
            # aussi max vs chaque embedding
            for e in p.get("embeddings") or []:
                sc = max(sc, cosine(embedding, e))
            if sc > best_score:
                best_score = sc
                best = {"person": p, "score": round(sc, 4)}
        if best and best["score"] >= MATCH_THRESHOLD:
            return best
        return None

    def reinforce(self, person_id: str, embedding: List[float], snapshot: str) -> Dict[str, Any]:
        for p in self.data["persons"]:
            if p["id"] != person_id:
                continue
            embs = p.setdefault("embeddings", [])
            embs.append(embedding)
            if len(embs) > MAX_EMBS_PER_PERSON:
                p["embeddings"] = embs[-MAX_EMBS_PER_PERSON:]
            snaps = p.setdefault("snapshots", [])
            name = Path(snapshot).name
            if name not in snaps:
                snaps.append(name)
                if len(snaps) > 24:
                    p["snapshots"] = snaps[-24:]
            p["seen_count"] = int(p.get("seen_count") or 0) + 1
            p["exposant"] = min(10, int(p.get("exposant") or 5) + 1)
            p["updated_at"] = _now()
            self.data["last_seen"] = {
                "kind": "person",
                "id": p["id"],
                "label": p.get("label"),
                "snapshot": name,
                "at": _now(),
            }
            self.save()
            return p
        raise KeyError(person_id)

    def create_pending(self, embedding: List[float], snapshot: str, box: List[int], method: str) -> Dict[str, Any]:
        name = Path(snapshot).name
        item = {
            "id": self._next_id("U"),
            "embedding": embedding,
            "snapshot": name,
            "box": box,
            "method": method,
            "created_at": _now(),
        }
        self.data["pending"].append(item)
        # garder peu de pending
        self.data["pending"] = self.data["pending"][-12:]
        self.data["last_seen"] = {
            "kind": "pending",
            "id": item["id"],
            "label": None,
            "snapshot": name,
            "at": _now(),
        }
        self.save()
        return item

    def label_pending_or_last(self, label: str, exposant: int = 8) -> Optional[Dict[str, Any]]:
        """Attache un nom au dernier visage vu (pending → person, ou rename person)."""
        self.load()
        label = (label or "").strip()
        if not label:
            return None
        last = self.data.get("last_seen") or {}
        # Si déjà une personne connue : juste renforcer le label
        if last.get("kind") == "person" and last.get("id"):
            for p in self.data["persons"]:
                if p["id"] == last["id"]:
                    p["label"] = label
                    p["exposant"] = max(int(p.get("exposant") or 0), exposant)
                    p["updated_at"] = _now()
                    self.save()
                    return p

        # Chercher pending correspondant
        pending_id = last.get("id") if last.get("kind") == "pending" else None
        pending = None
        if pending_id:
            for u in list(self.data["pending"]):
                if u["id"] == pending_id:
                    pending = u
                    break
        if pending is None and self.data["pending"]:
            pending = self.data["pending"][-1]

        if pending is None:
            # Créer personne sans embedding frais (label seul) — utile si teach texte
            person = {
                "id": self._next_id("P"),
                "label": label,
                "embeddings": [],
                "snapshots": [],
                "seen_count": 0,
                "exposant": exposant,
                "created_at": _now(),
                "updated_at": _now(),
            }
            self.data["persons"].append(person)
            self.save()
            return person

        # Fusionner si label déjà connu
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
            snaps = existing.setdefault("snapshots", [])
            if pending.get("snapshot") and pending["snapshot"] not in snaps:
                snaps.append(pending["snapshot"])
            existing["seen_count"] = int(existing.get("seen_count") or 0) + 1
            existing["exposant"] = max(int(existing.get("exposant") or 0), exposant)
            existing["updated_at"] = _now()
            self.data["pending"] = [u for u in self.data["pending"] if u["id"] != pending["id"]]
            self.data["last_seen"] = {
                "kind": "person",
                "id": existing["id"],
                "label": existing.get("label"),
                "snapshot": pending.get("snapshot"),
                "at": _now(),
            }
            self.save()
            return existing

        person = {
            "id": self._next_id("P"),
            "label": label,
            "embeddings": [pending["embedding"]] if pending.get("embedding") else [],
            "snapshots": [pending["snapshot"]] if pending.get("snapshot") else [],
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
            "snapshot": pending.get("snapshot"),
            "at": _now(),
        }
        self.save()
        return person

    def process_snapshot(self, image_path: str | Path) -> Dict[str, Any]:
        """
        Analyse une capture : match / pending.
        Retourne {faces: [...], recognized: [...], unknown: [...]}
        """
        self.load()
        faces = extract_face_embeddings(image_path)
        recognized: List[Dict[str, Any]] = []
        unknown: List[Dict[str, Any]] = []
        for f in faces:
            m = self.match(f["embedding"])
            if m:
                person = self.reinforce(m["person"]["id"], f["embedding"], str(image_path))
                recognized.append({
                    "id": person["id"],
                    "label": person.get("label"),
                    "score": m["score"],
                    "exposant": person.get("exposant"),
                    "seen_count": person.get("seen_count"),
                    "box": f["box"],
                    "method": f["method"],
                })
            else:
                pend = self.create_pending(f["embedding"], str(image_path), f["box"], f["method"])
                unknown.append({
                    "id": pend["id"],
                    "snapshot": pend["snapshot"],
                    "box": f["box"],
                    "method": f["method"],
                })
        return {
            "ok": True,
            "face_count": len(faces),
            "recognized": recognized,
            "unknown": unknown,
            "method": faces[0]["method"] if faces else None,
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "persons": [
                {
                    "id": p["id"],
                    "label": p.get("label"),
                    "exposant": p.get("exposant"),
                    "seen_count": p.get("seen_count"),
                    "snapshots": len(p.get("snapshots") or []),
                    "embeddings": len(p.get("embeddings") or []),
                }
                for p in self.data["persons"]
            ],
            "pending": len(self.data.get("pending") or []),
            "last_seen": self.data.get("last_seen"),
        }


_LABEL_PATTERNS = [
    re.compile(r"\bc['’]est\s+(?:moi\s+)?([A-Za-zÀ-ÿ][\wÀ-ÿ\-']{1,40})\b", re.I),
    re.compile(r"\bc['’]est\s+(?:bien\s+)?([A-Za-zÀ-ÿ][\wÀ-ÿ\-']{1,40})\b", re.I),
    re.compile(r"\b(?:il|elle)\s+s['’]appelle\s+([A-Za-zÀ-ÿ][\wÀ-ÿ\-']{1,40})\b", re.I),
    re.compile(r"\b(?:la\s+personne|le\s+visage|celui|celle)\s+.*\s+est\s+([A-Za-zÀ-ÿ][\wÀ-ÿ\-']{1,40})\b", re.I),
    re.compile(r"\bje\s+suis\s+([A-Za-zÀ-ÿ][\wÀ-ÿ\-']{1,40})\b", re.I),
]

# Mots grammaticaux uniquement (pas de liste de « fausses identités » — ça vit en mémoire)
_LABEL_SKIP = {
    "bien", "ça", "ca", "vrai", "faux", "correct", "moi", "toi", "lui",
    "elle", "une", "un", "le", "la", "les", "des", "bonjour", "merci",
}


def _norm_label(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return ""
    return name[0].upper() + name[1:]


def extract_identity_label(text: str) -> Optional[str]:
    """Extrait un nom probable depuis une phrase d'enseignement humain."""
    t = (text or "").strip()
    if not t or "?" in t:
        return None
    for pat in _LABEL_PATTERNS:
        m = pat.search(t)
        if m:
            name = m.group(1).strip()
            if name.lower() not in _LABEL_SKIP and len(name) >= 2:
                return _norm_label(name)
    return None


# Format des mémoires de correction (contenu dans memory_index, pas ici) :
#   Correction auditive: « entendu » → « voulu »
_CORR_AUDITIVE = re.compile(
    r"correction\s+auditive\s*:\s*[«\"]\s*(.+?)\s*[»\"]\s*(?:→|->|=|≈)\s*[«\"]\s*(.+?)\s*[»\"]",
    re.I,
)


def parse_auditory_correction(data: str) -> Optional[Tuple[str, str]]:
    """Lit une paire entendu→voulu depuis le texte d'une mémoire."""
    m = _CORR_AUDITIVE.search(data or "")
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()
