#!/usr/bin/env python3
"""Fusion optionnelle des doublons déjà présents dans memory_index.json.

Ne lance rien sur l'index vivant tant que --apply n'est pas passé.
Avec --apply :
  1. copie de sauvegarde <index>.bak-<horodatage> (fichier complet)
  2. archive JSON des entrées retirées (à côté de l'index)
  3. réécriture : les entrées non concernées sont copiées telles quelles,
     y compris les champs inconnus du schéma.

Arrêter memory-node AVANT --apply, sinon le processus réécrit l'index
depuis la RAM et annule le fichier.

Modes :
  défaut     faits enseignés de même sujet + même valeur (et même état)
  --all-exact  toute mémoire dont le texte data, le fondamental et l'état
               sont identiques après normalisation espaces/casse
               (ex. « Autonomie inhibée: … » répété à l'identique)

Les contradictions (même sujet, valeur différente) ne sont jamais fusionnées.
L'exposant du survivant n'est pas modifié : on garde le plus élevé, donc
une mémoire déjà ≥ 9 ne redescend pas.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fact_conflict import (  # noqa: E402
    claim_signature,
    exact_data_key,
    list_contradictions,
)


def _load(path: Path) -> Tuple[Any, List[Dict[str, Any]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw, raw
    if isinstance(raw, dict):
        entries = raw.get("entries")
        if not isinstance(entries, list):
            raise SystemExit("index illisible : 'entries' n'est pas une liste")
        return raw, entries
    raise SystemExit("index illisible : ni liste ni objet")


def _num_id(entry: Dict[str, Any]) -> int:
    try:
        return int(str(entry.get("id", "")).lstrip("Mm") or 0)
    except ValueError:
        return 0


def _survivor_key(entry: Dict[str, Any]) -> tuple:
    return (
        -int(entry.get("exposant") or 0),
        str(entry.get("date") or "9999-99-99"),
        _num_id(entry),
    )


def _signature(entry: Dict[str, Any], all_exact: bool) -> Optional[tuple]:
    if all_exact:
        data = entry.get("data") or ""
        if not str(data).strip():
            return None
        return (
            "exact",
            str(entry.get("fundamental") or ""),
            str(entry.get("state") or ""),
            exact_data_key(str(data)),
        )
    return claim_signature(
        str(entry.get("data") or ""),
        fundamental=str(entry.get("fundamental") or "C"),
        state=str(entry.get("state") or "P"),
    )


def _merge_group(group: List[Dict[str, Any]], today: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    ordered = sorted(group, key=_survivor_key)
    survivor = json.loads(json.dumps(ordered[0]))  # copie profonde, champs inconnus gardés
    removed = ordered[1:]
    logs = list(survivor.get("reinforcement_log") or [])
    corr = list(survivor.get("correlations") or [])
    for old in removed:
        for item in old.get("reinforcement_log") or []:
            logs.append(item)
        for cid in old.get("correlations") or []:
            if cid not in corr:
                corr.append(cid)
        if not survivor.get("consequence") and old.get("consequence"):
            survivor["consequence"] = old.get("consequence")
        if not survivor.get("human_feedback") and old.get("human_feedback"):
            survivor["human_feedback"] = old.get("human_feedback")
        if not survivor.get("action_context") and old.get("action_context"):
            survivor["action_context"] = old.get("action_context")
        tags = list(survivor.get("inhibition_tags") or [])
        for tag in old.get("inhibition_tags") or []:
            if tag not in tags:
                tags.append(tag)
        if tags:
            survivor["inhibition_tags"] = tags
    absorbed = [f"{e.get('id')} e{e.get('exposant')}" for e in removed]
    logs.append({
        "date": today,
        "old_exposant": survivor.get("exposant"),
        "new_exposant": survivor.get("exposant"),
        "reason": "fusion doublons (script, exposant inchangé) : " + ", ".join(absorbed),
    })
    survivor["reinforcement_log"] = logs
    survivor["correlations"] = corr
    return survivor, removed


def _retarget(entries: List[Dict[str, Any]], absorbed: Dict[str, str]) -> None:
    """Les liens vers un id absorbé pointent vers le survivant. Rien d'autre ne change."""
    if not absorbed:
        return
    for entry in entries:
        if "correlations" not in entry:
            continue
        new_corr: List[str] = []
        for cid in entry.get("correlations") or []:
            cid = absorbed.get(cid, cid)
            if cid == entry.get("id") or cid in new_corr:
                continue
            new_corr.append(cid)
        entry["correlations"] = new_corr


def plan(entries: List[Dict[str, Any]], all_exact: bool) -> Tuple[List[List[Dict[str, Any]]], List[Dict[str, Any]]]:
    buckets: Dict[tuple, List[Dict[str, Any]]] = {}
    for entry in entries:
        sig = _signature(entry, all_exact)
        if sig is None:
            continue
        buckets.setdefault(sig, []).append(entry)
    groups = [g for g in buckets.values() if len(g) >= 2]
    conflicts = [] if all_exact else list_contradictions(entries)
    return groups, conflicts


def apply_groups(entries: List[Dict[str, Any]], groups: List[List[Dict[str, Any]]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    today = dt.date.today().isoformat()
    removed_ids = set()
    absorbed_map: Dict[str, str] = {}
    removed_full: List[Dict[str, Any]] = []
    replacements: Dict[str, Dict[str, Any]] = {}
    for group in groups:
        survivor, removed = _merge_group(group, today)
        replacements[str(survivor.get("id"))] = survivor
        for old in removed:
            removed_ids.add(str(old.get("id")))
            absorbed_map[str(old.get("id"))] = str(survivor.get("id"))
            removed_full.append(old)
    kept: List[Dict[str, Any]] = []
    for entry in entries:
        eid = str(entry.get("id"))
        if eid in removed_ids:
            continue
        if eid in replacements:
            kept.append(replacements[eid])
        else:
            kept.append(entry)
    _retarget(kept, absorbed_map)
    # Le survivant peut encore citer un id absorbé : _retarget le traite aussi.
    return kept, removed_full


def main() -> None:
    parser = argparse.ArgumentParser(description="Fusion non destructive des doublons mémoire")
    parser.add_argument("--index", required=True, help="chemin de memory_index.json")
    parser.add_argument("--apply", action="store_true", help="écrit vraiment (après sauvegarde)")
    parser.add_argument(
        "--all-exact",
        action="store_true",
        help="doublons de texte exact (pas seulement les faits enseignés)",
    )
    args = parser.parse_args()
    path = Path(args.index)
    if not path.exists():
        raise SystemExit(f"introuvable : {path}")
    raw, entries = _load(path)
    groups, conflicts = plan(entries, args.all_exact)
    print(f"entrées : {len(entries)}")
    print(f"groupes fusionnables : {len(groups)}")
    for group in groups:
        ids = ", ".join(f"{e.get('id')} e{e.get('exposant')}" for e in sorted(group, key=_survivor_key))
        preview = str(group[0].get("data") or "").replace("\n", " ")[:80]
        print(f"  - {ids} | {preview}")
    if conflicts:
        print(f"contradictions laissées intactes : {len(conflicts)}")
        for c in conflicts:
            vals = ", ".join(f"{v.get('id')}={v.get('value_raw')}" for v in c["values"])
            print(f"  - {c['subject_raw']} : {vals}")
    if not groups:
        print("rien à fusionner")
        return
    if not args.apply:
        print("dry-run : aucun fichier écrit. Relancer avec --apply après arrêt du service.")
        return
    print("ATTENTION : memory-node doit être arrêté, sinon la RAM réécrit l'index.")
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(path.name + f".bak-{ts}")
    archive = path.with_name(f"dedup-archive-{ts}.json")
    shutil.copy2(path, backup)
    new_entries, removed = apply_groups(entries, groups)
    archive.write_text(
        json.dumps(
            {
                "source": str(path),
                "backup": str(backup),
                "removed_count": len(removed),
                "entries": removed,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if isinstance(raw, dict):
        raw["entries"] = new_entries
        raw["generated"] = dt.datetime.now().isoformat(timespec="seconds")
        if isinstance(raw.get("stats"), dict):
            raw["stats"]["total"] = len(new_entries)
        payload = raw
    else:
        payload = new_entries
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"sauvegarde : {backup}")
    print(f"archive des entrées retirées : {archive}")
    print(f"entrées restantes : {len(new_entries)} (retirées {len(removed)})")


if __name__ == "__main__":
    main()
