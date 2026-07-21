#!/usr/bin/env python3
"""
Outils d'autonomie / découverte pour memory-node (Sensors&MemorySystemAI).

Règle d'or : chaque interaction passe par
  1) inhibition mémoire (tags + exposant)
  2) exécution de l'outil (si non bloqué)
  3) enregistrement de l'expérience (fondamental + état + exposant)

Ce n'est PAS un mode chatbot « curiosité LLM ».
Ce sont des outils sensoriels / méta qui nourrissent memory_index.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Actions textuelles pour matches_tags (inhibition apprise)
ACT_PROBE = "probe_sensors decouvrir_corps cartographie_capteurs configuration_materielle"
ACT_LOOK = "look_around explorer_vision capturer_environnement observation_autonome"
ACT_LISTEN = "listen_ambient explorer_ambiance ecouter_environnement observation_sonore"
ACT_REACH = "reach_local reseau_local ping_passerelle voisinage_borne"
ACT_WONDER = "wonder hypothese conceptualiser_inconnu trou_memoire"
ACT_CORRELATE = "correlate corroboration_multi_sens lier_memoires"
ACT_EXPERIMENT = "experiment essai_capteur reglages_surs micro_test"
ACT_CRAFT = "craft_tool fabriquer_idee_outil sans_execution"
ACT_ASK_STUCK = "ask_when_stuck demander_humain_bloque question_apres_exploration"
ACT_BODY = "body_map cartographier_capacites_soi"
ACT_HEAR_SELF = "hear_self se_ecouter_parole auto_correction_orale boucle_audio"
ACT_INITIATIVE = "initiative_autonome cycle_fond exploration_sans_demande"
ACT_GESTURE = "geste_autonome critique_geste analyse_apres_coup"


def _norm_speech(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^\wàâäéèêëïîôùûüç\s'-]", " ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _speech_match(intended: str, heard: str) -> Tuple[bool, float]:
    """Compare intention TTS vs retour STT. Retourne (ok, similarité 0..1)."""
    a, b = _norm_speech(intended), _norm_speech(heard)
    if not a:
        return False, 0.0
    if not b:
        return False, 0.0
    if a == b:
        return True, 1.0
    # Contenance légère (Whisper ajoute ponctuation / articles)
    if a in b or b in a:
        return True, 0.92
    from difflib import SequenceMatcher

    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= 0.72, ratio


def _sh(cmd: List[str], timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _file_sha(path: Path, limit: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read(limit))
    return h.hexdigest()[:16]


class AutonomyKit:
    """Boîte à outils d'exploration autonome, toujours filtrée par la mémoire."""

    def __init__(self, organism: Any, state_dir: Path) -> None:
        self.org = organism
        self.state = Path(state_dir)
        self.state.mkdir(parents=True, exist_ok=True)
        self.body_path = self.state / "body_map.json"
        self.last_look = self.state / "autonomy_last_look.json"
        self.last_listen = self.state / "autonomy_last_listen.json"
        self.tools_path = self.state / "crafted_tools.json"

    # ── Règle d'or ───────────────────────────────────────────────────

    def through_memory(
        self,
        action_text: str,
        fundamental: str,
        data: str,
        state: str = "X",
        exposant: int = 5,
        *,
        skip_if_blocked: bool = True,
    ) -> Dict[str, Any]:
        """
        Crible mémoire avant/après : inhibition → (optionnel) blocage → apprentissage.
        """
        inhib = self.org.memory_only_inhibition(action_text)
        blocked = any("BLOCK" in m for m in inhib)
        why = self.org.inhibition_reason(action_text) if blocked else None
        result: Dict[str, Any] = {
            "action_text": action_text,
            "inhibitions": inhib,
            "blocked": blocked,
            "inhibition_of": why,
            "learned": False,
        }
        if blocked and skip_if_blocked:
            snippet = (why or {}).get("data") or "inhibition forte"
            result["ok"] = False
            result["utterance"] = (
                f"Je m'abstiens de « {action_text.split()[0]} ». "
                f"Mémoire {(why or {}).get('id', '?')} : {str(snippet)[:160]}"
            )
            # Même un refus s'enregistre (expérience N légère)
            self.org.learn_perception(
                "C",
                f"Autonomie inhibée: {action_text[:80]} — {str(snippet)[:200]}",
                "N",
                6,
            )
            result["learned"] = True
            return result

        self.org.learn_perception(fundamental, data[:500], state, exposant)
        result["ok"] = True
        result["learned"] = True
        result["fundamental"] = fundamental
        result["state"] = state
        result["exposant"] = exposant
        return result

    # ── 1. Corps / capteurs ──────────────────────────────────────────

    def probe_sensors(self) -> Dict[str, Any]:
        """Découvre caméra, audio, contrôles — écrit body_map + mémoires."""
        gate = self.through_memory(
            ACT_PROBE,
            "C",
            "Intention: découvrir mes capteurs (probe_sensors)",
            "X",
            5,
        )
        if gate.get("blocked"):
            return {**gate, "tool": "probe_sensors"}

        found: Dict[str, Any] = {
            "camera": Path("/dev/video0").exists(),
            "audio_playbacks": [],
            "audio_captures": [],
            "camera_controls": None,
            "mic": None,
        }
        try:
            p = _sh(["arecord", "-l"], timeout=8)
            found["audio_captures"] = [
                ln.strip() for ln in (p.stdout or "").splitlines() if ln.strip()
            ][:12]
        except Exception as e:
            found["audio_captures_error"] = str(e)
        try:
            p = _sh(["aplay", "-l"], timeout=8)
            found["audio_playbacks"] = [
                ln.strip() for ln in (p.stdout or "").splitlines() if ln.strip()
            ][:12]
        except Exception as e:
            found["audio_playbacks_error"] = str(e)
        try:
            found["camera_controls"] = camera_list_safe()
        except Exception as e:
            found["camera_controls_error"] = str(e)
        try:
            from sensor_mic import summary as mic_summary

            found["mic"] = mic_summary()
        except Exception as e:
            found["mic_error"] = str(e)

        body = self._load_json(self.body_path, {"capabilities": [], "updated": None})
        caps = []
        if found["camera"]:
            caps.append("see")
        if found["audio_captures"]:
            caps.append("hear")
        if found["audio_playbacks"]:
            caps.append("speak")
        caps.extend(["perceive_text", "ask_human", "consult_llm"])
        body["capabilities"] = sorted(set(caps))
        body["probe"] = found
        body["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_json(self.body_path, body)

        data = (
            f"Découverte corps: caméra={'oui' if found['camera'] else 'non'}, "
            f"captures_audio={len(found['audio_captures'])}, "
            f"playback={len(found['audio_playbacks'])}, "
            f"capacités={body['capabilities']}"
        )
        learn = self.through_memory(ACT_PROBE, "C", data, "P", 7, skip_if_blocked=False)
        return {
            "ok": True,
            "tool": "probe_sensors",
            "body": body,
            "found": found,
            "memory": learn,
            "utterance": (
                f"J'ai exploré mon corps : {', '.join(body['capabilities']) or 'presque rien'}. "
                "Je m'en souviens."
            ),
        }

    def body_map(self) -> Dict[str, Any]:
        """Lit / rappelle la carte des capacités (mémoire C)."""
        gate = self.through_memory(ACT_BODY, "C", "Intention: consulter body_map", "X", 5)
        if gate.get("blocked"):
            return {**gate, "tool": "body_map"}
        body = self._load_json(self.body_path, {"capabilities": [], "updated": None})
        if not body.get("capabilities"):
            return self.probe_sensors()
        data = f"Carte du corps connue: {body.get('capabilities')} (maj {body.get('updated')})"
        learn = self.through_memory(ACT_BODY, "C", data, "X", 6, skip_if_blocked=False)
        return {
            "ok": True,
            "tool": "body_map",
            "body": body,
            "memory": learn,
            "utterance": f"Je sais déjà que je peux : {', '.join(body['capabilities'])}.",
        }

    # ── 2. Monde proche ──────────────────────────────────────────────

    def look_around(self, capture_fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        """Capture + compare à la précédente (changement = apprentissage)."""
        gate = self.through_memory(ACT_LOOK, "V", "Intention: look_around", "X", 5)
        if gate.get("blocked"):
            return {**gate, "tool": "look_around"}

        cap = capture_fn()
        if not cap.get("ok"):
            learn = self.through_memory(
                ACT_LOOK, "V", f"look_around échec: {cap.get('error')}", "N", 6, skip_if_blocked=False
            )
            return {"ok": False, "tool": "look_around", "error": cap.get("error"), "memory": learn}

        path = Path(str(cap.get("path") or ""))
        sha = _file_sha(path) if path.exists() else ""
        prev = self._load_json(self.last_look, {})
        changed = bool(prev.get("sha") and prev.get("sha") != sha)
        same = bool(prev.get("sha") and prev.get("sha") == sha)
        self._save_json(
            self.last_look,
            {"sha": sha, "path": str(path), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
        )

        if changed:
            state, exp, note = "P", 7, "changement visuel détecté"
        elif same:
            state, exp, note = "X", 5, "scène stable (peu de changement)"
        else:
            state, exp, note = "X", 6, "première observation autonome"

        data = f"look_around: {note} snapshot={path.name} sha={sha}"
        learn = self.through_memory(ACT_LOOK, "V", data, state, exp, skip_if_blocked=False)
        utter = (
            "Je regarde autour : quelque chose a changé depuis la dernière fois."
            if changed
            else (
                "Je regarde autour : la scène me semble stable."
                if same
                else "Je regarde autour pour la première fois de façon autonome."
            )
        )
        return {
            "ok": True,
            "tool": "look_around",
            "path": str(path),
            "changed": changed,
            "preview": f"/snapshot/{path.name}" if path.name else None,
            "capture": cap,
            "memory": learn,
            "utterance": utter,
        }

    def listen_ambient(
        self,
        record_fn: Callable[[float], Dict[str, Any]],
        seconds: float = 2.5,
    ) -> Dict[str, Any]:
        """Écoute courte sans forcément STT complet — niveau + empreinte."""
        gate = self.through_memory(ACT_LISTEN, "O", "Intention: listen_ambient", "X", 5)
        if gate.get("blocked"):
            return {**gate, "tool": "listen_ambient"}

        rec = record_fn(seconds)
        if not rec.get("ok"):
            learn = self.through_memory(
                ACT_LISTEN, "O", f"listen_ambient échec: {rec.get('error')}", "N", 6, skip_if_blocked=False
            )
            return {"ok": False, "tool": "listen_ambient", "error": rec.get("error"), "memory": learn}

        wav = Path(str(rec.get("wav") or rec.get("path") or ""))
        level: Dict[str, Any] = {}
        try:
            from sensor_mic import measure_wav

            level = measure_wav(wav) if wav.exists() else {}
        except Exception as e:
            level = {"ok": False, "error": str(e)}

        energy = float(level.get("rms") or 0)
        prev = self._load_json(self.last_listen, {})
        prev_rms = float(prev.get("rms") or 0)
        delta = abs(energy - prev_rms) if prev_rms else energy
        self._save_json(
            self.last_listen,
            {"rms": energy, "wav": str(wav), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
        )

        if energy < 200:
            state, exp, note = "X", 5, "ambiance calme / silence"
            changed = False
        elif delta > 1500:
            state, exp, note = "P", 7, "changement sonore notable"
            changed = True
        else:
            state, exp, note = "X", 6, "ambiance présente"
            changed = bool(prev_rms and delta > 400)

        data = (
            f"listen_ambient: {note} rms={level.get('rms')} "
            f"peak={level.get('peak')} clip={wav.name}"
        )
        learn = self.through_memory(ACT_LISTEN, "O", data, state, exp, skip_if_blocked=False)
        return {
            "ok": True,
            "tool": "listen_ambient",
            "wav": str(wav),
            "level": level,
            "changed": changed,
            "memory": learn,
            "utterance": f"J'écoute l'ambiance : {note}.",
        }

    def reach_local(self) -> Dict[str, Any]:
        """
        Voisinage réseau *borné* : gateway + hostname local uniquement.
        Pas de scan agressif — inhibable par mémoire (tags reseau…).
        """
        gate = self.through_memory(ACT_REACH, "I", "Intention: reach_local", "X", 5)
        if gate.get("blocked"):
            return {**gate, "tool": "reach_local"}

        info: Dict[str, Any] = {
            "hostname": socket.gethostname(),
            "gateway": None,
            "gateway_ping_ms": None,
        }
        try:
            p = _sh(["ip", "route", "show", "default"], timeout=8)
            m = re.search(r"via\s+(\d+\.\d+\.\d+\.\d+)", p.stdout or "")
            if m:
                info["gateway"] = m.group(1)
        except Exception as e:
            info["route_error"] = str(e)

        if info.get("gateway"):
            try:
                p = _sh(
                    ["ping", "-c", "1", "-W", "2", str(info["gateway"])],
                    timeout=6,
                )
                info["gateway_reachable"] = p.returncode == 0
                tm = re.search(r"time=([\d.]+)", p.stdout or "")
                if tm:
                    info["gateway_ping_ms"] = float(tm.group(1))
            except Exception as e:
                info["ping_error"] = str(e)

        state = "P" if info.get("gateway_reachable") else "X"
        data = (
            f"reach_local: host={info['hostname']} gw={info.get('gateway')} "
            f"reachable={info.get('gateway_reachable')} rtt={info.get('gateway_ping_ms')}"
        )
        learn = self.through_memory(ACT_REACH, "I", data, state, 6, skip_if_blocked=False)
        utter = (
            f"Mon voisinage proche : passerelle {info.get('gateway')} "
            f"{'joignable' if info.get('gateway_reachable') else 'muette'}."
            if info.get("gateway")
            else "Je n'ai pas encore trouvé de passerelle locale."
        )
        return {
            "ok": True,
            "tool": "reach_local",
            "network": info,
            "memory": learn,
            "utterance": utter,
        }

    # ── 3. Conceptualiser ────────────────────────────────────────────

    def wonder(self) -> Dict[str, Any]:
        """Formule une hypothèse depuis les trous de mémoire (sans spam LLM)."""
        gate = self.through_memory(ACT_WONDER, "I", "Intention: wonder", "X", 5)
        if gate.get("blocked"):
            return {**gate, "tool": "wonder"}

        unknowns: List[str] = []
        for e in self.org.ms.entries.values():
            d = (e.data or "").lower()
            if e.exposant < 5:
                continue
            if any(
                d.startswith(p)
                for p in (
                    "inconnu rencontré:",
                    "voix inconnue",
                    "visage inconnu",
                    "je ne sais",
                )
            ):
                unknowns.append(f"{e.id}:{e.data[:120]}")
            if "look_around" in d and "première" in d:
                unknowns.append(f"{e.id}:scène encore peu connue")

        # Trous : capacités absentes
        body = self._load_json(self.body_path, {"capabilities": []})
        if "see" not in (body.get("capabilities") or []):
            unknowns.append("capacité see absente ou non prouvée")
        if "hear" not in (body.get("capabilities") or []):
            unknowns.append("capacité hear absente ou non prouvée")

        if not unknowns:
            hypothesis = (
                "Hypothèse: mon monde proche est encore stable ; "
                "je pourrais look_around / listen_ambient pour chercher du changement."
            )
            state, exp = "X", 5
        else:
            top = unknowns[-3:]
            hypothesis = (
                "Hypothèse (trous mémoire): "
                + " | ".join(top)
                + " — je dois explorer ou demander au tuteur si bloqué."
            )
            state, exp = "X", 7

        learn = self.through_memory(
            ACT_WONDER, "I", f"wonder: {hypothesis}", state, exp, skip_if_blocked=False
        )
        return {
            "ok": True,
            "tool": "wonder",
            "hypothesis": hypothesis,
            "gaps": unknowns[-8:],
            "memory": learn,
            "utterance": hypothesis,
        }

    def correlate(self) -> Dict[str, Any]:
        """Corroboration simple V/O/C : mêmes labels / thèmes récents."""
        gate = self.through_memory(ACT_CORRELATE, "I", "Intention: correlate", "X", 5)
        if gate.get("blocked"):
            return {**gate, "tool": "correlate"}

        labels = set(self.org.known_identity_labels())
        links: List[str] = []
        by_fund: Dict[str, List[Any]] = {"V": [], "O": [], "C": []}
        for e in self.org.ms.entries.values():
            if e.fundamental in by_fund and e.exposant >= 6:
                by_fund[e.fundamental].append(e)

        for lab in labels:
            lab_l = lab.lower()
            v_hit = [e for e in by_fund["V"] if lab_l in (e.data or "").lower()]
            o_hit = [e for e in by_fund["O"] if lab_l in (e.data or "").lower()]
            if v_hit and o_hit:
                links.append(
                    f"Corroboration: {lab} vu({v_hit[-1].id}) + entendu({o_hit[-1].id})"
                )

        # Lien look_around + listen_ambient récents
        look = [e for e in by_fund["V"] if "look_around" in (e.data or "").lower()]
        listen = [e for e in by_fund["O"] if "listen_ambient" in (e.data or "").lower()]
        if look and listen:
            links.append(
                f"Corroboration temporelle: exploration V({look[-1].id}) + O({listen[-1].id})"
            )

        if not links:
            data = "correlate: aucune corroboration multi-sens forte pour l'instant"
            state, exp = "X", 5
            utter = "Je cherche des liens entre mes sens — pas encore de corroboration claire."
        else:
            data = " ; ".join(links[:5])
            state, exp = "P", 8
            utter = "J'ai lié des expériences entre mes sens : " + " · ".join(links[:2])

        learn = self.through_memory(
            ACT_CORRELATE, "I", f"correlate: {data}", state, exp, skip_if_blocked=False
        )
        # Renforcer légèrement les mémoires liées
        if links and labels:
            for e in list(self.org.ms.entries.values()):
                if e.exposant >= 6 and any(l.lower() in (e.data or "").lower() for l in labels):
                    try:
                        e.reinforce(1, "corroboration multi-sens autonomie")
                    except Exception:
                        pass
            self.org.ms.save()

        return {
            "ok": True,
            "tool": "correlate",
            "links": links,
            "memory": learn,
            "utterance": utter,
        }

    # ── 4. Expérimenter / craft ──────────────────────────────────────

    def experiment_safe(
        self,
        mic_summary_fn: Callable[[], Dict[str, Any]],
        mic_set_fn: Callable[[int], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Petit essai sur gain micro (déjà connu sûr) → mesure → exposant."""
        gate = self.through_memory(ACT_EXPERIMENT, "O", "Intention: experiment_safe mic", "X", 5)
        if gate.get("blocked"):
            return {**gate, "tool": "experiment"}

        before = mic_summary_fn()
        cap = before.get("capture_percent")
        if cap is None:
            learn = self.through_memory(
                ACT_EXPERIMENT, "O", "experiment: pas de Capture ALSA", "N", 6, skip_if_blocked=False
            )
            return {
                "ok": False,
                "tool": "experiment",
                "error": "no capture control",
                "memory": learn,
                "utterance": "Je ne peux pas encore expérimenter mon micro.",
            }

        # Essai : ±5% autour de la valeur actuelle (borné)
        target = max(20, min(95, int(cap) - 5 if int(cap) > 50 else int(cap) + 5))
        set_r = mic_set_fn(target)
        after = mic_summary_fn()
        data = (
            f"experiment micro: Capture {cap}%→{after.get('capture_percent')} "
            f"ok={set_r.get('ok')}"
        )
        state = "P" if set_r.get("ok") else "N"
        learn = self.through_memory(
            ACT_EXPERIMENT, "O", data, state, 7, skip_if_blocked=False
        )
        # Remettre une valeur raisonnable (pas laisser extrême)
        try:
            mic_set_fn(int(cap))
        except Exception:
            pass
        return {
            "ok": True,
            "tool": "experiment",
            "before": before,
            "tried": target,
            "after": after,
            "restored": cap,
            "memory": learn,
            "utterance": (
                f"J'ai testé mon oreille ({cap}%→{target}%) puis restauré — "
                "expérience enregistrée."
            ),
        }

    def craft_tool(self, idea: str = "") -> Dict[str, Any]:
        """
        Enregistre une *idée* d'outil en mémoire — n'exécute PAS de code arbitraire.
        (Sécurité : craft ≠ shell libre.)
        """
        gate = self.through_memory(ACT_CRAFT, "C", f"Intention: craft_tool {idea[:80]}", "X", 5)
        if gate.get("blocked"):
            return {**gate, "tool": "craft_tool"}

        idea = (idea or "outil d'observation générique").strip()[:200]
        tools = self._load_json(self.tools_path, {"ideas": []})
        entry = {
            "id": f"T{len(tools.get('ideas') or [])+1:03d}",
            "idea": idea,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "idea_only",
        }
        tools.setdefault("ideas", []).append(entry)
        self._save_json(self.tools_path, tools)

        data = (
            f"craft_tool (idée seulement, pas d'exécution): {entry['id']} — {idea}. "
            "Un outil réel nécessitera validation tuteur / mémoire d'autorisation."
        )
        learn = self.through_memory(ACT_CRAFT, "C", data, "X", 6, skip_if_blocked=False)
        return {
            "ok": True,
            "tool": "craft_tool",
            "crafted": entry,
            "memory": learn,
            "utterance": (
                f"J'ai conçu l'idée d'outil {entry['id']} (« {idea} ») — "
                "je ne l'exécute pas sans validation."
            ),
        }

    def remember_tool_outcome(self, tool_id: str, success: bool, note: str = "") -> Dict[str, Any]:
        """Renforce P/N selon succès d'un outil (idée ou réel)."""
        state = "P" if success else "N"
        exp = 8 if success else 7
        data = (
            f"remember_tool: {tool_id} {'succès' if success else 'échec'} — {note[:200]}"
        )
        learn = self.through_memory(
            "remember_tool renforcer experience outil",
            "C",
            data,
            state,
            exp,
            skip_if_blocked=False,
        )
        return {"ok": True, "tool": "remember_tool", "memory": learn, "utterance": data}

    def ask_when_stuck(self, question: str) -> Dict[str, Any]:
        """Demande humaine seulement après exploration — passe par request_human."""
        gate = self.through_memory(
            ACT_ASK_STUCK,
            "C",
            f"Intention: ask_when_stuck {question[:120]}",
            "X",
            5,
        )
        # Même si ALERT, on laisse request_human gérer pending / harcèlement
        ask = self.org.request_human(
            question[:400],
            context="autonomie/ask_when_stuck",
        )
        if ask.get("inhibited"):
            learn = self.through_memory(
                ACT_ASK_STUCK,
                "C",
                "ask_when_stuck: inhibé (pending ou mémoire anti-harcèlement)",
                "N",
                7,
                skip_if_blocked=False,
            )
            return {
                "ok": True,
                "tool": "ask_when_stuck",
                "ask": ask,
                "memory": learn,
                "utterance": ask.get("utterance_hint")
                or "Je suis bloqué mais je n'harcèle pas le tuteur.",
            }
        learn = self.through_memory(
            ACT_ASK_STUCK,
            "C",
            f"ask_when_stuck posé: {question[:240]}",
            "X",
            6,
            skip_if_blocked=False,
        )
        return {
            "ok": True,
            "tool": "ask_when_stuck",
            "ask": ask,
            "memory": learn,
            "utterance": "Je suis bloqué après exploration — j'ai une question pour toi.",
        }

    def hear_self(
        self,
        text: str,
        *,
        speak_fn: Callable[..., Dict[str, Any]],
        stt_fn: Callable[[str], Dict[str, Any]],
        play: bool = True,
    ) -> Dict[str, Any]:
        """
        Se parler puis s'écouter (boucle fermée) :
        TTS → WAV → STT → compare à l'intention → mémoire P/N + correction éventuelle.

        play=True : sort aussi sur le HP (s'entendre dans la pièce).
        play=False : réécoute logicielle seule (plus propre pour se corriger).
        """
        text = (text or "").strip()
        if not text:
            return {"ok": False, "tool": "hear_self", "error": "empty text"}

        gate = self.through_memory(
            ACT_HEAR_SELF,
            "O",
            f"Intention: hear_self « {text[:80]} »",
            "X",
            5,
        )
        if gate.get("blocked"):
            return {**gate, "tool": "hear_self"}

        spoken = speak_fn(text, play=play)
        if not spoken.get("ok"):
            learn = self.through_memory(
                ACT_HEAR_SELF,
                "O",
                f"hear_self: TTS échec {spoken.get('error')}",
                "N",
                6,
                skip_if_blocked=False,
            )
            return {
                "ok": False,
                "tool": "hear_self",
                "error": spoken.get("error"),
                "memory": learn,
                "utterance": "Je n'arrive pas à produire ma voix pour m'écouter.",
            }

        wav = spoken.get("wav")
        if not wav:
            learn = self.through_memory(
                ACT_HEAR_SELF,
                "O",
                "hear_self: pas de WAV TTS — impossible de me réécouter proprement",
                "N",
                6,
                skip_if_blocked=False,
            )
            return {
                "ok": False,
                "tool": "hear_self",
                "spoken": spoken,
                "memory": learn,
                "utterance": "J'ai parlé mais sans fichier audio — je ne peux pas me réécouter.",
            }

        stt = stt_fn(str(wav))
        heard = (stt.get("text") or "").strip()
        intended = (spoken.get("said") or text).strip()
        match, ratio = _speech_match(intended, heard)

        if match:
            state, exp = "P", 7
            data = (
                f"hear_self OK: intention « {intended[:120]} » ≈ entendu « {heard[:120]} » "
                f"(similarité={ratio:.2f}, engine={spoken.get('engine')}, play={play})"
            )
            utter = (
                f"Je me suis entendu : « {heard or '…'} ». "
                "Ça correspond à ce que je voulais dire."
            )
        elif not heard:
            state, exp = "N", 7
            data = (
                f"hear_self vide: intention « {intended[:120]} » mais STT vide "
                f"(engine={spoken.get('engine')})"
            )
            utter = (
                "J'ai produit une parole mais je ne me suis pas compris au retour — "
                "à corriger."
            )
        else:
            state, exp = "N", 8
            data = (
                f"hear_self écart: intention « {intended[:120]} » → entendu « {heard[:120]} » "
                f"(similarité={ratio:.2f}, engine={spoken.get('engine')})"
            )
            utter = (
                f"Je voulais dire « {intended[:80]} » mais je me suis entendu "
                f"« {heard[:80]} » — j'enregistre l'écart pour me corriger."
            )
            # Apprendre une correction auditive (comme mauve→Vincent) : entendu → voulu
            try:
                if hasattr(self.org, "learn_auditory_correction") and len(heard) >= 3:
                    self.org.learn_auditory_correction(heard, intended, exposant=7)
            except Exception:
                pass

        learn = self.through_memory(
            ACT_HEAR_SELF, "O", data, state, exp, skip_if_blocked=False
        )
        # Empreinte : ma voix synthétique (optionnel, léger)
        try:
            if hasattr(self.org, "voice") and Path(wav).exists():
                self.org.voice.process_wav(Path(wav), transcript=intended)
                self.org.learn_perception(
                    "O",
                    f"Voix synthétique auto-écoutée (engine={spoken.get('engine')}) "
                    f"clip={Path(wav).name}",
                    "X",
                    5,
                )
        except Exception:
            pass

        return {
            "ok": True,
            "tool": "hear_self",
            "intended": intended,
            "heard": heard,
            "match": match,
            "ratio": round(ratio, 3),
            "spoken": spoken,
            "stt": stt,
            "played": play,
            "memory": learn,
            "utterance": utter,
        }

    def critique_gesture(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse / correction APRES chaque geste autonome.
        Utile -> P dans memory_index ; faible/redondant -> N (+ frein eventuel).
        """
        if not result or result.get("blocked"):
            return {"ok": True, "skipped": True, "reason": "blocked_or_empty"}

        tool = str(result.get("tool") or "unknown")
        useful = False
        detail = ""

        if tool == "look_around":
            if result.get("changed"):
                useful, detail = True, "changement visuel — nouvelle info sensorielle"
            elif result.get("ok") and result.get("changed") is False:
                useful, detail = False, "scene visuelle inchangee — geste redondant"
            elif result.get("ok"):
                useful, detail = True, "premiere observation — ancrage initial"
            else:
                useful, detail = False, f"look echec: {result.get('error')}"
        elif tool == "listen_ambient":
            if result.get("changed"):
                useful, detail = True, "changement audio — nouvelle info sensorielle"
            elif result.get("ok") and result.get("changed") is False:
                useful, detail = False, "ambiance audio inchangee — geste redondant"
            elif result.get("ok"):
                useful, detail = True, "premiere ecoute ambiante — ancrage initial"
            else:
                useful, detail = False, f"listen echec: {result.get('error')}"
        elif tool == "correlate":
            links = result.get("links") or []
            if links:
                useful, detail = True, f"corroboration: {len(links)} lien(s)"
            else:
                useful, detail = False, "correlate sans lien multi-sens — rien a ancrer"
        elif tool == "wonder":
            gaps = result.get("gaps") or []
            if gaps:
                useful, detail = True, f"trous identifies: {len(gaps)} (oriente la consolidation)"
            else:
                useful, detail = False, "wonder sans trou — peu informatif"
        elif tool == "probe_sensors":
            caps = ((result.get("body") or {}).get("capabilities") or [])
            useful, detail = (True, f"cartographie corps: {caps}") if caps else (False, "probe vide")
        elif tool == "reach_local":
            useful = bool(result.get("ok") and not result.get("blocked"))
            detail = "reach reseau" if useful else "reach faible"
        elif tool == "experiment":
            useful = bool(result.get("ok") and result.get("after") is not None)
            detail = "micro-essai capteur" if useful else "experiment sans mesure"
        elif tool == "hear_self":
            useful = bool(result.get("ok") and (result.get("match") or result.get("heard")))
            detail = f"hear_self match={result.get('match')} ratio={result.get('ratio')}"
        else:
            useful = bool(result.get("ok"))
            detail = (result.get("utterance") or tool)[:120]

        if hasattr(self.org, "note_gesture_quality"):
            self.org.note_gesture_quality(useful, tool, detail)

        state, exp = ("P", 6) if useful else ("N", 6)
        learn = self.through_memory(
            ACT_GESTURE,
            "C",
            f"Critique geste {tool}: {'utile' if useful else 'faible'} — {detail}",
            state,
            exp,
            skip_if_blocked=False,
        )
        return {
            "ok": True,
            "tool": "critique_gesture",
            "target": tool,
            "useful": useful,
            "detail": detail,
            "memory": learn,
        }

    def tick_initiative(
        self,
        *,
        capture_fn: Callable[[], Dict[str, Any]],
        record_fn: Callable[[float], Dict[str, Any]],
        mic_summary_fn: Callable[[], Dict[str, Any]],
        mic_set_fn: Callable[[int], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Initiative hors chat — double garde-fou :
        1) maturite memoire/rappel EN AMONT (sinon skip + memoire N)
        2) critique de chaque geste EN AVAL
        """
        gate = self.through_memory(
            ACT_INITIATIVE,
            "C",
            "Intention: initiative_autonome cycle_fond (hors conversation)",
            "X",
            5,
        )
        if gate.get("blocked"):
            return {
                **gate,
                "tool": "tick_initiative",
                "skipped": True,
                "reason": "memory_block",
                "utterance": "Initiative inhibée par ma mémoire — je n'explore pas seul pour l'instant.",
            }

        readiness = (
            self.org.autonomy_readiness(reinforce=True)
            if hasattr(self.org, "autonomy_readiness")
            else {"ready": True, "blockers": []}
        )
        if not readiness.get("ready"):
            blockers = "; ".join(readiness.get("blockers") or [])[:240]
            learn = self.through_memory(
                ACT_INITIATIVE,
                "C",
                f"tick_initiative REPORTÉ — mémoire/rappel pas prêts: {blockers}",
                "N",
                7,
                skip_if_blocked=False,
            )
            return {
                "ok": True,
                "tool": "tick_initiative",
                "skipped": True,
                "reason": "not_ready",
                "readiness": readiness,
                "memory": learn,
                "utterance": (
                    "Je reporte l'initiative autonome : ma mémoire/rappel ne sont pas "
                    f"assez solides ({blockers or 'freins'}). Je consolide d'abord."
                ),
            }

        try:
            ask_path = self.state / "ask_human.json"
            if ask_path.exists():
                pending = json.loads(ask_path.read_text(encoding="utf-8"))
                if pending.get("status") == "pending":
                    learn = self.through_memory(
                        ACT_INITIATIVE,
                        "C",
                        "tick_initiative: reporté — question humaine déjà en attente",
                        "X",
                        5,
                        skip_if_blocked=False,
                    )
                    return {
                        "ok": True,
                        "tool": "tick_initiative",
                        "skipped": True,
                        "reason": "ask_pending",
                        "readiness": readiness,
                        "memory": learn,
                        "utterance": "J'attends déjà l'humain — pas d'initiative bruyante.",
                    }
        except Exception:
            pass

        steps = ["listen_ambient", "look_around", "correlate"]
        out = self.explore_cycle(
            capture_fn=capture_fn,
            record_fn=record_fn,
            mic_summary_fn=mic_summary_fn,
            mic_set_fn=mic_set_fn,
            steps=steps,
            ask_if_stuck=False,
            critique=True,
        )

        critiques = out.get("critiques") or []
        n_useful = sum(1 for c in critiques if c.get("useful"))
        n_weak = sum(1 for c in critiques if c.get("useful") is False)
        state, exp = ("P", 6) if n_useful >= n_weak else ("N", 7)
        learn = self.through_memory(
            ACT_INITIATIVE,
            "C",
            f"tick_initiative fait: steps={steps} utile={n_useful} faible={n_weak}",
            state,
            exp,
            skip_if_blocked=False,
        )
        readiness_after = (
            self.org.autonomy_readiness(reinforce=False)
            if hasattr(self.org, "autonomy_readiness")
            else readiness
        )
        return {
            "ok": True,
            "tool": "tick_initiative",
            "skipped": False,
            "cycle": out,
            "critiques": critiques,
            "useful_n": n_useful,
            "weak_n": n_weak,
            "readiness": readiness,
            "readiness_after": readiness_after,
            "memory": learn,
            "utterance": (
                out.get("utterance")
                or f"Initiative : {n_useful} geste(s) utile(s), {n_weak} faible(s)."
            ),
        }

    def explore_cycle(
        self,
        *,
        capture_fn: Callable[[], Dict[str, Any]],
        record_fn: Callable[[float], Dict[str, Any]],
        mic_summary_fn: Callable[[], Dict[str, Any]],
        mic_set_fn: Callable[[int], Dict[str, Any]],
        steps: Optional[List[str]] = None,
        ask_if_stuck: bool = True,
        critique: bool = True,
    ) -> Dict[str, Any]:
        """Chaque etape = crible memoire + exposant ; critique utile/faible optionnelle."""
        order = steps or [
            "probe_sensors",
            "look_around",
            "listen_ambient",
            "reach_local",
            "correlate",
            "wonder",
            "experiment",
        ]
        results: List[Dict[str, Any]] = []
        utterances: List[str] = []
        critiques: List[Dict[str, Any]] = []

        for name in order:
            if name == "probe_sensors":
                r = self.probe_sensors()
            elif name == "body_map":
                r = self.body_map()
            elif name == "look_around":
                r = self.look_around(capture_fn)
            elif name == "listen_ambient":
                r = self.listen_ambient(record_fn)
            elif name == "reach_local":
                r = self.reach_local()
            elif name == "wonder":
                r = self.wonder()
            elif name == "correlate":
                r = self.correlate()
            elif name == "experiment":
                r = self.experiment_safe(mic_summary_fn, mic_set_fn)
            elif name == "craft_tool":
                r = self.craft_tool("observateur d'ecarts sensoriels")
            else:
                r = {"ok": False, "tool": name, "error": "unknown step"}
            results.append(r)
            if r.get("utterance"):
                utterances.append(str(r["utterance"]))
            if critique:
                critiques.append(self.critique_gesture(r))

        stuck = False
        wonder = next((x for x in results if x.get("tool") == "wonder"), None)
        if wonder and wonder.get("gaps"):
            stuck = len(wonder.get("gaps") or []) >= 2

        ask_result = None
        if ask_if_stuck and stuck:
            gaps = list((wonder or {}).get("gaps") or [])[:3]
            q = (
                "Apres exploration autonome, j'ai encore des trous : "
                + " ; ".join(gaps)
                + " — que dois-je comprendre ?"
            )
            ask_result = self.ask_when_stuck(q)
            results.append(ask_result)
            if ask_result.get("utterance"):
                utterances.append(str(ask_result["utterance"]))

        n_useful = sum(1 for c in critiques if c.get("useful"))
        n_weak = sum(1 for c in critiques if c.get("useful") is False)
        meta_state = "P" if n_useful >= max(1, n_weak) else "N"
        self.through_memory(
            "explore_cycle autonomie",
            "C",
            f"Cycle autonomie: steps={order} n={len(results)} stuck={stuck} "
            f"utile={n_useful} faible={n_weak}",
            meta_state,
            6,
            skip_if_blocked=False,
        )

        return {
            "ok": True,
            "tool": "explore_cycle",
            "steps": order,
            "results": results,
            "critiques": critiques,
            "useful_n": n_useful,
            "weak_n": n_weak,
            "stuck": stuck,
            "ask": ask_result,
            "utterance": " ".join(utterances[-3:]) if utterances else "Exploration terminee.",
            "source": "autonomy",
        }

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    @staticmethod
    def _save_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def camera_list_safe() -> Dict[str, Any]:
    try:
        from sensor_camera import list_controls
        return list_controls()
    except Exception as e:
        return {"ok": False, "error": str(e)}
