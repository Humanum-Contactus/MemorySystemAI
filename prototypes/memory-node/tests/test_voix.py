#!/usr/bin/env python3
"""Tests automatisés — corrections voix (phase W du journal d'octobre 2026).

À QUOI SERT CE FICHIER
----------------------
Le nœud se parle à lui-même (« hear_self ») pour vérifier sa prononciation.
Avant la correction, il enregistrait sa PROPRE voix de synthèse comme une
personne (une fiche voix « VP002 »), et il pouvait s'écouter parler par le
micro. Ce test vérifie les quatre corrections :
  1. hear_self n'écrit plus rien dans la mémoire des voix ;
  2. les clips « tts_self_* » (ma synthèse) sont toujours ignorés ;
  3. « half-duplex » : pas d'enregistrement micro pendant que je parle,
     plus une garde de 0,5 s ;
  4. le script de maintenance supprime VP002 sans toucher au reste.

Toutes les données sont FABRIQUÉES ici (aucune vraie voix, aucun vrai nom) :
un fichier voice_persons.json minimal, des sons synthétiques (sinusoïdes).

COMMENT L'ESSAYER
-----------------
    python3 prototypes/memory-node/tests/test_voix.py
Bibliothèque standard uniquement. Code de sortie 0 = tout est OK.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
import subprocess
import sys
import tempfile
import threading
import time
import types
import wave
from pathlib import Path

# Chemins relatifs à ce fichier : marche où que soit cloné le dépôt.
NODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(NODE))
R = Path(tempfile.mkdtemp(prefix="msai-voix-"))

fails = 0


def check(cond: bool, msg: str) -> None:
    global fails
    print(("  OK  " if cond else "  ÉCHEC  ") + msg)
    fails += 0 if cond else 1


# Fabrique un WAV mono 16 kHz : une note qui ondule, assez « vocale » pour
# que voice_memory calcule une empreinte, sans être la voix de personne.
def mkwav(p: Path, sec: float = 1.5) -> None:
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"".join(
            struct.pack("<h", int(8000 * math.sin(2 * math.pi * (140 + 20 * math.sin(i / 800)) * i / 16000)
                              * (1 + 0.3 * math.sin(i / 300))))
            for i in range(int(16000 * sec))))


# Mémoire des voix fictive : VP001 = une personne, VP002 = ma propre synthèse
# (le cas à corriger). last_seen pointe sur un clip tts_self_, comme sur le nœud.
def fresh(name: str) -> Path:
    now = "2026-01-01T00:00:00"
    data = {
        "schema": "voice_persons/v1",
        "persons": [
            {"id": "VP001", "label": "Personne A", "exposant": 8, "embeddings": [[0.1, 0.2]],
             "clips": ["o_100.wav"], "seen_count": 3, "last_transcript": "", "created_at": now, "updated_at": now},
            {"id": "VP002", "label": "Synthèse", "exposant": 8, "embeddings": [[0.3, 0.4]],
             "clips": ["tts_self_1.wav"], "seen_count": 5, "last_transcript": "", "created_at": now, "updated_at": now},
        ],
        "pending": [{"id": "VU001", "embedding": [0.1, 0.2], "clip": "o_200.wav", "transcript": "", "created_at": now}],
        "last_seen": {"kind": "person", "id": "VP002", "label": "Synthèse", "clip": "tts_self_1.wav", "at": now},
    }
    p = R / name
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


import voice_memory as vm  # noqa: E402
import autonomy  # noqa: E402

print("== 1. hear_self ne calcule plus d'empreinte sur ma voix de synthèse")
vp = fresh("vp1.json")
h0 = sha(vp)
calls: list = []


# Faux organisme : juste ce dont hear_self a besoin. On note si
# voice.process_wav est appelé (il ne doit plus l'être).
class Org:
    voice = vm.VoicePersonMemory(vp)

    def learn_perception(self, *a, **k):
        calls.append(a)

    def learn_auditory_correction(self, *a, **k):
        pass


org = Org()
org.voice.process_wav = lambda *a, **k: calls.append("PROCESS_WAV") or {}
kit = autonomy.AutonomyKit.__new__(autonomy.AutonomyKit)  # sans __init__ : pas de capteurs
kit.org = org
kit.through_memory = lambda *a, **k: {"blocked": False}
tw = R / "tts_self_123.wav"
mkwav(tw)
r = kit.hear_self("Bonjour test",
                  speak_fn=lambda text, play=True: {"ok": True, "wav": str(tw), "said": text, "engine": "mock"},
                  stt_fn=lambda w: {"text": "Bonjour test"}, play=False)
check(r.get("ok") is True, "hear_self OK (synthèse et transcription imitées, aucun son)")
check("PROCESS_WAV" not in calls, "voice.process_wav non appelé")
check(sha(vp) == h0, "voice_persons.json identique octet pour octet")

print("== 2. voice_memory ignore les clips tts_self_")
vp = fresh("vp2.json")
h0 = sha(vp)
m = vm.VoicePersonMemory(vp)
res = m.process_wav(tw, transcript="x")
check(res.get("ok") is False and "tts_self" in res.get("error", ""), "process_wav(tts_self_*) ignoré")
check(sha(vp) == h0, "fichier inchangé")
p = m.label_pending_or_last("Test")
d = json.loads(vp.read_text())
check([x for x in d["persons"] if x["id"] == "VP002"][0]["label"] == "Synthèse",
      "l'étiquette ne va pas sur VP002 via un last_seen tts_self_")
check(p is not None and "tts_self_1.wav" not in (p.get("clips") or []), "étiquette posée sur un clip humain")
vp = fresh("vp3.json")
m = vm.VoicePersonMemory(vp)
m.data["pending"] = [{"id": "VU099", "embedding": [0.1], "clip": "tts_self_9.wav", "transcript": "", "created_at": "x"}]
m.data["last_seen"] = {"kind": "pending", "id": "VU099", "label": None, "clip": "tts_self_9.wav", "at": "x"}
m.save()
p = m.label_pending_or_last("Personne")
check(p is None or "tts_self_9.wav" not in (p.get("clips") or []), "un clip tts_self_ en attente n'est jamais étiqueté")
hw = R / "o_1.wav"
mkwav(hw)
_r = m.process_wav(hw)
# L'empreinte vocale demande numpy (dépendance FACULTATIVE, voir
# requirements-optional.txt). Sans numpy, on vérifie seulement que le clip
# humain n'est PAS rejeté comme « tts_self ».
if importlib.util.find_spec("numpy"):
    check(_r.get("ok") is True, "process_wav sur un clip humain fonctionne toujours")
else:
    check("tts_self" not in str(_r.get("error")), "sans numpy : clip humain non rejeté comme tts_self")

print("== 3. half-duplex SPEAKING (pas de micro pendant que je parle)")
# On charge organism.py dans un dossier jetable, comme test_contradictions.py.
spec = importlib.util.spec_from_file_location("tc_helpers", NODE / "tests" / "test_contradictions.py")
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)
o = tc.load_organism()
o.STATE = R
ev: dict = {}


# Faux « sh » : aplay dure 1 s ; arecord note l'instant où il démarre.
def fake_sh(cmd, timeout=120):
    if cmd[0] == "aplay":
        time.sleep(1.0)
        ev["play_end"] = time.monotonic()
    if cmd[0] == "arecord":
        ev["rec_start"] = time.monotonic()
        ev["speaking_at_rec"] = o.SPEAKING.is_set()
        Path(cmd[-1]).write_bytes(b"\0" * 2000)
    return types.SimpleNamespace(returncode=0, stdout="", stderr="")


o.sh = fake_sh
t = threading.Thread(target=o._play_tts, args=(["aplay", "-q", "x.wav"],))
t.start()
time.sleep(0.1)
check(o.SPEAKING.is_set(), "SPEAKING levé pendant la lecture")
o._record_wav(1)
t.join()
check(ev.get("speaking_at_rec") is False, "arecord lancé après la fin de la lecture")
check(ev["rec_start"] - ev["play_end"] >= 0.5, "garde de 0,5 s respectée")
o.SPEAKING.set()
t0 = time.monotonic()
okw = o._wait_not_speaking(max_wait=0.3)
dt = time.monotonic() - t0
o.SPEAKING.clear()
check(okw is False and dt < 1.0, "attente bornée puis abandon (jamais de blocage infini)")
check(o.SPEAK_WAIT_MAX_SEC > 90, "délai max par défaut > durée max d'aplay (90 s)")

print("== 4. suppression de VP002 (copie)")
vp = fresh("vp4.json")
before = json.loads(vp.read_text())
subprocess.run([sys.executable, str(NODE / "maintenance" / "supprimer_vp002.py"), str(vp), "--apply"],
               check=True, stdout=subprocess.DEVNULL)
after = json.loads(vp.read_text())
check([x["id"] for x in after["persons"]] == ["VP001"], "VP002 supprimé, VP001 seul")
check(after["persons"][0] == before["persons"][0], "VP001 identique")
check(after["last_seen"] is None and after["pending"] == before["pending"], "last_seen remis à None, pending inchangé")
check(vm.VoicePersonMemory(vp).summary() is not None, "fichier relu par VoicePersonMemory")

print("\n" + ("RÉUSSI — 0 contrôle(s) en échec" if not fails else f"ÉCHEC — {fails} contrôle(s)"))
sys.exit(1 if fails else 0)
