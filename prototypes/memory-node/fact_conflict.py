#!/usr/bin/env python3
"""Découpage minimal des faits « X est Y » enseignés par l'humain.

Aucune dépendance. Les anciens enregistrements (sans ce module) restent
lisibles : on ne fait que lire `data`, `correlations`, `human_feedback`.

Limite assumée : heuristique française (premier « est » / « = »), pas un
analyseur syntaxique. Voir le rapport de proposition.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

TAUGHT_PREFIX = "fait enseigné par l'humain:"
POSEE_PREFIX = "contradiction_posée:"
TRANCHEE_PREFIX = "contradiction_tranchée:"

# Retrait en tête seulement — pour que « Pour information fiable, … » porte
# sur le même sujet que la phrase sans ce préambule.
_HEDGE_RE = re.compile(
    r"^(?:(?:"
    r"pour\s+information(?:\s+fiable)?"
    r"|pour\s+info(?:\s+fiable)?"
    r"|information\s+fiable"
    r"|selon\s+moi"
    r"|je\s+pense\s+que"
    r"|je\s+crois\s+que"
    r"|il\s+para[iî]t\s+que"
    r"|en\s+fait"
    r")\s*[:,]?\s*)+",
    re.IGNORECASE,
)

_ARTICLES = {
    "le", "la", "les", "un", "une", "des", "du", "de", "au", "aux",
    "ce", "cet", "cette", "mon", "ma", "mes", "ton", "ta", "tes",
    "son", "sa", "ses", "notre", "nos", "votre", "vos", "leur", "leurs",
}

_VALUE_FILLERS = {"bien", "tres", "très", "vraiment", "toujours", "aussi"}

# Accords que le simple retrait du « e » final rate.
_IRREG = {
    "blanche": "blanc",
    "blanches": "blanc",
    "fraiche": "frais",
    "fraîche": "frais",
    "fraiches": "frais",
    "fraîches": "frais",
}


def _tokenize(text: str) -> List[str]:
    text = (text or "").lower().replace("’", "'").replace("`", "'")
    text = re.sub(r"[^a-zàâäéèêëïîôùûüç0-9'\s]", " ", text)
    out: List[str] = []
    for part in text.split():
        part = part.strip("'")
        if "'" in part:
            left, right = part.split("'", 1)
            if left in {"l", "d", "j", "n", "m", "t", "s", "c", "qu"} and right:
                part = right
        if part:
            out.append(part)
    return out


def _fold_token(token: str) -> str:
    if token in _IRREG:
        return _IRREG[token]
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("e"):
        return token[:-1]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _subject_key(raw_left: str) -> str:
    toks = [t for t in _tokenize(raw_left) if t not in _ARTICLES]
    return " ".join(toks)


def _value_key(raw_right: str) -> str:
    text = (raw_right or "").strip().strip(".").strip()
    text = re.sub(
        r"^(?:de\s+la\s+couleur|de\s+couleur|la\s+couleur|couleur)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^(?:un|une|le|la|les|des|du|de|d')\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^(?:bien|très|tres|vraiment|toujours)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # « bien de couleur bleue » : le filler peut précéder la couleur.
    text = re.sub(
        r"^(?:de\s+la\s+couleur|de\s+couleur|la\s+couleur|couleur)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    toks = _tokenize(text)
    kept = [t for t in toks if t not in _VALUE_FILLERS]
    if not kept:
        kept = toks
    return " ".join(_fold_token(t) for t in kept)


def _is_specific(subject_key: str) -> bool:
    toks = [t for t in subject_key.split() if len(t) >= 4]
    if any(len(t) >= 5 for t in toks):
        return True
    return len(toks) >= 2


def _split_copula(raw: str) -> Optional[tuple]:
    """Coupe sur le premier « est » ou « = » entouré d'espaces.

    « c'est » ne contient pas « est » isolé : le chemin identité n'est pas
    réinterprété ici.
    """
    m = re.search(r"\sest\s", raw, flags=re.IGNORECASE)
    if m:
        return raw[: m.start()], raw[m.end() :]
    m = re.search(r"\s=\s", raw)
    if m:
        return raw[: m.start()], raw[m.end() :]
    return None


def parse_sentence(text: str) -> Optional[Dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return None
    raw = _HEDGE_RE.sub("", raw).strip()
    parts = _split_copula(raw)
    if not parts:
        return None
    left, right = parts[0].strip(" ,;"), parts[1].strip().strip(".").strip()
    if len(left) < 2 or not right:
        return None
    subject = _subject_key(left)
    value = _value_key(right)
    if not subject or not value:
        return None
    return {
        "subject_raw": left.strip(),
        "value_raw": right,
        "subject_key": subject,
        "value_key": value,
        "specific": _is_specific(subject),
        "body_key": " ".join(_tokenize(raw)),
    }


def taught_body(data: str) -> Optional[str]:
    data = (data or "").strip()
    if not data.lower().startswith(TAUGHT_PREFIX):
        return None
    return data[len(TAUGHT_PREFIX) :].strip()


def parse_taught(data: str) -> Optional[Dict[str, Any]]:
    body = taught_body(data)
    if body is None:
        return None
    return parse_sentence(body)


def claim_signature(data: str, fundamental: str = "C", state: str = "P") -> Optional[tuple]:
    """Clé de regroupement des doublons de faits enseignés. None si ce n'en est pas un."""
    parsed = parse_taught(data)
    if not parsed:
        return None
    if parsed["specific"]:
        return ("claim", fundamental, state, parsed["subject_key"], parsed["value_key"])
    return ("body", fundamental, state, parsed["body_key"])


def _view(rec: Any) -> Dict[str, Any]:
    if isinstance(rec, dict):
        return rec
    return {
        "id": rec.id,
        "data": rec.data or "",
        "exposant": int(rec.exposant or 0),
        "human_feedback": rec.human_feedback or "",
        "correlations": list(rec.correlations or []),
        "fundamental": getattr(rec, "fundamental", "C"),
        "state": getattr(rec, "state", "P"),
    }


def classify_new_fact(records: Iterable[Any], new_text: str) -> Dict[str, Any]:
    """Décide sans rien écrire.

    kind:
      - unparsed : pas un « X est Y » exploitable
      - duplicate : même sujet + même valeur (ou même phrase si sujet trop vague)
      - contradiction : même sujet spécifique, valeur différente
      - new : rien d'équivalent
    """
    parsed = parse_sentence(new_text)
    if not parsed:
        return {"kind": "unparsed", "parsed": None, "duplicate": None, "conflicts": []}

    dups: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    for rec in records:
        view = _view(rec)
        old = parse_taught(view.get("data") or "")
        if not old:
            continue
        same_subject = parsed["specific"] and old["specific"] and old["subject_key"] == parsed["subject_key"]
        if same_subject and old["value_key"] == parsed["value_key"]:
            dups.append({**view, **old})
        elif same_subject and old["value_key"] != parsed["value_key"]:
            conflicts.append({**view, **old})
        elif (not parsed["specific"]) and (not old["specific"]) and old["body_key"] == parsed["body_key"]:
            dups.append({**view, **old})

    if dups:
        def _rank(r: Dict[str, Any]) -> tuple:
            try:
                num = int(str(r.get("id", "")).lstrip("Mm") or 0)
            except ValueError:
                num = 0
            return (-int(r.get("exposant") or 0), num)

        dups.sort(key=_rank)
        return {
            "kind": "duplicate",
            "parsed": parsed,
            "duplicate": dups[0],
            "conflicts": conflicts,
        }
    if conflicts:
        return {
            "kind": "contradiction",
            "parsed": parsed,
            "duplicate": None,
            "conflicts": conflicts,
        }
    return {"kind": "new", "parsed": parsed, "duplicate": None, "conflicts": []}


def _groups(records: Iterable[Any]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for rec in records:
        view = _view(rec)
        parsed = parse_taught(view.get("data") or "")
        if not parsed or not parsed["specific"]:
            continue
        groups.setdefault(parsed["subject_key"], []).append({**view, **parsed})
    return groups


def _matches(subject_key: str, perception: str) -> bool:
    if not _is_specific(subject_key):
        return False
    needed = [t for t in subject_key.split() if len(t) >= 4]
    if not needed:
        return False
    have = set(_tokenize(perception))
    return all(t in have for t in needed)


def conflict_groups_for_perception(records: Iterable[Any], perception: str) -> List[Dict[str, Any]]:
    """Groupes de faits enseignés contredits dont le sujet est entièrement dans la perception."""
    found: List[Dict[str, Any]] = []
    for key, items in _groups(records).items():
        if not _matches(key, perception):
            continue
        by_value: Dict[str, Dict[str, Any]] = {}
        for it in items:
            by_value.setdefault(it["value_key"], it)
        if len(by_value) < 2:
            continue
        found.append({
            "subject_key": key,
            "subject_raw": items[0]["subject_raw"],
            "values": list(by_value.values()),
            "items": items,
            "ids": [it["id"] for it in items],
        })
    return found


def list_contradictions(records: Iterable[Any]) -> List[Dict[str, Any]]:
    """Toutes les contradictions de faits enseignés, sans regarder une perception."""
    found = []
    for key, items in _groups(records).items():
        by_value: Dict[str, Dict[str, Any]] = {}
        for it in items:
            by_value.setdefault(it["value_key"], it)
        if len(by_value) < 2:
            continue
        found.append({
            "subject_key": key,
            "subject_raw": items[0]["subject_raw"],
            "values": list(by_value.values()),
            "ids": [it["id"] for it in items],
        })
    return found


def already_posed(records: Iterable[Any], subject_key: str) -> bool:
    posed = POSEE_PREFIX + subject_key
    resolved = TRANCHEE_PREFIX + subject_key + "="
    for rec in records:
        fb = _view(rec).get("human_feedback") or ""
        if fb == posed or fb.startswith(posed + " ") or fb.startswith(resolved):
            return True
    return False


def resolved_value_key(records: Iterable[Any], subject_key: str) -> Optional[str]:
    prefix = TRANCHEE_PREFIX + subject_key + "="
    for rec in records:
        fb = _view(rec).get("human_feedback") or ""
        if fb.startswith(prefix):
            val = fb[len(prefix):]
            if val and val != "?":
                return val
    return None


def match_answer_to_values(answer: str, value_keys: Iterable[str]) -> Optional[str]:
    keys = [k for k in value_keys if k]
    if not answer or not keys:
        return None
    direct = _value_key(answer)
    if direct in keys:
        return direct
    ans = {_fold_token(t) for t in _tokenize(answer)}
    hits = []
    for key in keys:
        parts = key.split()
        if parts and all(p in ans for p in parts):
            hits.append(key)
    if len(hits) == 1:
        return hits[0]
    return None


def _fmt_values(values: List[Dict[str, Any]]) -> str:
    parts = [f"« {v.get('value_raw') or v.get('value_key')} » ({v.get('id')})" for v in values]
    if len(parts) == 2:
        return " et ".join(parts)
    return ", ".join(parts)


def build_question(subject_raw: str, values: List[Dict[str, Any]]) -> str:
    shown = _fmt_values(values)
    if len(values) == 2:
        shown = " ou ".join(
            f"« {v.get('value_raw') or v.get('value_key')} » ({v.get('id')})" for v in values
        )
    return (
        f"Enseignements contradictoires sur « {subject_raw} » : {shown}. "
        "Lequel retenir ? Je ne départage pas par la répétition, "
        "et je ne reposerai pas la question."
    )


def utter_uncertain(subject_raw: str, values: List[Dict[str, Any]], tail: str) -> str:
    return (
        f"Je ne choisis pas : on m'a enseigné des choses contradictoires sur "
        f"« {subject_raw} » — {_fmt_values(values)}. "
        f"Répéter une version ne la rend pas plus vraie. {tail}"
    )


def utter_resolved(subject_raw: str, chosen_raw: str, other_values: List[Dict[str, Any]]) -> str:
    others = _fmt_values(other_values) if other_values else "l'autre version"
    return (
        f"Tu as tranché pour « {chosen_raw} » sur « {subject_raw} ». "
        f"Je garde aussi en mémoire {others}, sans l'effacer."
    )


def exact_data_key(data: str) -> str:
    return " ".join((data or "").lower().split())
