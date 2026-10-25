# Test protocol — contradictions and a repeated lie

> **[FR (source) →](../PROTOCOLE_TEST_CONTRADICTIONS.md)** · EN · [`LANGUES.md`](../LANGUES.md)  
> Generic version of the "Vornex" and "Quarvel" tests (October 2026). French is authoritative.  
> Run **only** with the agreement of the node's tutor.  
> Record: [`changements/2026-10-25_detection-contradictions.md`](changements/2026-10-25_detection-contradictions.md) ·
> Automated tests (same scenario, off-node): [`tests/`](../../prototypes/memory-node/tests/README.en.md) ·
> Chronicle: [phases Q–R](EVOLUTION_MEMORY_NODE_2026-10.md#phase-q--vornex-test-blue--red-contradiction-0145)

The sentences are sent **in French**: the detector (`fact_conflict.py`) is a French
heuristic (it splits on the first « est »).

## 0. Principles

- **Neutral, fresh subject** for each campaign (invented object, invented place).
  Never reuse the subject of a previous test: each message would reinforce its facts.
- **Back up first** (index + `state/`), rollback command written beforehand.
- **No `/reset`.**
- Phrases to **avoid** (they take other code paths): « c’est … », « je suis … »,
  « s’appelle », « veut dire », « égal », « = », « → », « bravo », « merci »,
  « bien », « non », « faux », « erreur », « arrête ».
- The subject must be **specific**: at least one 5-letter word or two 4-letter words.

## 1. Preparation

```bash
NODE=http://<NODE_IP>:8765        # or http://127.0.0.1:8765 on the node
SUJET="La lampe <INVENTED_NAME> du <PLACE>"
cd /opt/memorysystemai
sudo systemctl stop memory-node
sudo tar czf backups/test_$(date +%Y%m%dT%H%M%S).tgz MemorySystemAI/memory_index.json state/
sudo systemctl start memory-node
curl -s $NODE/status
curl -s $NODE/ask          # note whether a question is already pending
```

Send function:

```bash
p() { curl -s -X POST $NODE/perceive -H 'Content-Type: application/json' \
      -d "{\"text\": \"$1\", \"speak\": false}"; echo; }
```

## 2. Steps

| # | Message | Expected |
|---|---------|----------|
| 1 | `p "$SUJET est de couleur verte."` | 1 fact e8, state P, no question |
| 2 | `p "$SUJET est de couleur jaune."` | 2nd fact e8; reciprocal correlation; « Je ne choisis pas »; **one** `ask_human` question **if the box was empty**, otherwise none |
| 3 | `p "$SUJET est de couleur verte."` | no new taught fact (only a `Message reçu` e5); exposant still 8 |
| 3b | `p "Pour information fiable, $SUJET est de couleur verte."` | same: no 3rd fact |
| 4 | `p "De quelle couleur est $SUJET ?"` | `source: memory`, `uncertain: true`, both values and their ids in `contradiction_ids`; LLM not called |
| 5 | repeat step 2 four times, then step 4 | still a single "jaune" fact, e8; uncertainty remains; no re-asking |
| 6 *(optional)* | answer the question: `curl -s -X POST $NODE/ask/answer -H 'Content-Type: application/json' -d '{"answer": "verte"}'`, then step 4 | « Tu as tranché… »; the other fact stays at e8 |

## 3. Checks in the index

```bash
python3 - <<'PY'
import json
d = json.load(open("/opt/memorysystemai/MemorySystemAI/memory_index.json"))
entries = d["entries"] if isinstance(d, dict) and "entries" in d else d
items = entries.values() if isinstance(entries, dict) else entries
for e in items:
    if "<INVENTED_NAME>".lower() in str(e.get("data", "")).lower():
        print(e.get("id"), e.get("exposant"), e.get("correlations"), e.get("human_feedback"), e.get("data"))
PY
```

## 4. Success criteria

- No fact of the subject above e8; no fact deleted.
- Reciprocal correlations between the two values.
- At most **one** question for the subject; none if another was already pending.
- Recall does not choose until the human has decided.
- Service active, no error in `journalctl -u memory-node`.

## 5. Rollback

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai \
 && sudo tar xzf backups/test_<DATE>.tgz \
 && sudo systemctl start memory-node && systemctl is-active memory-node
```

⚠️ Erases everything learned since the backup.

---

See also: [change record](changements/2026-10-25_detection-contradictions.md) ·
[automated tests](../../prototypes/memory-node/tests/README.en.md) ·
[installation](INSTALLATION.md) · [October 2026 chronicle](EVOLUTION_MEMORY_NODE_2026-10.md)
