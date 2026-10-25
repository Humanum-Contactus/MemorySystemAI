#!/usr/bin/env python3
"""Découpage minimal des faits « X est Y » enseignés par l'humain.

À QUOI SERT CE FICHIER
----------------------
Quand un humain enseigne une phrase comme « Le cristal de l'atelier est bleu »,
le nœud la garde comme un « fait enseigné ». Si plus tard quelqu'un dit
« Le cristal de l'atelier est rouge », les deux phrases parlent du MÊME sujet
avec deux VALEURS différentes : c'est une contradiction.

Idée du concept (MemorySystemAI) : répéter un mensonge ne doit pas le rendre
plus vrai. La mémoire ne « vote » pas au nombre de copies ; elle signale le
désaccord et demande UNE fois à l'humain (le tuteur) de trancher.

Ce module ne fait que LIRE et COMPARER des textes. Il n'écrit jamais dans la
mémoire : c'est organism.py qui décide quoi enregistrer. On peut donc le tester
seul, sans serveur, sans capteur, sans réseau.

COMMENT L'ESSAYER (dans un terminal, depuis ce dossier)
-------------------------------------------------------
    python3 -c "import fact_conflict as fc; print(fc.parse_sentence('Le cristal de l atelier est de couleur bleue.'))"

Résultat attendu : un dictionnaire avec subject_key = « cristal atelier »
et value_key = « bleu ».

Aucune dépendance : seulement la bibliothèque standard de Python (module `re`
pour les expressions régulières, c'est-à-dire des motifs de recherche dans du
texte). Les anciens enregistrements (créés avant ce module) restent lisibles :
on ne fait que lire `data`, `correlations`, `human_feedback`.

Limite assumée : heuristique française (on coupe sur le premier « est » ou
« = »), pas un vrai analyseur de grammaire. Une heuristique est une règle
simple qui marche souvent, pas toujours. Les limites sont listées dans
docs/changements/2026-10-25_detection-contradictions.md.
"""
# Rend les annotations de type (les « : str », « -> Dict ») paresseuses :
# elles servent de documentation et ne sont pas évaluées à l'exécution.
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

# Préfixes de texte posés dans la mémoire. Ce sont de simples chaînes, lisibles
# par un humain dans memory_index.json (format JSON = texte ouvert) :
# - TAUGHT_PREFIX : début du champ `data` d'un fait enseigné ;
# - POSEE_PREFIX  : marque « la question sur ce sujet a déjà été posée » ;
# - TRANCHEE_PREFIX : marque « l'humain a choisi telle valeur ».
TAUGHT_PREFIX = "fait enseigné par l'humain:"
POSEE_PREFIX = "contradiction_posée:"
TRANCHEE_PREFIX = "contradiction_tranchée:"

# Retrait en tête seulement — pour que « Pour information fiable, … » porte
# sur le même sujet que la phrase sans ce préambule.
# Pourquoi : « Pour information fiable, le cristal est bleu » doit être reconnu
# comme le MÊME fait que « Le cristal est bleu ». Sinon une simple formule de
# politesse créerait un nouveau sujet et cacherait la contradiction.
# Comment : ce motif enlève, au début de la phrase seulement, une ou plusieurs
# formules de la liste ci-dessous (suivies éventuellement de « : » ou « , »).
# La liste est fermée exprès : on préfère rater une formule que deviner.
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

# Petits mots retirés du SUJET pour comparer l'essentiel :
# « le cristal », « ce cristal », « mon cristal » → « cristal ».
_ARTICLES = {
    "le", "la", "les", "un", "une", "des", "du", "de", "au", "aux",
    "ce", "cet", "cette", "mon", "ma", "mes", "ton", "ta", "tes",
    "son", "sa", "ses", "notre", "nos", "votre", "vos", "leur", "leurs",
}

# Mots d'insistance retirés de la VALEUR : « très bleu » et « bleu » = même valeur.
_VALUE_FILLERS = {"bien", "tres", "très", "vraiment", "toujours", "aussi"}

# Accords que le simple retrait du « e » final rate.
# Accords que le simple retrait du « e » final rate.
# Exemple : « blanche » sans son « e » donnerait « blanch », pas « blanc ».
_IRREG = {
    "blanche": "blanc",
    "blanches": "blanc",
    "fraiche": "frais",
    "fraîche": "frais",
    "fraiches": "frais",
    "fraîches": "frais",
}


# Découpe un texte en mots simples (« tokens ») pour pouvoir les comparer.
# Étapes : 1) minuscules et apostrophes uniformisées ; 2) toute ponctuation
# devient un espace ; 3) l'élision est retirée (« l'atelier » → « atelier »,
# « d'or » → « or ») ; 4) on garde la liste des mots non vides.
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


# Ramène un mot à une forme commune pour que l'accord ne crée pas de
# fausse différence : « bleue », « bleus », « bleues » → « bleu ».
# Étapes : 1) cas irréguliers de la table _IRREG ; 2) sinon on retire « es »,
# puis « e », puis « s » final, seulement si le mot reste assez long.
# Limite connue : « porte » et « port » finissent par se ressembler.
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


# Clé du sujet : les mots de la partie gauche (avant « est »), sans articles.
# Deux phrases ont le même sujet si leurs clés sont identiques.
def _subject_key(raw_left: str) -> str:
    toks = [t for t in _tokenize(raw_left) if t not in _ARTICLES]
    return " ".join(toks)


# Clé de la valeur : la partie droite (après « est »), nettoyée.
# Étapes : 1) retirer le point final ; 2) retirer « de couleur » / « la couleur » ;
# 3) retirer un article ; 4) retirer un mot d'insistance (« très ») ;
# 5) re-retirer « de couleur » (cas « bien de couleur bleue ») ;
# 6) découper en mots, enlever les mots d'insistance restants, et ramener
# chaque mot à sa forme commune (_fold_token).
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


# Un sujet est « spécifique » s'il est assez précis pour qu'une contradiction
# ait un sens : au moins un mot de 5 lettres ou plus, ou deux mots de 4 lettres.
# Pourquoi : « le wifi est coupé » puis « le wifi est allumé » ne sont pas un
# mensonge, l'état change. Un sujet trop court ne déclenche donc rien.
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


# Point d'entrée principal : transforme une phrase en sujet + valeur.
# Renvoie None si la phrase n'est pas de la forme « X est Y » exploitable.
# Étapes : 1) retirer le préambule (« pour information fiable ») ;
# 2) couper sur le premier « est » / « = » ; 3) nettoyer les deux côtés ;
# 4) calculer les clés de sujet et de valeur ; 5) noter si le sujet est
# spécifique ; body_key garde la phrase entière normalisée (utile pour
# repérer une répétition mot pour mot quand le sujet est trop vague).
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


# Si `data` commence par « Fait enseigné par l'humain: », renvoie la phrase
# enseignée qui suit ; sinon None (ce n'est pas un fait enseigné).
def taught_body(data: str) -> Optional[str]:
    data = (data or "").strip()
    if not data.lower().startswith(TAUGHT_PREFIX):
        return None
    return data[len(TAUGHT_PREFIX) :].strip()


# Combinaison des deux fonctions précédentes, pour un enregistrement mémoire.
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


# Les enregistrements arrivent sous deux formes : des dictionnaires (lus depuis
# le fichier JSON) ou des objets MemoryEntry (en mémoire vive). Cette fonction
# les ramène tous à un dictionnaire, pour que le reste du code n'ait qu'un cas.
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
    # Étape 1 : la nouvelle phrase est-elle un « X est Y » ?
    parsed = parse_sentence(new_text)
    if not parsed:
        return {"kind": "unparsed", "parsed": None, "duplicate": None, "conflicts": []}

    # Étape 2 : comparer avec chaque fait déjà enseigné.
    dups: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    for rec in records:
        view = _view(rec)
        old = parse_taught(view.get("data") or "")
        if not old:
            continue
        # Même sujet seulement si les deux sujets sont spécifiques ET identiques.
        same_subject = parsed["specific"] and old["specific"] and old["subject_key"] == parsed["subject_key"]
        if same_subject and old["value_key"] == parsed["value_key"]:
            dups.append({**view, **old})
        elif same_subject and old["value_key"] != parsed["value_key"]:
            conflicts.append({**view, **old})
        elif (not parsed["specific"]) and (not old["specific"]) and old["body_key"] == parsed["body_key"]:
            dups.append({**view, **old})

    # Étape 3 : s'il y a des doublons, on désigne le plus fort (exposant le plus
    # haut, puis le plus ancien numéro M…) : c'est lui qu'organism.py renforcera.
    # Un doublon passe avant une contradiction : redire une version connue
    # n'est pas une nouvelle information.
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


# Range tous les faits enseignés spécifiques par sujet :
# { « cristal atelier » : [fait bleu, fait rouge, …], … }.
def _groups(records: Iterable[Any]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for rec in records:
        view = _view(rec)
        parsed = parse_taught(view.get("data") or "")
        if not parsed or not parsed["specific"]:
            continue
        groups.setdefault(parsed["subject_key"], []).append({**view, **parsed})
    return groups


# La perception (la question posée) parle-t-elle de ce sujet ?
# Règle simple : tous les mots de 4 lettres ou plus du sujet doivent être
# présents dans la question. « De quelle couleur est le cristal de l'atelier ? »
# contient « cristal » et « atelier » → oui.
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
        # Une valeur par clé (le premier fait rencontré la représente). S'il n'y a
        # qu'une valeur, toutes les copies disent la même chose : pas de contradiction.
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


# A-t-on déjà posé (ou déjà tranché) la question sur ce sujet ? On le lit dans
# le champ human_feedback des faits. Sert la règle « ask_human sans harceler » :
# une seule question par sujet, jamais de relance.
def already_posed(records: Iterable[Any], subject_key: str) -> bool:
    posed = POSEE_PREFIX + subject_key
    resolved = TRANCHEE_PREFIX + subject_key + "="
    for rec in records:
        fb = _view(rec).get("human_feedback") or ""
        if fb == posed or fb.startswith(posed + " ") or fb.startswith(resolved):
            return True
    return False


# Si l'humain a tranché, renvoie la clé de la valeur choisie, sinon None.
# « ? » veut dire « réponse reçue mais qui ne désigne aucune valeur ».
def resolved_value_key(records: Iterable[Any], subject_key: str) -> Optional[str]:
    prefix = TRANCHEE_PREFIX + subject_key + "="
    for rec in records:
        fb = _view(rec).get("human_feedback") or ""
        if fb.startswith(prefix):
            val = fb[len(prefix):]
            if val and val != "?":
                return val
    return None


# Relie la réponse libre de l'humain à UNE des valeurs connues.
# Étapes : 1) la réponse nettoyée est-elle exactement une valeur ? 2) sinon,
# quelles valeurs ont tous leurs mots dans la réponse ? Si une seule → choisie.
# Si zéro ou plusieurs (« bleu ou rouge, je ne sais pas ») → None : on ne
# devine pas à la place de l'humain.
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


# Mise en forme lisible : « bleue » (M12) et « rouge » (M15).
def _fmt_values(values: List[Dict[str, Any]]) -> str:
    parts = [f"« {v.get('value_raw') or v.get('value_key')} » ({v.get('id')})" for v in values]
    if len(parts) == 2:
        return " et ".join(parts)
    return ", ".join(parts)


# Texte de l'unique question envoyée à l'humain (ask_human).
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


# Ce que le nœud répond quand la contradiction n'est pas tranchée :
# il cite les deux versions et refuse de choisir. `tail` précise si la
# question a été posée, est déjà en attente, ou ne sera pas relancée.
def utter_uncertain(subject_raw: str, values: List[Dict[str, Any]], tail: str) -> str:
    return (
        f"Je ne choisis pas : on m'a enseigné des choses contradictoires sur "
        f"« {subject_raw} » — {_fmt_values(values)}. "
        f"Répéter une version ne la rend pas plus vraie. {tail}"
    )


# Ce que le nœud répond une fois que l'humain a tranché. L'autre version
# n'est pas effacée : la mémoire garde la trace de ce qu'on lui a dit.
def utter_resolved(subject_raw: str, chosen_raw: str, other_values: List[Dict[str, Any]]) -> str:
    others = _fmt_values(other_values) if other_values else "l'autre version"
    return (
        f"Tu as tranché pour « {chosen_raw} » sur « {subject_raw} ». "
        f"Je garde aussi en mémoire {others}, sans l'effacer."
    )


# Clé « texte exact » : minuscules et espaces normalisés. Utilisée par
# dedup_taught_facts.py --all-exact pour repérer des copies mot pour mot.
def exact_data_key(data: str) -> str:
    return " ".join((data or "").lower().split())
