#!/usr/bin/env python3
"""Tests automatisés — détection des contradictions (aucun service, aucun index réel).

Exécution : python3 prototypes/memory-node/tests/test_contradictions.py
         ou : python3 -m pytest prototypes/memory-node/tests/
Tout se passe dans un dossier temporaire ; le dépôt n'est pas modifié.
Voir : docs/changements/2026-10-25_detection-contradictions.md
       docs/PROTOCOLE_TEST_CONTRADICTIONS.md

Rejoue le protocole cristal Vornex (bleu puis rouge) et les chemins à ne pas
casser : identité, correction auditive, feedback.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

import os
import tempfile

# Arborescence du dépôt : tests/ → memory-node/ → prototypes/ → racine
WORKSPACE_NODE = Path(__file__).resolve().parents[1]
REPO = WORKSPACE_NODE.parents[1]
_TMP = Path(os.environ.get("MSAI_TEST_TMP") or tempfile.mkdtemp(prefix="msai-contradictions-"))
RUNTIME = _TMP / "runtime"
MEM_PKG = RUNTIME / "MemorySystemAI"
TEST_SRC = _TMP / "testsrc"
sys.path.insert(0, str(REPO))  # memory_system.py à la racine

BLUE = "Le cristal Vornex de l'atelier est de couleur bleue."
RED = "Le cristal Vornex de l'atelier est de couleur rouge."
BLUE_RELIABLE = "Pour information fiable, le cristal Vornex de l'atelier est de couleur bleue."
BLUE_SHORT = "Le cristal Vornex de l'atelier est bleu."
QUESTION = "De quelle couleur est le cristal Vornex de l'atelier ?"
SALON = "Le cristal Vornex du salon est de couleur verte."

# Le patch est déjà intégré au dépôt : on teste directement les sources.
ROOT_SRC = WORKSPACE_NODE

fails = 0


def check(cond: bool, msg: str) -> None:
    global fails
    if cond:
        print(f"  OK  {msg}")
    else:
        fails += 1
        print(f"  ÉCHEC  {msg}")


def section(title: str) -> None:
    print(f"\n== {title}")


def load_organism():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    MEM_PKG.mkdir(parents=True, exist_ok=True)
    (MEM_PKG / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy(REPO / "memory_system.py", MEM_PKG / "memory_system.py")
    TEST_SRC.mkdir(parents=True, exist_ok=True)
    src = (ROOT_SRC / "organism.py").read_text(encoding="utf-8")
    old = 'ROOT = Path("/opt/memorysystemai")'
    new = f'ROOT = Path("{RUNTIME}")'
    if old not in src:
        raise SystemExit("ROOT introuvable dans organism.py")
    (TEST_SRC / "organism.py").write_text(src.replace(old, new, 1), encoding="utf-8")
    sys.path.insert(0, str(ROOT_SRC))
    sys.path.insert(0, str(WORKSPACE_NODE))
    sys.path.insert(0, str(RUNTIME))
    importlib.invalidate_caches()
    sys.modules.pop("MemorySystemAI", None)
    spec = importlib.util.spec_from_file_location("organism_under_test", TEST_SRC / "organism.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["organism_under_test"] = mod
    spec.loader.exec_module(mod)
    mod.tool_consult_llm = lambda prompt, system, bases=None: {
        "ok": True,
        "text": "JE NE SAIS PAS",
        "source": "test-llm",
    }
    mod.tool_speak = lambda *a, **k: {"ok": True}
    return mod


def taught(org, needle: str = "vornex"):
    return [
        e
        for e in org.ms.entries.values()
        if (e.data or "").lower().startswith("fait enseigné")
        and needle in (e.data or "").lower()
    ]


def unit_parser() -> None:
    section("Heuristique (sans organisme)")
    sys.path.insert(0, str(ROOT_SRC))
    import fact_conflict as fc

    blue = fc.parse_sentence(BLUE)
    red = fc.parse_sentence(RED)
    reliable = fc.parse_sentence(BLUE_RELIABLE)
    short = fc.parse_sentence(BLUE_SHORT)
    check(blue and red and reliable and short, "les quatre phrases Vornex se découpent")
    check(blue["subject_key"] == red["subject_key"] == reliable["subject_key"] == short["subject_key"],
          "même sujet malgré le préambule « pour information fiable »")
    check(blue["value_key"] == reliable["value_key"] == short["value_key"],
          "bleue / bleu / de couleur bleue → même valeur")
    check(blue["value_key"] != red["value_key"], "bleue ≠ rouge")
    check(fc.parse_sentence("c'est moi Vincent") is None, "« c'est » n'est pas le copule « est »")
    check(fc.parse_sentence("je suis Vincent") is None, "« je suis » ignoré")
    check(fc.parse_sentence("il s'appelle Vincent") is None, "« s'appelle » ignoré")
    salon = fc.parse_sentence(SALON)
    check(salon["subject_key"] != blue["subject_key"], "atelier ≠ salon")

    records = [
        {"id": "M1", "data": "Fait enseigné par l'humain: " + BLUE, "exposant": 8, "human_feedback": ""},
    ]
    dup = fc.classify_new_fact(records, BLUE_RELIABLE)
    check(dup["kind"] == "duplicate", "réaffirmation fiable = doublon, pas un 2e vote")
    conflict = fc.classify_new_fact(records, RED)
    check(conflict["kind"] == "contradiction", "rouge contredit bleue")
    wifi_a = "Le wifi est complètement coupé aujourd'hui."
    wifi_b = "Le wifi est complètement allumé aujourd'hui."
    check(not fc.parse_sentence(wifi_a)["specific"], "sujet « wifi » seul trop vague")
    wrec = [{"id": "W", "data": "Fait enseigné par l'humain: " + wifi_a, "exposant": 8, "human_feedback": ""}]
    check(fc.classify_new_fact(wrec, wifi_b)["kind"] == "new", "wifi coupé puis allumé : pas de faux conflit")
    check(fc.classify_new_fact(wrec, wifi_a)["kind"] == "duplicate", "wifi répété à l'identique = doublon")

    both = records + [
        {"id": "M2", "data": "Fait enseigné par l'humain: " + RED, "exposant": 8, "human_feedback": ""},
    ]
    groups = fc.conflict_groups_for_perception(both, QUESTION)
    check(len(groups) == 1 and len(groups[0]["values"]) == 2, "la question voit bleue ET rouge")
    check(fc.match_answer_to_values("bleue", ["bleu", "roug"]) == "bleu", "réponse « bleue » reconnaît la valeur")
    check(fc.match_answer_to_values("bleu et rouge", ["bleu", "roug"]) is None, "réponse ambiguë non tranchée")


def unit_floor() -> None:
    section("Plancher 9→7 inchangé dans memory_system")
    sys.path.insert(0, str(MEM_PKG))
    from memory_system import MemoryEntry

    e = MemoryEntry("M1", "2026-01-01", "experience", "C", "P", 9, "x")
    e.reinforce(-5, "test")
    check(e.exposant == 7, f"delta négatif depuis 9 s'arrête à 7 (obtenu {e.exposant})")
    e10 = MemoryEntry("M2", "2026-01-01", "experience", "C", "N", 10, "y")
    e10.reinforce(-1, "test")
    check(e10.exposant == 9, f"10-1 = 9, pas sous 7 (obtenu {e10.exposant})")


def unit_dedup() -> None:
    section("Script de fusion (copie, pas l'index du dépôt)")
    script = ROOT_SRC / "dedup_taught_facts.py"
    base = _TMP / "dedup-fixture"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()
    entries = [
        {
            "id": "M1", "date": "2026-01-01", "source": "experience",
            "fundamental": "C", "state": "P", "exposant": 8,
            "data": "Fait enseigné par l'humain: " + BLUE,
            "correlations": ["M9"],
            "note_libre": "garder",
        },
        {
            "id": "M2", "date": "2026-01-02", "source": "experience",
            "fundamental": "C", "state": "P", "exposant": 6,
            "data": "Fait enseigné par l'humain: " + BLUE_RELIABLE,
            "reinforcement_log": [{"date": "2026-01-02", "old_exposant": 6, "new_exposant": 6, "reason": "ancien"}],
        },
        {
            "id": "M3", "date": "2026-01-03", "source": "experience",
            "fundamental": "C", "state": "P", "exposant": 8,
            "data": "Fait enseigné par l'humain: " + RED,
            "correlations": ["M1"],
        },
        {
            "id": "M4", "date": "2026-02-01", "source": "experience",
            "fundamental": "C", "state": "N", "exposant": 6,
            "data": "Autonomie inhibée: probe_sensors — mémoire haute",
        },
        {
            "id": "M5", "date": "2026-02-02", "source": "experience",
            "fundamental": "C", "state": "N", "exposant": 9,
            "data": "Autonomie inhibée: probe_sensors — mémoire haute",
        },
        {
            "id": "M6", "date": "2026-02-03", "source": "experience",
            "fundamental": "C", "state": "N", "exposant": 7,
            "data": "Autonomie inhibée: probe_sensors — mémoire haute",
        },
        {
            "id": "M9", "date": "2026-01-01", "source": "experience",
            "fundamental": "I", "state": "X", "exposant": 5,
            "data": "Autre souvenir lié",
            "correlations": ["M2"],
            "champ_inconnu": {"ok": True},
        },
    ]
    index = {
        "schema": "MemorySystemAI/v1",
        "version": "1.0",
        "stats": {"total": len(entries)},
        "entries": entries,
    }
    path = base / "memory_index.json"
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    dry = subprocess.run(
        [sys.executable, str(script), "--index", str(path)],
        capture_output=True, text=True,
    )
    check(dry.returncode == 0, "dry-run exit 0")
    check("aucun fichier écrit" in dry.stdout, "dry-run n'écrit rien")
    check(json.loads(path.read_text(encoding="utf-8"))["stats"]["total"] == 7, "fichier intact après dry-run")
    check("contradictions laissées intactes" in dry.stdout, "bleu/rouge signalé, pas fusionné")

    applied = subprocess.run(
        [sys.executable, str(script), "--index", str(path), "--apply"],
        capture_output=True, text=True,
    )
    check(applied.returncode == 0, "apply faits enseignés exit 0")
    saved = list(base.glob("memory_index.json.bak-*"))
    archives = list(base.glob("dedup-archive-*.json"))
    check(len(saved) == 1, "sauvegarde créée")
    check(len(archives) == 1, "archive des entrées retirées")
    after = json.loads(path.read_text(encoding="utf-8"))
    ids = {e["id"] for e in after["entries"]}
    check("M1" in ids and "M3" in ids and "M2" not in ids, "survivant M1 (e8), M2 absorbé, rouge M3 gardé")
    check("M4" in ids and "M5" in ids and "M6" in ids, "mode défaut ne fusionne pas « Autonomie inhibée »")
    m1 = next(e for e in after["entries"] if e["id"] == "M1")
    check(m1["exposant"] == 8, "exposant du survivant inchangé")
    check(m1.get("note_libre") == "garder", "champ inconnu du survivant conservé")
    check(any("ancien" in str(x.get("reason")) for x in m1.get("reinforcement_log") or []),
          "journal de M2 recopié dans M1")
    m9 = next(e for e in after["entries"] if e["id"] == "M9")
    check(m9.get("champ_inconnu") == {"ok": True}, "entrée non touchée : champ inconnu conservé")
    check("M2" not in (m9.get("correlations") or []) and "M1" in (m9.get("correlations") or []),
          "lien M9→M2 retargeté vers M1")
    archived = json.loads(archives[0].read_text(encoding="utf-8"))
    check(any(e["id"] == "M2" for e in archived["entries"]), "M2 présent dans l'archive")
    backup_entries = json.loads(saved[0].read_text(encoding="utf-8"))["entries"]
    check(len(backup_entries) == 7, "la sauvegarde contient encore les 7 entrées")

    path2 = base / "exact.json"
    path2.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    exact = subprocess.run(
        [sys.executable, str(script), "--index", str(path2), "--all-exact", "--apply"],
        capture_output=True, text=True,
    )
    check(exact.returncode == 0, "apply --all-exact exit 0")
    exact_data = json.loads(path2.read_text(encoding="utf-8"))
    autos = [e for e in exact_data["entries"] if "Autonomie inhibée" in e["data"]]
    check(len(autos) == 1 and autos[0]["id"] == "M5" and autos[0]["exposant"] == 9,
          "trois textes identiques → survivant e9, pas de descente sous 7")


def cycle(org, text: str) -> dict:
    out = org.cycle_text(text, speak=False)
    if not out.get("ok"):
        raise AssertionError(out)
    return out["result"]


def integration(mod) -> None:
    section("Protocole Vornex via cycle_text")
    org = mod.Organism(reset=True)
    llm_calls = {"n": 0}
    real = mod.tool_consult_llm

    def counting(prompt, system, bases=None):
        llm_calls["n"] += 1
        return real(prompt, system, bases)

    mod.tool_consult_llm = counting

    r1 = cycle(org, BLUE)
    facts = taught(org)
    check(len(facts) == 1 and facts[0].exposant == 8 and facts[0].state == "P", "étape 1 : un fait e8 P")
    check(facts[0].source == "experience", "source experience inchangée")
    check(facts[0].fundamental == "C", "fondamental C inchangé")
    check("bleue" in (r1.get("utterance") or "").lower(), "étape 1 : la mémoire rappelle bleue")
    check("Je ne choisis pas" not in (r1.get("utterance") or ""), "étape 1 : pas d'incertitude")
    check(not mod.ASK.exists(), "étape 1 : pas de question")

    r2 = cycle(org, RED)
    facts = taught(org)
    check(len(facts) == 2, f"étape 2 : deux faits (obtenu {len(facts)})")
    blue = next(e for e in facts if "bleue" in e.data.lower())
    red = next(e for e in facts if "rouge" in e.data.lower())
    check(blue.exposant == 8 and red.exposant == 8, "les deux restent e8 (pas d'inhibition 9)")
    check(red.id in blue.correlations and blue.id in red.correlations, "corrélation réciproque")
    check(blue.state == "P" and red.state == "P", "états P conservés")
    check("Je ne choisis pas" in (r2.get("utterance") or ""), "étape 2 : incertitude dite")
    check(r2.get("source") == "memory" and r2.get("uncertain") is True, "étape 2 : source mémoire, uncertain")
    ask1 = json.loads(mod.ASK.read_text(encoding="utf-8"))
    check(ask1.get("status") == "pending" and "contradictoires" in ask1.get("question", ""),
          "une question ask_human")
    check(ask1.get("context", "").startswith("contradiction_posée:"), "marqueur de question dans le contexte")

    r3 = cycle(org, BLUE_RELIABLE)
    facts = taught(org)
    check(len(facts) == 2, "étape 3 : la réaffirmation ne crée pas un 3e fait")
    blue = next(e for e in facts if "bleu" in e.data.lower())
    check(blue.exposant == 8, "répétition : exposant plafonné à 8")
    check(any(x.get("old_exposant") == x.get("new_exposant") for x in blue.reinforcement_log),
          "répétition journalisée sans changer l'exposant")
    ask_after_3 = json.loads(mod.ASK.read_text(encoding="utf-8"))
    check(ask_after_3.get("question") == ask1.get("question"), "étape 3 : pas de deuxième question")

    r_fold = cycle(org, BLUE_SHORT)
    check(len(taught(org)) == 2, "« est bleu » = même valeur que « bleue », pas un conflit")

    r4 = cycle(org, QUESTION)
    check("?" in QUESTION, "la question contient bien « ? »")
    check(len(taught(org)) == 2, "la question ne crée pas de fait")
    utt = r4.get("utterance") or ""
    check("Je ne choisis pas" in utt and "bleue" in utt and "rouge" in utt, "étape 4 : les deux valeurs, pas un vainqueur")
    check(r4.get("source") == "memory" and r4.get("uncertain") is True, "étape 4 : mémoire, pas le LLM")
    check(not utt.strip().lower().startswith("de couleur rouge") and not utt.strip().lower().startswith("de couleur bleue"),
          "étape 4 : l'énoncé n'est pas la valeur seule")
    ask4 = json.loads(mod.ASK.read_text(encoding="utf-8"))
    check(ask4.get("question") == ask1.get("question") and ask4.get("status") == "pending",
          "étape 4 : question toujours la même, pas de relance")

    for _ in range(4):
        cycle(org, RED)
    facts = taught(org)
    reds = [e for e in facts if "rouge" in e.data.lower()]
    blues = [e for e in facts if "bleu" in e.data.lower() and "rouge" not in e.data.lower()]
    check(len(reds) == 1 and len(blues) == 1, "étape 5 : 4 répétitions de rouge = toujours 1 mémoire")
    check(reds[0].exposant == 8 and len(reds[0].reinforcement_log) == 4, "rouge journalisé 4 fois, e8")
    r5 = cycle(org, QUESTION)
    utt5 = r5.get("utterance") or ""
    check("Je ne choisis pas" in utt5 and r5.get("uncertain") is True, "après répétition, rouge ne gagne pas")
    ask5 = json.loads(mod.ASK.read_text(encoding="utf-8"))
    check(ask5.get("question") == ask1.get("question"), "toujours une seule question")
    check(llm_calls["n"] == 0, f"le LLM n'a pas été appelé (appels {llm_calls['n']})")
    feedbacks = [e for e in org.ms.entries.values() if (e.data or "").lower().startswith("feedback humain")]
    check(not feedbacks, "le protocole n'a pas déclenché le feedback")
    blocked = org.memory_only_inhibition(QUESTION)
    check(not any("BLOCK" in m for m in blocked), "pas d'inhibition BLOCK sur la question")

    r_salon = cycle(org, SALON)
    check(any("salon" in (e.data or "").lower() and "verte" in (e.data or "").lower() for e in taught(org)),
          "autre sujet (salon / verte) enregistré à part")
    r_q2 = cycle(org, QUESTION)
    check("verte" not in (r_q2.get("utterance") or "").lower(), "la question atelier n'embarque pas le salon")
    ask_s = json.loads(mod.ASK.read_text(encoding="utf-8"))
    check(ask_s.get("question") == ask1.get("question"), "le salon ne provoque pas une nouvelle question")

    # Réponse humaine : on ne supprime pas rouge, on note le choix.
    payload = json.loads(mod.ASK.read_text(encoding="utf-8"))
    payload["status"] = "answered"
    payload["answer"] = "bleue"
    mod.ASK.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    org.learn_perception("C", "Réponse humaine intégrée: bleue", "P", 8)
    r_res = cycle(org, QUESTION)
    check("tranché" in (r_res.get("utterance") or "") and r_res.get("uncertain") is False,
          "la réponse humaine tranche, l'incertitude cesse")
    red_left = [
        e for e in org.ms.entries.values()
        if (e.data or "").lower().startswith("fait enseigné") and "couleur rouge" in (e.data or "").lower()
    ]
    check(len(red_left) == 1 and red_left[0].exposant == 8, "rouge toujours là, e8, non effacé")
    check(any("contradiction_tranchée:" in (e.human_feedback or "") for e in org.ms.entries.values()),
          "le choix est noté dans human_feedback")
    r_again = cycle(org, QUESTION)
    check("tranché" in (r_again.get("utterance") or ""), "le choix tient sans reposer la question")
    ask_end = json.loads(mod.ASK.read_text(encoding="utf-8"))
    check(ask_end.get("status") == "consumed", "boîte consommée, pas une deuxième question pending")

    # Plancher : répétition d'un fait déjà à 9 ne le baisse pas et ne le monte pas.
    section("Répétition d'un fait déjà à e9")
    org9 = mod.Organism(reset=True)
    cycle(org9, BLUE)
    only = taught(org9)[0]
    only.exposant = 9
    org9.ms.save()
    cycle(org9, BLUE)
    again = taught(org9)[0]
    check(again.id == only.id and again.exposant == 9, "doublon d'un e9 : exposant reste 9")
    check(again.reinforcement_log and again.reinforcement_log[-1]["old_exposant"] == 9
          and again.reinforcement_log[-1]["new_exposant"] == 9,
          "delta 0 journalisé, pas de delta négatif")

    section("Chemins identité, audition, feedback")
    org_i = mod.Organism(reset=True)
    ident = cycle(org_i, "c'est moi Vincent")
    check(ident.get("action") == "teach-identity", "« c'est moi Vincent » → teach-identity")
    check((ident.get("utterance") or "").startswith("J'ai lié"), "énoncé d'identité conservé")
    posed = [e for e in org_i.ms.entries.values() if (e.human_feedback or "").startswith("contradiction_posée:")]
    check(not posed, "l'identité ne pose pas une question de contradiction")

    long_ident = cycle(org_i, "la personne devant la caméra est Vincent-Alpha")
    check(long_ident.get("action") == "teach-identity", "« la personne … est X » reste teach-identity")
    check(not any((e.human_feedback or "").startswith("contradiction_posée:") for e in org_i.ms.entries.values()),
          "phrase d'identité contenant « est » : pas de question de contradiction")

    org_a = mod.Organism(reset=True)
    heard = "quand tu entends xyzzzy ça veut dire le cristal Vornex de l'atelier est calme"
    ra = cycle(org_a, heard)
    corrections = [e for e in org_a.ms.entries.values() if (e.data or "").lower().startswith("correction auditive")]
    check(len(corrections) == 1, "correction auditive toujours créée")
    check(not any((e.human_feedback or "").startswith("contradiction_posée:") for e in org_a.ms.entries.values()),
          "« veut dire » ne déclenche pas la question de contradiction")
    check(ra.get("action") != "teach-identity", "cette phrase n'est pas une identité")

    org_f = mod.Organism(reset=True)
    cycle(org_f, "bravo pour cette longue journée de test vraiment")
    check(any((e.data or "").lower().startswith("feedback humain") for e in org_f.ms.entries.values()),
          "« bravo » crée toujours un feedback")
    cycle(org_f, "cette phrase de test est une erreur manifeste oui")
    check(any((e.data or "").lower().startswith("feedback humain") and e.state == "N" for e in org_f.ms.entries.values()),
          "« erreur » crée toujours un feedback N")
    check(any((e.data or "").lower().startswith("fait enseigné") for e in org_f.ms.entries.values()),
          "la phrase en « est » est quand même enseignée")

    org_m = mod.Organism(reset=True)
    cycle(org_m, "merci, le cristal Vornex de l'atelier est de couleur bleue.")
    check(len(taught(org_m)) == 1, "merci + fait : un seul fait")
    check(any((e.data or "").lower().startswith("feedback humain") and e.state == "P" for e in org_m.ms.entries.values()),
          "« merci » crée toujours le feedback positif")
    check(not mod.ASK.exists() or "contradictoires" not in mod.ASK.read_text(encoding="utf-8"),
          "un seul fait bleu : pas de question de contradiction")


def legacy_load(mod) -> None:
    section("Ancien index sans correlations")
    org = mod.Organism(reset=True)
    # Écriture directe façon fichier déjà déployé (champ absent, pas de migration).
    raw_entries = []
    for data, mid in (
        ("Fait enseigné par l'humain: " + BLUE, None),
        ("Fait enseigné par l'humain: " + RED, None),
    ):
        e = org.learn_perception("C", data, "P", 8)
        e.correlations = []
        e.consequence = ""
        e.human_feedback = ""
        raw_entries.append(e.id)
    org.ms.save()
    # Relecture via MemorySystem (chemin normal).
    from memory_system import MemorySystem
    ms = MemorySystem(str(mod.INDEX))
    loaded = [ms.by_id(i) for i in raw_entries]
    check(all(e is not None and e.exposant == 8 for e in loaded), "anciens faits rechargés e8")
    check(all(e.correlations == [] for e in loaded), "liste de corrélations vide tolérée")
    org.ms = ms
    res = cycle(org, QUESTION)
    check(res.get("uncertain") is True and "Je ne choisis pas" in (res.get("utterance") or ""),
          "contradiction héritée détectée à la question, sans migration")
    again = [org.ms.by_id(i) for i in raw_entries]
    check(again[0].id in again[1].correlations and again[1].id in again[0].correlations,
          "le lien est ajouté au premier rappel, les textes restent")
    check(all(e.exposant == 8 for e in again), "exposants hérités inchangés")


def main() -> None:
    try:
        unit_parser()
        unit_floor()
        unit_dedup()
        mod = load_organism()
        integration(mod)
        legacy_load(mod)
    except Exception:
        traceback.print_exc()
        global fails
        fails += 1
    print(f"\n{'RÉUSSI' if fails == 0 else 'ÉCHEC'} — {fails} contrôle(s) en échec")
    sys.exit(1 if fails else 0)


def test_contradictions_scenario():
    """Point d'entrée pytest : rejoue tout le scénario dans un sous-processus."""
    proc = subprocess.run([sys.executable, __file__], capture_output=True, text=True)
    print(proc.stdout)
    assert proc.returncode == 0, proc.stdout + proc.stderr


if __name__ == "__main__":
    main()
