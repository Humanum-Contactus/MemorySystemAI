#!/usr/bin/env python3
"""Tests automatisés — « Autonomie inhibée » compté au lieu d'être recopié
(phases U et V du journal d'octobre 2026).

À QUOI SERT CE FICHIER
----------------------
Quand la boucle de fond veut agir et que la mémoire l'en empêche, le nœud
garde une trace « Autonomie inhibée: … ». Avant la correction, il créait un
NOUVEAU souvenir à chaque tick (toutes les 5 minutes) : des centaines de
copies. Maintenant le même refus RENFORCE un seul souvenir (plafond 8) et
compte ses occurrences avec leurs dates. Ce test vérifie :
  1. trois refus identiques → un seul souvenir, occurrences = 3, 3 dates ;
  2. les champs `occurrences` / `occurrence_dates` survivent à la sauvegarde
     et au rechargement (memory_system.py) ;
  3. les autres souvenirs ne reçoivent pas ces champs ;
  4. contradiction_ids est vide quand il n'y a pas de contradiction (phase U) ;
  5. le script de fusion reconstruit le compteur depuis une archive, sans perte.

Tout est fabriqué dans un dossier temporaire : aucun index réel.

COMMENT L'ESSAYER
-----------------
    python3 prototypes/memory-node/tests/test_autonomie.py
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

NODE = Path(__file__).resolve().parents[1]

# On réutilise la préparation d'organisme isolé de test_contradictions.py
# (dossier jetable, LLM et voix imités).
spec = importlib.util.spec_from_file_location("tc_helpers", NODE / "tests" / "test_contradictions.py")
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)

fails = 0


def check(cond: bool, msg: str) -> None:
    global fails
    print(("  OK  " if cond else "  ÉCHEC  ") + msg)
    fails += 0 if cond else 1


mod = tc.load_organism()
org = mod.Organism(reset=True)

print("== 1. Trois refus identiques → un seul souvenir compté")
# On simule une norme qui bloque l'action : la mémoire répond « BLOCK ».
org.memory_only_inhibition = lambda text: ["BLOCK norme de test"]
org.inhibition_reason = lambda text: {"id": "M0", "data": "norme de test"}
PREFIX = "Autonomie inhibée: initiative_test"


def inh():
    return [e for e in org.ms.entries.values() if (e.data or "").startswith(PREFIX)]


n0 = len(org.ms.entries)
for _ in range(3):
    org.autonomy.through_memory("initiative_test essai", "C", "x")
check(len(inh()) == 1, f"un seul souvenir (obtenu {len(inh())})")
check(len(org.ms.entries) == n0 + 1, "une seule entrée ajoutée à l'index")
m = inh()[0]
check(m.occurrences == 3 and len(m.occurrence_dates) == 3, f"occurrences={m.occurrences}, dates={len(m.occurrence_dates)}")
check(all("T" in d and ("+" in d or "Z" in d or "-" in d[19:]) for d in m.occurrence_dates), "dates ISO avec fuseau")
check(m.exposant <= 8, "plafond 8 respecté")

print("== 2. Champs conservés à la sauvegarde et au rechargement")
org.ms.save()
ms_mod = sys.modules[type(org.ms).__module__]
ms2 = ms_mod.MemorySystem(str(org.ms.index_path) if hasattr(org.ms, "index_path") else str(tc.MEM_PKG / "memory_index.json"))
m2 = ms2.by_id(m.id)
check(m2 is not None and m2.occurrences == 3 and m2.occurrence_dates == m.occurrence_dates, "rechargement : champs intacts")

print("== 3. Les autres souvenirs ne reçoivent pas ces champs")
others = [e for e in org.ms.entries.values() if e.id != m.id and "occurrences" in e.to_dict()]
check(not others, "aucun autre souvenir n'a de compteur")

print("== 4. contradiction_ids vide sans contradiction")
org.memory_only_inhibition = lambda text: []
out = org.cycle_text("La lampe Testor du garage est de couleur verte.", speak=False)
res = out.get("result") or out
check(not res.get("contradiction_ids"), "premier fait : contradiction_ids vide")
out = org.cycle_text("La lampe Testor du garage est de couleur jaune.", speak=False)
res = out.get("result") or out
check(len(res.get("contradiction_ids") or []) == 2, "vraie contradiction : deux ids")

print("== 5. Script de fusion avec archive (index fabriqué)")
tmp = tc._TMP / "fusion"
tmp.mkdir(parents=True, exist_ok=True)
txt = "Autonomie inhibée: initiative_autonome — norme de test"


def e(i, day):
    return {"id": f"M{i}", "fundamental": "C", "state": "N", "exposant": 6, "data": txt,
            "date": day, "correlations": []}


index = {"schema": "test", "entries": [e(10, "2026-01-01"), e(11, "2026-01-02"),
                                        {"id": "M12", "fundamental": "V", "state": "P", "exposant": 5,
                                         "data": "autre", "date": "2026-01-02", "correlations": ["M11"]}]}
(tmp / "index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
(tmp / "archive.json").write_text(json.dumps([e(13, "2026-01-03")], ensure_ascii=False), encoding="utf-8")
cmd = [sys.executable, str(NODE / "maintenance" / "fusion_autonomie_occurrences.py"),
       "--index", str(tmp / "index.json"), "--keep", "M10", "--archive", str(tmp / "archive.json")]
before = (tmp / "index.json").read_bytes()
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
check((tmp / "index.json").read_bytes() == before, "dry-run : rien écrit")
subprocess.run(cmd + ["--apply"], check=True, stdout=subprocess.DEVNULL)
d = json.loads((tmp / "index.json").read_text())
keep = next(x for x in d["entries"] if x["id"] == "M10")
check([x["id"] for x in d["entries"]] == ["M10", "M12"], "doublon présent retiré, autre souvenir gardé")
check(keep["occurrences"] == 3 and len(keep["occurrence_dates"]) == 3, "compteur = 1 + 1 présent + 1 archivé")
check(keep["exposant"] == 6, "exposant du survivant inchangé")
check(d["entries"][1]["correlations"] == ["M10"], "corrélation redirigée vers le survivant")
check(any(p.name.startswith("autonomie-archive-") for p in tmp.iterdir()), "entrée retirée archivée")

print("\n" + ("RÉUSSI — 0 contrôle(s) en échec" if not fails else f"ÉCHEC — {fails} contrôle(s)"))
sys.exit(1 if fails else 0)
