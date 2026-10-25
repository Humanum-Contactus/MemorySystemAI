# Evolution October 2026 — `memory-node` prototype

> **[FR (source) →](../EVOLUTION_MEMORY_NODE_2026-10.md)** · EN · [`LANGUES.md`](../LANGUES.md)  
> ← **Previous:** [Period 21.07 – 24.10.2026 (project paused)](EVOLUTION_MEMORY_NODE_2026-07-10.md) ·
> **Next:** *(none yet)* · [Docs index](README.md) · [CHANGELOG](../../CHANGELOG.en.md)

**Concept author:** Vincent Vermeille (Humanum-Contactus)  
**Prototype implementation:** agent session (LAN control host → node)  
**Status:** contradiction detection, autonomy and voice fixes deployed on the node and carried into this repository  
**Code:** [`prototypes/memory-node/`](../../prototypes/memory-node/)  
**French is authoritative.** Shell commands and the French sentences sent to the node are kept as they are.

This document **picks up exactly where** the
[July 2026 chronicle](EVOLUTION_MEMORY_NODE_2026-07.md) ends (phase I), traces the
repository history between the two chronicles (phases J–L, from `git log`), then
tells the October work (phases M–W): how the node learned **not to decide on its
own** when it is taught two incompatible versions of a fact.

Related documents:

- [`changements/2026-10-25_detection-contradictions.md`](changements/2026-10-25_detection-contradictions.md) — change record (phases M–Q)  
- [`changements/2026-10-25_autonomie-contradiction-ids.md`](changements/2026-10-25_autonomie-contradiction-ids.md) — record (phases S–V)  
- [`changements/2026-10-25_voix-half-duplex.md`](changements/2026-10-25_voix-half-duplex.md) — record (phase W)  
- [`TEST_PROTOCOL_CONTRADICTIONS.md`](TEST_PROTOCOL_CONTRADICTIONS.md) — generic test protocol (phases Q–R)  
- [`../../prototypes/memory-node/tests/README.en.md`](../../prototypes/memory-node/tests/README.en.md) — automated tests  
- [`INSTALLATION.md`](INSTALLATION.md) — install and test  
- [`../../CHANGELOG.en.md`](../../CHANGELOG.en.md) — version history  
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md#continuing-the-journal) — how to continue this journal  

---

## 0. One-sentence summary

After **autonomy** arrived in July (exploration tools, background loop, living
norms), October brings **resistance to contradictions**: repeating a lie no longer
makes it true, recall refuses to choose, and the human is asked **only once** —
without touching the foundations of the concept.

---

## 1. Starting point — where the July chronicle ends

The July chronicle ends with **phase I — Memories = norms (not `.py` tables)**:
`ask` anti-harassment as a C/N/e9 memory, STT corrections as O memories,
inhibition only through **tags** + exposant, OpenClaw bridge accepted as a relay.

Its last described state (§ 6 "Next"):

| Item | State end of July | What it becomes here |
|------|-------------------|----------------------|
| Fundamental & State | fragile heuristic | unchanged |
| Semantic similarity | word overlap | unchanged (on purpose: § 4) |
| Multi-sense corroboration | partial | living norm + `answer_from_corroboration` (phase L) |
| Less LLM / OpenClaw dependency | still strong | memory screen before the LLM (phase L) |
| More "childlike" learning | basic | unchanged |
| More active mode | still passive | autonomy tools + background loop (phases K–L) |
| Inhibition of machine actions (SSH/sudo) | not wired | unchanged |

Last change to the July chronicle in git: commit `2cbf065`
(21.07.2026 12:20, documentation made bilingual).

---

## 2. Timeline of the work

### Between the two chronicles — from `git log` (21.07.2026)

Source: repository history (`git log 2cbf065..e586d78`, diffs reread). Nothing is
added beyond what the commits and their diffs show.

### Phase J — Documentation: whitepaper first, bilingualism

| Commit | Date (Zurich) | Content |
|--------|---------------|---------|
| `de84c9f` | 21.07 12:20 | Bilingual banner + EN summary in `SENSORS_AND_MEMORY_SYSTEM_AI.md` |
| `7084cdb` | 21.07 12:44 | README, `CONTRIBUTING.md`, `LANGUES.md`, docs index: the **whitepaper** becomes the foundation; the prototype is presented as an embodied sketch derived from it |

- **Files touched**: those of the commits above. **Commands**: not recorded
  (only the git history exists). **Result**: visible in the diffs.
  **Rollback**: `git revert de84c9f 7084cdb`

### Phase K — Autonomy toolbox (`autonomy.py`)

| Commit | Date (Zurich) | Content |
|--------|---------------|---------|
| `fa25480` | 21.07 14:13 | New `autonomy.py` (+763), `organism.py` (+120 / −4): `probe_sensors`, `body_map`, `look_around`, `listen_ambient`, `reach_local`, `wonder`, `correlate`, `experiment_safe`, `craft_tool`, `ask_when_stuck`, `explore_cycle`; every tool goes through `through_memory` (inhibition by tags → execution → recording). `POST /explore`, `POST /autonomy`, "Explorer" button in the nursery |
| `74002c1` | 21.07 14:18 | `/explore` and `/autonomy` routes documented in [`ARCHITECTURE_MEMORY_NODE.md`](ARCHITECTURE_MEMORY_NODE.md) |

Principle kept: this is **not** "LLM curiosity"; these are sensory / meta tools
that feed `memory_index`.

- **Files touched**: `prototypes/memory-node/autonomy.py`, `organism.py`, `ui/index.html`,
  `docs/ARCHITECTURE_MEMORY_NODE.md`. **Commands**: not recorded (git history
  only). **Rollback**: `git revert 74002c1 fa25480`

### Phase L — Hardened autonomy: living norms, source balance, initiative

Commit `e586d78` (21.07 15:07) — `organism.py` (+874 / −54), `autonomy.py`
(+404 / −24), `ui/index.html` (+36 / −1):

| Building block | Content (from the diff) |
|----------------|-------------------------|
| Living norms | `LIVING_NORMS` / `ensure_living_norms`: 4 tagged e7 memories — memory first, corroboration, initiative, consolidate before autonomy |
| Source balance | live counters in `memory_index` (`note_answer_source`, `source_bilan_from_memory`) instead of a stats file |
| Screen before the LLM | `llm_consultation_gate`: BLOCK/ALERT from memory before the LLM tool |
| Corroboration | `answer_from_corroboration` (sight + hearing / face + voice) |
| Maturity | `autonomy_readiness`: maturity verdict written to memory before any initiative outside the UI |
| Gestures | `critique_gesture`, `note_gesture_quality` (useful / weak counters) |
| Hearing itself | `hear_self`: compares what is said with what is heard ("S’écouter" button) |
| Background loop | `start_autonomy_loop` / `tick_initiative` (variables `AUTONOMY_LOOP`, `AUTONOMY_INTERVAL`), always screened by `ACT_INITIATIVE` |

Commit message: norms and inhibitions stay living memories with exposants;
session logs stay private (`.gitignore`).

> This **background loop** is what writes an "Autonomie inhibée: …" memory
> (`autonomy.py`) every time an action is blocked — the origin of the finding in
> **phase S**.

- **Commands**: not recorded (git history only). **Rollback**:
  `git revert e586d78`

### Undocumented period — 21.07.2026 15:07 → 24.10.2026

No commit and no published chronicle for this period. The private session log is
not versioned. The only findings made on 25.10 on the node:

- the running code was **identical to `e586d78`** (except for line endings);
- the index held **about 1034 memories**;
- deployment is **flat** (no git clone on the node).

What happened on the node in between (use, teaching) **is not documented**.

---

### October 2026 work

### How to read each phase

Each phase follows the same plan: **what we were looking for** (hypothesis),
**what we tried**, **what we observed**, **what we take from it** (lesson), then
**files touched**, **commands executed** and **rollback**. Commands come from the
session log; private data is replaced by markers (`<UTILISATEUR>`, `<IP_DU_NOEUD>`,
`<IP_FILAIRE_DU_NOEUD>`). When the log does not give the command word for word,
this is written as the comment `# commande exacte non consignée` ("exact command
not recorded"): nothing is reconstructed.

### Phase M — Analysis and proposal (box, read-only; 25.10.2026 01:13–01:34)

- **Looking for**: whether the node can be convinced by a repeated lie, and why.
- **Tried**: reading the path `/perceive` → `cycle_text` → `interpret_with_tools`,
  then a minimal proposal (pure module `fact_conflict.py`, hook in `organism.py`,
  off-server script `dedup_taught_facts.py`), tried on a **copy** of the
  repository with the "Vornex" protocol.
- **Observed**: every sentence "X est Y" became a C/P/e8 `Fait enseigné`, with no
  merge and no detection; recall decided **by number of copies**. With the patch,
  on the copy: **97 checks OK, 0 failure**. The demo harness assumed an existing
  folder (harness defect, not a patch defect).
- **Lesson**: repetition must not make something true; we add without touching the
  foundations, and we always test on a copy first.
- **Files touched**: none on the node; throwaway copy on the box.
- **Commands**:

```bash
cp -a /workspace/MemorySystemAI /tmp/msai
cd /tmp/msai
patch -p1 --dry-run < proposition.patch   # redirection exacte non consignée ; « dry-run OK »
patch -p1 < proposition.patch             # idem ; « appliqué proprement »
python3 -m py_compile prototypes/memory-node/organism.py \
  prototypes/memory-node/fact_conflict.py prototypes/memory-node/dedup_taught_facts.py
# commande exacte non consignée : lancement du script de démonstration (97 contrôles)
```

- **Rollback**: `rm -rf /tmp/msai /tmp/prop /tmp/vornex-apply`

### Phase N — Access to the node (01:38–01:45)

- **Looking for**: checking that the deployed code is the repository's before patching it.
- **Tried**: connection over the wired interface, then over the wifi interface
  after checking that the **host key fingerprint** matched the one already known;
  `patch --dry-run` on a copy of the deployed files.
- **Observed**: wired interface **unreachable** (timeout, missing from the ARP
  table). The node is not a git clone: `organism.py` is "flat" with **CRLF** line
  endings. Content identical to the repository once the `\r` are removed, but the
  dry-run fails on **5 hunks out of 5** ("different line endings") → stop, nothing
  changed. Option chosen: prepare the flat files on the box (LF → patch → CRLF),
  checked byte for byte, and replayed: 97 OK. Firewall `ufw` **deliberately left
  unchanged**.
- **Lesson**: an invisible detail (line endings) is enough to block a patch; a
  respected stop condition is better than forcing.
- **Files touched**: none on the node (copies in `/tmp/stage`).
- **Commands**:

```bash
ssh <UTILISATEUR>@<IP_FILAIRE_DU_NOEUD>          # → « Connection timed out »
Test-NetConnection <IP_FILAIRE_DU_NOEUD> -Port 22  # (PowerShell, poste de contrôle) → échec
ssh -v -o StrictHostKeyChecking=yes <UTILISATEUR>@<IP_DU_NOEUD>  # lecture de l’empreinte, forme exacte non consignée
patch -p1 --dry-run   # sur /tmp/stage/... → 5/5 hunks FAILED (« different line endings »)
# commandes exactes non consignées : conversion LF → patch → CRLF sur la box
```

- **Rollback**: not applicable; cleanup `rm -rf /tmp/stage /tmp/proposition.patch` on the node.

### Phase O — Deploying contradiction detection (01:40–01:45)

- **Looking for**: installing the patch without losing anything.
- **Tried**: stopping the service, **timestamped backup** (index + state +
  `organism.py`), installing the 3 files, restart, then the Vornex protocol through
  `/perceive` (see phase Q).
- **Observed**: service active, no error, memory count unchanged. `py_compile`
  could not write its cache (`__pycache__` owned by root): not blocking, the
  service compiles in memory.
- **Lesson**: backup + rollback command written **before** the change.
- **Files touched**: `organism.py`, `fact_conflict.py` (new), `dedup_taught_facts.py` (new).
- **Commands**:

```bash
sudo systemctl stop memory-node
# commande exacte non consignée : création de backups/contradictions_20261025T014030.tgz
#   (MemorySystemAI/memory_index.json + state/ + organism.py)
tar tzf backups/contradictions_20261025T014030.tgz   # contrôle : 340 entrées
# commande exacte non consignée : copie des 3 fichiers dans /opt/memorysystemai
sudo systemctl start memory-node
```

- **Rollback**:

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/contradictions_20261025T014030.tgz && rm -f fact_conflict.py dedup_taught_facts.py && sudo systemctl start memory-node && systemctl is-active memory-node
```

  (also restores the index as of 25.10 01:40:30: memories created since would be lost.)
  Details: [change record](changements/2026-10-25_detection-contradictions.md).

### Phase P — Merging duplicates (01:44, with Vincent’s agreement)

- **Looking for**: removing the exact copies accumulated before the patch, which
  skewed recall.
- **Tried**: dry-run on a copy of the index, then a new backup and `--apply`.
- **Observed**: **6 groups** of exact duplicates merged, **1044 → 1036**
  memories; survivors’ exposants unchanged, correlations retargeted,
  contradictions left intact, removed entries archived.
- **Lesson**: cleaning yes, erasing without trace no: the dry-run shows, the human
  decides, the archive keeps.
- **Files touched**: `MemorySystemAI/memory_index.json` (+ `.bak-…` and `dedup-archive-….json` created by the script).
- **Commands**:

```bash
sudo systemctl stop memory-node
# commande exacte non consignée : création de backups/dedup_20261025T014429.tgz (index + state/)
tar tzf backups/dedup_20261025T014429.tgz        # 341 entrées
python3 dedup_taught_facts.py --index MemorySystemAI/memory_index.json            # dry-run (chemin exact non consigné)
python3 dedup_taught_facts.py --index MemorySystemAI/memory_index.json --apply    # idem
sudo systemctl start memory-node
```

- **Rollback**:

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/dedup_20261025T014429.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

### Phase Q — Vornex test (blue / red contradiction, 01:45)

- **Looking for**: checking under real conditions that truth is not decided by the
  number of repetitions.
- **Tried**: successive messages to `/perceive` (no voice):

| Step | Result |
|------|--------|
| « … est de couleur bleue. » | 1 fact e8 |
| « … est de couleur rouge. » | 2nd fact e8, reciprocal correlation, **one** `ask_human` question |
| Red repeated | no new fact (duplicate avoided) |
| Question « De quelle couleur … ? » | `source: memory`, `uncertain`, both values quoted, « Je ne choisis pas » |
| Question asked 3 times | **no re-asking** |

- **Observed**: expected behaviour at every step. The question is left **pending**
  for Vincent.
- **Lesson**: memory is consulted before the LLM and states its doubt instead of
  choosing. Protocol: [`TEST_PROTOCOL_CONTRADICTIONS.md`](TEST_PROTOCOL_CONTRADICTIONS.md).
- **Files touched**: index (new memories), `state/ask_human.json`.
- **Commands**:

```bash
# commande exacte non consignée : curl depuis le nœud vers 127.0.0.1:8765/perceive (speak=false),
#   une requête par phrase du tableau
```

- **Rollback**: the one from phase O (also erases these test memories).

### Phase R — Quarvel test (25.10.2026 23:17–23:25, green / yellow)

- **Looking for**: replaying a truth / lie test without reinforcing the Vornex
  facts still awaiting an answer.
- **Tried**: the planned protocol reused the Vornex subject → test **stopped at
  23:17** before anything was sent; fresh subject "lampe Quarvel du hangar"
  **approved by Vincent** ("oui, va pour la lampe Quarvel"), backup, then
  green → yellow → green → question.
- **Observed**: contradiction **detected**, reciprocal correlation; recall
  **refuses to choose** and quotes both values; "verte" repeated: **no
  duplicate**. **No new question**: only one can be pending (Vornex’s was), which
  is the intended anti-harassment. The `uncertain` field could not be read
  (truncated output): **not verified**. The index had grown from ~1036 to 1262
  entries since the morning (see phase S).
- **Lesson**: a test subject is not reused while a question is open; what we did
  not see, we write down as "not verified".
- **Files touched**: index (+6 memories); `ask_human.json` unchanged.
- **Commands**:

```bash
# commande exacte non consignée : création de backups/inhibition_20261025T232008.tgz
tar tzf backups/inhibition_20261025T232008.tgz   # 350 entrées
# commandes exactes non consignées : 4 envois à /perceive (É1 verte, É2 jaune, É3 verte, É4 question)
```

- **Rollback** (erases everything learned since 23:20:08):

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/inhibition_20261025T232008.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

### Phase S — Findings after the tests

- **Looking for**: understanding two anomalies seen during the Quarvel test.
- **Observed**:
  1. **~226 more "Autonomie inhibée: …" memories** since the morning, created by
     the background loop (introduced in **phase L**): one `learn_perception` per
     blocked action.
  2. **`contradiction_ids` wrongly present from the first fact** (the list holds
     the single recalled fact, with no real contradiction).
- **Lesson**: a targeted test also reveals effects elsewhere; we note them before
  fixing them.
- **Files touched / commands / rollback**: none (observation).

### Phase T — Examining the two findings (23:29–23:35, nothing changed in production)

- **Looking for**: the exact cause of S.1 and S.2.
- **Tried**: Vincent’s agreement: "examine and prepare, do not deploy". Read-only
  copy of the node brought back to the box, code reading, patch prepared and
  tested on that copy.
- **Observed**:
  - S.1: `autonomy.py` (`through_memory`) creates a memory on **every** blocked
    tick, every 300 s (12 per hour): **542** memories, 541 with identical text.
  - S.2: `organism.py` returns `[entry.id, *ids]` even when `ids` is empty; the
    value is then copied into the response.
  - On the copy: patched code **0 failures**; production code **3 failures** (bug
    reproduced); contradiction demo **97 OK**. Cleanup dry-run: 1 group, 1270 → 730.
  - Caveat: reinforcement (cap 8) would push the surviving memory above the
    injection threshold (≥ 7).
- **Lesson**: reproduce the bug on the old code before believing in the fix.
- **Files touched**: none in production.
- **Commands**:

```bash
# commandes exactes non consignées : archive /tmp/autosnap.tgz sur le nœud, rapatriée sur la box
# commandes exactes non consignées : lancement des tests sur copie (ancien code / code patché)
```

- **Rollback**: not applicable.

### Phase U — Fix: contradiction_ids announced too early (deployed at 23:36)

- **Looking for**: a first fact should no longer be presented as a contradiction.
- **Tried**: one line: `[entry.id, *ids] if ids else []`, shipped in the same patch
  as phase V (v1).
- **Observed**: on the copy, É1 clean, É2/É4 `uncertain: true` + 2 ids; applied in
  production together with phase V (dry-run OK, CRLF line endings preserved,
  in-memory `compile()` OK). Automated test:
  [`tests/test_autonomie.py`](../../prototypes/memory-node/tests/test_autonomie.py) (section 4).
- **Lesson**: an API field must say the same thing as the real state.
- **Files touched**: `organism.py`. Record: [`changements/2026-10-25_autonomie-contradiction-ids.md`](changements/2026-10-25_autonomie-contradiction-ids.md).
- **Commands / rollback**: see phase V (same patch, same backup).

### Phase V — Autonomie inhibée: counting instead of copying (23:36–23:52)

- **Looking for**: stopping the pile-up of copies without losing the history of refusals.
- **Tried**:
  1. **Patch v1**: an identical refusal **reinforces** the existing memory (same
     rule as taught facts, cap 8) instead of creating a new one.
  2. **Cleanup v1** of the existing stock (1271 → 730).
  3. **Vincent’s stop**, then a **new decision**: "merge while keeping the number
     and the dates".
  4. **Patch A**: `autonomy.py` counts occurrences (`occurrences` +
     `occurrence_dates`, ISO with time zone); `memory_system.py` serialises and
     reads back these two fields (otherwise `to_dict` / `from_dict` erased them at
     every save).
  5. **Merge with occurrences** into the surviving “autonomy inhibited” memory, rebuilding the counter
     from the cleanup-v1 archive and the times from the node’s log.
- **Observed**:
  - Cleanup v1 was applied at 23:36:26, **before** Vincent’s stop order, and it
    **kept neither the number nor the dates**. Nothing was lost: full archive of
    the 541 removed entries + full previous index; nothing was restored.
  - Patch A tested on a copy: 3 ticks → counter +3, stable entries, fields kept
    after save and reload, 0 orphans, 97 tests OK.
  - Merge: **543 occurrences** (1 + 541 archived + 1 reinforcement), 543 ISO dates.
    The node log times matched one to one, day by day
    (21.07: 76, 22.07: 210, 24.10: 5, 25.10: 252); the 25.10 clock change (02:xx
    twice) is handled (+02:00 then +01:00).
  - Result: **730 memories**, 0 orphan correlations. Check after 10 min (23:51):
    730 stable, no new "Autonomie inhibée", each tick counted (546 occurrences),
    survivor at e8.
- **Lesson**: a merge must keep the **trace** (how many, when), not just the text;
  a stop order must be able to interrupt a sequence already under way; a new field
  only really exists if saving preserves it.
- **Files touched**: `autonomy.py`, `organism.py` (phase U), `memory_system.py`,
  index (+ archive `autonomie-archive-….json` and `.bak-…` copies). Scripts:
  [`maintenance/`](../../prototypes/memory-node/maintenance/README.en.md).
  Record: [`changements/2026-10-25_autonomie-contradiction-ids.md`](changements/2026-10-25_autonomie-contradiction-ids.md).
- **Commands**:

```bash
sudo systemctl stop memory-node                                    # 23:36:07
# commande exacte non consignée : création de backups/autonomie_20261025T233607.tgz
patch -p1 --dry-run < proposition.patch   # forme exacte non consignée ; « dry-run OK »
# commande exacte non consignée : application du patch v1
python3 nettoyage_autonomie_inhibee.py --index MemorySystemAI/memory_index.json --apply   # chemin exact non consigné
sudo systemctl start memory-node                                   # 23:36:46
sudo systemctl stop memory-node                                    # 23:40:03
# commande exacte non consignée : création de backups/autonomie_occurrences_20261025T234003.tgz
# commande exacte non consignée : application du patch A
python3 fusion_autonomie_occurrences.py --index MemorySystemAI/memory_index.json \
  --keep <ID_DU_SURVIVANT> --archive MemorySystemAI/autonomie-archive-20261025-233626.json --log <JOURNAL_DU_NOEUD>
#   (dry-run puis --apply à 23:40:22 ; arguments exacts non consignés)
sudo systemctl start memory-node                                   # 23:40:22
```

- **Rollback**:

```bash
# avant la fusion avec occurrences (code v1 + index à 730) :
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/autonomie_occurrences_20261025T234003.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
# complet (code d’origine + index à 1271) :
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/autonomie_20261025T233607.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

  The last archive does not contain `memory_system.py`: restore it from
  `autonomie_occurrences_20261025T234003.tgz` or keep the patched version
  (backward-compatible). Both rollbacks erase what has been learned since.

### Phase W — Voice fixes (23:53)

- **Looking for**: the node should no longer take its own synthetic voice for a person.
- **Tried**:
  1. `autonomy.py`: `hear_self` no longer calls `voice.process_wav` (learning the
     perception is kept);
  2. `voice_memory.py`: `tts_self_*` clips are ignored (`_is_tts_self`) by
     `process_wav` and `label_pending_or_last`;
  3. `organism.py`: half-duplex `SPEAKING` around audio playback, 0.5 s guard;
     recording waits at most 100 s, then records anyway;
  4. deletion of the false voice profile, which was the synthetic voice itself.
- **Observed**: tests on copy **20/20**, contradiction demo 97 OK; in production:
  service active, 0 errors, existing profiles unchanged, pending question
  unchanged. Since `hear_self` has not run since, fix 1 is **verified on the copy
  only**. `sensory_agent.py` (another recording process) is **not** covered by
  `SPEAKING` (not modified).
- **Lesson**: a machine that listens to itself must be able to tell its own voice
  apart; the simplest way is not to listen while it speaks.
- **Files touched**: `autonomy.py`, `voice_memory.py`, `organism.py`,
  `state/voice_persons.json`. Test: [`tests/test_voix.py`](../../prototypes/memory-node/tests/test_voix.py).
  Record: [`changements/2026-10-25_voix-half-duplex.md`](changements/2026-10-25_voix-half-duplex.md).
- **Commands**:

```bash
sudo systemctl stop memory-node                                    # 23:53:40
# commande exacte non consignée : création de backups/voix_20261025T235340.tgz (355 fichiers)
# commande exacte non consignée : installation des fichiers patchés (voix.patch)
python3 supprimer_vp002.py state/voice_persons.json --apply   # chemin exact non consigné
sudo systemctl start memory-node                                   # 23:53:43
```

- **Rollback**:

```bash
# commande non consignée au journal ; sur le modèle des phases précédentes :
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/voix_20261025T235340.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```

| Still to do | State |
|-------------|-------|
| Decide whether the "Autonomie inhibée" memory should stay above the injection threshold (≥ 7) | to decide |
| Cover `sensory_agent.py` with the half-duplex | postponed (Vincent’s decision: “not now”) |
| Answer the pending Vornex questions | Vincent |

---

## 3. Resulting architecture

```
POST /perceive
   │
   ├─ hearing correction / identity / feedback    (phase I, unchanged)
   ├─ taught fact ("X est Y")
   │     └─ fact_conflict.classify_new_fact       (phase O)
   │           ├─ new            → Fait enseigné C/P/e8 (as before)
   │           ├─ duplicate      → reinforcement (cap 8), no new entry
   │           └─ contradiction  → new fact + reciprocal correlations
   │                               + 1 ask_human question (if box free)
   └─ interpret_with_tools
         ├─ inhibition (≥ 9)                       (unchanged)
         ├─ open contradiction → uncertain recall, source memory (phase O)
         ├─ memory recall / corroboration           (phase L)
         └─ LLM screen → LLM / ask_human            (phase L)

Background loop (phase L): tick_initiative → through_memory → "Autonomie inhibée"
      └─ same refusal → reinforcement + occurrences / dates   (phase V)

Voice (phase W): TTS playback → SPEAKING raised → microphone waits (+0.5 s)
      hear_self → no voiceprint; tts_self_* clips ignored
```

---

## 4. Design decisions (traces)

| Temptation | Decision |
|------------|----------|
| Delete the "false" fact | Rejected — both stay, at the same exposants |
| Move the lie to state N | Rejected — no implicit punishment |
| Let the number of repetitions decide | Rejected — recall refuses to choose |
| Question queue | Rejected — one question at a time, no harassment |
| Use `MemorySystem.evaluate` (3 common words) | Rejected — abusive merges |
| Migrate the index at startup | Rejected — old indexes read as they are |
| Open the firewall to ease access | Rejected — `ufw` unchanged |

---

## 5. Lessons learned

1. Repetition is not proof: without an explicit link, memory "votes".  
2. A real test must use a **fresh subject** so as not to reinforce a previous test.  
3. Always **back up first**, and write the rollback command **before** acting.  
4. Flat deployment and CRLF line endings trap a naive `patch`.  
5. A background loop that writes to memory on every block **inflates the index**.  
6. Check the host key fingerprint before switching network interface.  
7. A period without commits or chronicle is lost for research: keep the journal
   **as you go** (see the [contribution rule](../../CONTRIBUTING.md#continuing-the-journal)).
8. A merge must keep the trace (number, dates), and a new field only exists if
   saving preserves it (phase V).
9. A stop order must be able to interrupt a sequence already under way (phase V).
10. A machine that listens to itself must recognise its own voice (phase W).

---

## 6. Next (concept priorities)

| Item | State | Priority |
|------|-------|----------|
| "Autonomie inhibée" pile-up | fixed (phases U–V) | — |
| `contradiction_ids` without contradiction | fixed (phases U–V) | — |
| Fundamental & State | fragile heuristic (inherited from July) | High |
| Semantic similarity | word overlap (inherited from July) | High |
| Human answer to the pending Vornex questions | waiting for Vincent | Medium |
| "First est" heuristic (simple French) | known limit | Medium |
| Inhibition of machine actions (SSH/sudo) | not wired (inherited from July) | Medium |
| `GET /memories` without correlations | known | Low |

---

## 7. File map

| Path | Role | Phase |
|------|------|-------|
| `prototypes/memory-node/autonomy.py` | Autonomy tools, initiative loop | K–L, V–W |
| `prototypes/memory-node/fact_conflict.py` | Subject / value heuristic, standard library | O |
| `prototypes/memory-node/dedup_taught_facts.py` | Duplicate merge (dry-run by default) | O–P |
| `prototypes/memory-node/organism.py` | Runtime; hooks L, O, U, W | L, O, U, W |
| `prototypes/memory-node/voice_memory.py` | Voice memory; ignores `tts_self_*` | W |
| `memory_system.py` | Optional fields `occurrences` / `occurrence_dates` | V |
| `prototypes/memory-node/maintenance/` | Manual scripts (merge, false voice profile deletion) | V–W |
| `prototypes/memory-node/tests/` | Automated tests (97 + 15 + 18 checks) | O, U–W |
| `docs/changements/` | Change records (EN: `docs/en/changements/`) | O, U–W |

---

## 8. Acknowledgements / provenance

Concept and purpose: **Vincent Vermeille** (Humanum-Contactus).  
July 2026 (phases J–L): repository commits. October 2026 (phases M–W):
human + agent collaboration; each step submitted to Vincent, backed up first and
reversible — except cleanup v1 in phase V, applied before his stop order (nothing
lost: full archive).

---

← **Previous:** [Period 21.07 – 24.10.2026 (project paused)](EVOLUTION_MEMORY_NODE_2026-07-10.md) ·
**Next:** *(none yet)* · [Docs index](README.md) · [CHANGELOG](../../CHANGELOG.en.md) ·
[Change records](changements/README.md)
