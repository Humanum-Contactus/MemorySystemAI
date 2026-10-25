#!/usr/bin/env python3
"""Fusion « Autonomie inhibée » identiques à un survivant (M719), SANS perte.

Dry-run par défaut. --apply (service ARRÊTÉ, après sauvegarde) :
  - retire les doublons encore présents (texte normalisé + C + N identiques au survivant),
    archive JSON complète de ces entrées, redirige leurs corrélations vers le survivant ;
  - écrit dans le survivant : occurrences (total, survivant compris) et
    occurrence_dates (une par occurrence, ordre chronologique).
Sources des occurrences : survivant + doublons présents + archives --archive
(retirés auparavant) + renforcements « même inhibition d'autonomie répétée »
du survivant (code patché, sans compteur).
Heures : organism.log (« autonomy tick skipped=True … inhibée par ma mémoire »).
Elles ne sont utilisées pour un jour que si le nombre de ticks bloqués du jour
== nombre d'occurrences du jour (correspondance 1 pour 1 dans l'ordre) ; sinon
on garde la date au jour, et le jour est signalé.
Rien d'autre n'est modifié ; l'exposant du survivant n'est pas changé.
"""
# À QUOI SERT CE FICHIER : regrouper les souvenirs « Autonomie inhibée »
# identiques en UN survivant qui garde le NOMBRE d'occurrences et la DATE de
# chacune (décision de Vincent, phase V). Les heures viennent du journal du
# nœud (--log) seulement si elles correspondent une pour une ; sinon, date du jour.
# COMMENT L'ESSAYER (sur une copie) :
#   python3 fusion_autonomie_occurrences.py --index copie.json --keep <ID> --archive archive.json
#   ... puis --apply. Version identique à celle exécutée sur le nœud le 25.10.2026.
import argparse, collections, datetime as dt, json, shutil
from pathlib import Path
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Zurich")
REASON = "même inhibition d'autonomie répétée"
def key(e): return " ".join((e.get("data") or "").lower().split())
def num(e):
    try: return int(str(e.get("id", "")).lstrip("Mm") or 0)
    except ValueError: return 0
ap = argparse.ArgumentParser()
ap.add_argument("--index", required=True); ap.add_argument("--keep", default="M719")
ap.add_argument("--archive", action="append", default=[]); ap.add_argument("--log")
ap.add_argument("--apply", action="store_true")
a = ap.parse_args(); p = Path(a.index)
raw = json.loads(p.read_text(encoding="utf-8")); entries = raw["entries"]
keep = next(e for e in entries if e["id"] == a.keep)
K = (key(keep), keep["fundamental"], keep["state"])
assert K[0].startswith("autonomie inhibée:"), "survivant inattendu"
present = [e for e in entries if e["id"] != keep["id"] and (key(e), e.get("fundamental"), e.get("state")) == K]
archived = []
for f in a.archive:
    for e in json.loads(Path(f).read_text(encoding="utf-8")):
        if (key(e), e.get("fundamental"), e.get("state")) == K: archived.append(e)
        else: raise SystemExit(f"archive {f} : entrée {e.get('id')} différente du survivant — arrêt")
ids = [keep["id"]] + [e["id"] for e in present] + [e["id"] for e in archived]
if len(ids) != len(set(ids)): raise SystemExit("ids en double entre index et archive — arrêt")
if keep.get("occurrences"): raise SystemExit("le survivant a déjà un compteur — arrêt (déjà fusionné ?)")
occ = []  # (jour, ordre, source)
for e in sorted([keep] + present + archived, key=num): occ.append((e["date"], num(e), e["id"]))
for i, r in enumerate(keep.get("reinforcement_log") or []):
    if REASON in (r.get("reason") or ""): occ.append((r["date"], 10**9 + i, f"{keep['id']}:renforcement#{i+1}"))
occ.sort()
perday = collections.Counter(d for d, _, _ in occ)
ticks = collections.defaultdict(list)
if a.log:
    for l in Path(a.log).read_bytes().decode("utf-8", "replace").splitlines():
        if "autonomy tick skipped=True" in l and "inhibée par ma mémoire" in l:
            try: t = dt.datetime.fromisoformat(l[:19])
            except ValueError: continue
            ticks[t.date().isoformat()].append(t)
# Ordre du log conservé (pas de tri) : au passage heure d'été → hiver,
# l'heure 02:xx se répète ; la 2e série reçoit fold=1 (UTC+1).
for d, lst in ticks.items():
    prev, fold, fixed = None, 0, []
    for t in lst:
        if prev is not None and t < prev: fold = 1
        if t.hour >= 3: fold = 0
        fixed.append(t.replace(tzinfo=TZ, fold=fold)); prev = t
    ticks[d] = fixed
dates, flagged = [], []
byday = collections.defaultdict(list)
for o in occ: byday[o[0]].append(o)
for d in sorted(byday):
    lst = byday[d]; tk = ticks.get(d, [])
    if len(tk) == len(lst):
        dates += [t.isoformat(timespec="seconds") for t in tk]
    else:
        flagged.append((d, len(lst), len(tk))); dates += [d] * len(lst)
print(f"entrées index : {len(entries)} | survivant {keep['id']} e{keep['exposant']}")
print(f"occurrences : {len(occ)} = 1 survivant + {len(present)} doublons présents + {len(archived)} archivés + {len(occ)-1-len(present)-len(archived)} renforcements")
for d in sorted(byday): print(f"  {d} : {len(byday[d])} occurrence(s), ticks log {len(ticks.get(d, []))} → {'heures du log' if (d, len(byday[d]), len(ticks.get(d, []))) not in flagged else 'DATE AU JOUR SEULEMENT'}")
print(f"première {dates[0]} | dernière {dates[-1]} | jours sans heure : {flagged or 'aucun'}")
chk = [dt.datetime.fromisoformat(x) for x in dates if "T" in x]
if any(b <= a_ for a_, b in zip(chk, chk[1:])): raise SystemExit("dates non strictement croissantes — arrêt")
print(f"index après : {len(entries) - len(present)} entrées")
if not a.apply: print("DRY-RUN : rien écrit."); raise SystemExit(0)
ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(p, p.with_name(p.name + f".bak-occurrences-{ts}"))
if present:
    p.with_name(f"autonomie-archive-{ts}.json").write_text(json.dumps(present, ensure_ascii=False, indent=1), encoding="utf-8")
gone = {e["id"] for e in present}
out = []
for e in entries:
    if e["id"] in gone: continue
    if e.get("correlations"):
        new = []
        for c in e["correlations"]:
            c = keep["id"] if c in gone else c
            if c != e["id"] and c not in new: new.append(c)
        e["correlations"] = new
    out.append(e)
keep["occurrences"] = len(occ); keep["occurrence_dates"] = dates
raw["entries"] = out
p.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"APPLIQUÉ : {len(entries)} → {len(out)} ; {keep['id']} occurrences={len(occ)}")
