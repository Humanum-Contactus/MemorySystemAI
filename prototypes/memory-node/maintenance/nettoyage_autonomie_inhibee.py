#!/usr/bin/env python3
"""Fusion des souvenirs « Autonomie inhibée: … » identiques (NON EXÉCUTÉ en prod).

Dry-run par défaut : n'écrit rien. --apply (service ARRÊTÉ, après sauvegarde) :
  1. copie <index>.bak-autonomie-<horodatage>
  2. archive JSON des entrées retirées à côté de l'index
  3. réécriture : seules les entrées retirées disparaissent ; les corrélations
     qui pointaient vers elles sont redirigées vers le survivant.
Regroupement : texte normalisé (casse/espaces) + fondamental + état.
Survivant : exposant le plus haut puis id le plus ancien. Exposant NON modifié.
"""
# HISTORIQUE (phase V) : malgré la mention « NON EXÉCUTÉ » de sa docstring,
# écrite à la préparation, ce script a été appliqué sur le nœud le 25.10.2026
# à 23:36, AVANT l'ordre d'arrêt de Vincent. Défaut constaté : il ne gardait ni
# le nombre ni les dates. Remplacé par fusion_autonomie_occurrences.py.
# Conservé pour la traçabilité ; à ne plus utiliser.
import argparse, datetime as dt, json, shutil
from pathlib import Path
PREFIX = "autonomie inhibée:"
def key(e): return " ".join((e.get("data") or "").lower().split())
def num(e):
    try: return int(str(e.get("id", "")).lstrip("Mm") or 0)
    except ValueError: return 0
ap = argparse.ArgumentParser(); ap.add_argument("--index", required=True); ap.add_argument("--apply", action="store_true")
a = ap.parse_args(); p = Path(a.index)
raw = json.loads(p.read_text(encoding="utf-8")); entries = raw["entries"] if isinstance(raw, dict) else raw
groups = {}
for e in entries:
    k = key(e)
    if k.startswith(PREFIX): groups.setdefault((k, e.get("fundamental"), e.get("state")), []).append(e)
plan = []
for (k, f, s), g in groups.items():
    if len(g) < 2: continue
    g.sort(key=lambda e: (-int(e.get("exposant") or 0), num(e)))
    plan.append((g[0], g[1:]))
removed = {e["id"]: keep["id"] for keep, rest in plan for e in rest}
print(f"entrées : {len(entries)} | souvenirs Autonomie inhibée : {sum(len(g) for g in groups.values())} en {len(groups)} texte(s) distinct(s)")
print(f"groupes fusionnables : {len(plan)} | entrées retirées : {len(removed)} | après : {len(entries) - len(removed)}")
for keep, rest in plan:
    print(f"  garder {keep['id']} e{keep.get('exposant')} ({keep.get('date')}) — retirer {len(rest)} : {rest[0]['id']} … {rest[-1]['id']} | {keep['data'][:110]}")
if not a.apply:
    print("DRY-RUN : rien écrit."); raise SystemExit(0)
ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(p, p.with_name(p.name + f".bak-autonomie-{ts}"))
p.with_name(f"autonomie-archive-{ts}.json").write_text(json.dumps([e for e in entries if e["id"] in removed], ensure_ascii=False, indent=1), encoding="utf-8")
kept = []
for e in entries:
    if e["id"] in removed: continue
    if e.get("correlations"):
        new = []
        for c in e["correlations"]:
            c = removed.get(c, c)
            if c != e["id"] and c not in new: new.append(c)
        e["correlations"] = new
    kept.append(e)
if isinstance(raw, dict): raw["entries"] = kept
else: raw = kept
p.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"APPLIQUÉ : {len(entries)} → {len(kept)}")
