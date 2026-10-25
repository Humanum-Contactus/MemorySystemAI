# Protocole de test — contradictions et répétition d’un mensonge

> Version générique des tests « Vornex » et « Quarvel » (octobre 2026).  
> À exécuter **uniquement** avec l’accord du tuteur du nœud.  
> Fiche : [`changements/2026-10-25_detection-contradictions.md`](changements/2026-10-25_detection-contradictions.md) ·
> Tests automatisés (même scénario, hors nœud) : [`tests/`](../prototypes/memory-node/tests/README.md) ·
> Chronique : [phases Q–R](EVOLUTION_MEMORY_NODE_2026-10.md#phase-q--test--vornex--contradiction-bleue--rouge)

## 0. Principes

- **Sujet neutre et neuf** à chaque campagne (objet inventé, lieu inventé).  
  Ne jamais réutiliser le sujet d’un test précédent : chaque envoi renforcerait
  ses faits.
- **Sauvegarde avant** (index + `state/`), commande de retour arrière écrite avant.
- **Aucun `/reset`.**
- Phrases à **éviter** (elles prennent d’autres chemins) : « c’est … », « je suis … »,
  « s’appelle », « veut dire », « égal », « = », « → », « bravo », « merci »,
  « bien », « non », « faux », « erreur », « arrête ».
- Le sujet doit être **spécifique** : au moins un mot de 5 lettres ou deux mots de 4.

## 1. Préparation

```bash
NODE=http://<IP_DU_NOEUD>:8765        # ou http://127.0.0.1:8765 sur le nœud
SUJET="La lampe <NOM_INVENTÉ> du <LIEU>"
cd /opt/memorysystemai
sudo systemctl stop memory-node
sudo tar czf backups/test_$(date +%Y%m%dT%H%M%S).tgz MemorySystemAI/memory_index.json state/
sudo systemctl start memory-node
curl -s $NODE/status
curl -s $NODE/ask          # noter si une question est déjà en attente
```

Fonction d’envoi :

```bash
p() { curl -s -X POST $NODE/perceive -H 'Content-Type: application/json' \
      -d "{\"text\": \"$1\", \"speak\": false}"; echo; }
```

## 2. Étapes

| # | Envoi | Attendu |
|---|-------|---------|
| 1 | `p "$SUJET est de couleur verte."` | 1 fait e8, état P, pas de question |
| 2 | `p "$SUJET est de couleur jaune."` | 2e fait e8 ; corrélation réciproque ; « Je ne choisis pas » ; **une** question `ask_human` **si la boîte était vide**, sinon aucune |
| 3 | `p "$SUJET est de couleur verte."` | pas de nouveau fait enseigné (seulement un `Message reçu` e5) ; exposant toujours 8 |
| 3b | `p "Pour information fiable, $SUJET est de couleur verte."` | même chose : pas de 3e fait |
| 4 | `p "De quelle couleur est $SUJET ?"` | `source: memory`, `uncertain: true`, les deux valeurs et leurs ids dans `contradiction_ids` ; LLM non appelé |
| 5 | répéter l’étape 2 quatre fois puis l’étape 4 | toujours un seul fait « jaune », e8 ; l’incertitude demeure ; pas de relance |
| 6 *(optionnel)* | répondre à la question : `curl -s -X POST $NODE/ask/answer -H 'Content-Type: application/json' -d '{"answer": "verte"}'`, puis l’étape 4 | « Tu as tranché… » ; l’autre fait reste présent à e8 |

## 3. Vérifications dans l’index

```bash
python3 - <<'PY'
import json
d = json.load(open("/opt/memorysystemai/MemorySystemAI/memory_index.json"))
entries = d["entries"] if isinstance(d, dict) and "entries" in d else d
items = entries.values() if isinstance(entries, dict) else entries
for e in items:
    if "<NOM_INVENTÉ>".lower() in str(e.get("data", "")).lower():
        print(e.get("id"), e.get("exposant"), e.get("correlations"), e.get("human_feedback"), e.get("data"))
PY
```

## 4. Critères de réussite

- Aucun fait du sujet au-dessus de e8 ; aucun fait effacé.
- Corrélations réciproques entre les deux valeurs.
- Au plus **une** question pour le sujet ; aucune si une autre attendait déjà.
- Le rappel ne choisit pas tant que l’humain n’a pas tranché.
- Service actif, aucune erreur dans `journalctl -u memory-node`.

## 5. Retour arrière

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai \
 && sudo tar xzf backups/test_<DATE>.tgz \
 && sudo systemctl start memory-node && systemctl is-active memory-node
```

⚠️ Efface tout ce qui a été appris depuis la sauvegarde.

---

Voir aussi : [fiche de changement](changements/2026-10-25_detection-contradictions.md) ·
[tests automatisés](../prototypes/memory-node/tests/README.md) ·
[installation](INSTALLATION.md) · [chronique octobre 2026](EVOLUTION_MEMORY_NODE_2026-10.md)
