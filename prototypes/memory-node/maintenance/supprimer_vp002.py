#!/usr/bin/env python3
"""Supprime VP002 de state/voice_persons.json (fiche + empreintes + étiquette + clips).
last_seen -> None (valeur par défaut de VoicePersonMemory) s'il pointe VP002 ou un clip tts_self_.
Ne touche à rien d'autre. Usage: supprimer_vp002.py <fichier> [--apply]"""
# À QUOI SERT CE FICHIER : retirer la fausse fiche voix VP002 (c'était ma propre
# voix de synthèse, enregistrée par erreur avant la phase W). Rien d'autre n'est
# touché ; le script vérifie que les autres fiches restent identiques (assert).
# COMMENT L'ESSAYER : toujours sur une COPIE d'abord, service arrêté pour le vrai :
#   python3 supprimer_vp002.py /tmp/copie_voice_persons.json          # montre
#   python3 supprimer_vp002.py /tmp/copie_voice_persons.json --apply  # écrit
# Version identique à celle exécutée sur le nœud le 25.10.2026.
import json, sys, hashlib
p = sys.argv[1]; apply = "--apply" in sys.argv
raw = open(p, "rb").read(); d = json.loads(raw)
before = {x["id"]: json.dumps(x, sort_keys=True) for x in d["persons"]}
assert "VP002" in before, "VP002 absent"
d["persons"] = [x for x in d["persons"] if x["id"] != "VP002"]
ls = d.get("last_seen") or {}
reset = ls.get("id") == "VP002" or str(ls.get("clip") or "").startswith("tts_self_")
if reset: d["last_seen"] = None
for x in d["persons"]: assert json.dumps(x, sort_keys=True) == before[x["id"]]
print("avant", sorted(before), "après", [x["id"] for x in d["persons"]], "last_seen remis à None:", reset,
      "pending", len(d["pending"]), "(inchangé)")
if apply:
    open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))
    print("APPLIQUÉ sha", hashlib.sha256(open(p, "rb").read()).hexdigest())
