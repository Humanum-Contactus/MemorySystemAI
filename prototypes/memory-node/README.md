# Prototype `memory-node` — organisme incarné

Premier jet d’un **nœud Sensors&MemorySystemAI** : ardoise quasi vide,
outils sensoriels, consultation LLM externe, apprentissage par exposants,
nursery graphique locale.

> Ce n’est **pas** un chatbot avec interdits texte.  
> Le LLM est un **outil**, pas l’identité.  
> Les normes apprises vivent dans **`memory_index`**, pas dans des tables `.py`.

Documentation :

| Doc | Contenu |
|-----|---------|
| [Chronique d’évolution](../../docs/EVOLUTION_MEMORY_NODE_2026-07.md) | Histoire du chantier |
| [Architecture & API](../../docs/ARCHITECTURE_MEMORY_NODE.md) | Flux + routes HTTP |
| [Modules](../../docs/MODULES_MEMORY_NODE.md) | Référence fichier par fichier |
| [Pourquoi ça compte](../../docs/POURQUOI_CA_COMPTE.md) | Sens de la recherche |
| [Index docs](../../docs/README.md) | Tous les docs |

---

## Contenu de ce dossier

| Fichier | Rôle |
|---------|------|
| `organism.py` | Runtime HTTP : boucle cognitive + outils |
| `visual_memory.py` | Empreintes visage → identité (V) |
| `voice_memory.py` | Empreintes voix → identité (O) |
| `sensor_camera.py` | Auto-réglage caméra V4L2 |
| `sensor_mic.py` | Auto-réglage gain micro ALSA |
| `ui/index.html` | Nursery kiosk |
| `requirements.txt` | Dépendances Python indicatives |
| `systemd/memory-node.service.example` | Unit systemd |
| `openclaw-skill/` | Pont Telegram (**pont**, pas le cœur du concept) |

Prérequis : package `MemorySystemAI` (racine du dépôt) sur `PYTHONPATH`,
ou déployé sous `/opt/memorysystemai/` (prod).

---

## Boucle cognitive

```
perception (texte / micro / caméra)
    → inhibition (mémoires à tags, exposant élevé)
    → rappel mémoire (prioritaire si fait déjà appris)
    → sinon consulter LLM (outil)
    → sinon request_human (inhibé si mémoire anti-harcèlement + pending)
    → enregistrer (fondamentaux + exposant)
```

---

## API (résumé)

| Méthode | Route | Rôle |
|---------|-------|------|
| GET | `/` | Nursery |
| GET | `/status` `/memories` `/faces` `/voices` `/ask` `/mic` `/camera` `/vision` | État |
| POST | `/perceive` | Perception texte (+ teach identité / corrections) |
| POST | `/see` `/capture` `/hear` `/speak` | Capteurs |
| POST | `/mic` `/camera` `/volume` `/vision` | Capteurs / sortie |
| POST | `/ask/answer` | Réponse tuteur |
| POST | `/reset` | `{"confirm":"RESET_ORGANISM"}` |

Détail : [ARCHITECTURE_MEMORY_NODE.md](../../docs/ARCHITECTURE_MEMORY_NODE.md).

---

## Déploiement typique (Ubuntu nœud)

```bash
# Sur le nœud (exemple)
sudo mkdir -p /opt/memorysystemai
# copier MemorySystemAI + prototypes/memory-node/*.py + ui/
sudo systemctl enable --now memory-node.service
# tokens hors git :
#   /opt/memorysystemai/state/nvidia_token.txt
#   /opt/memorysystemai/state/puter_token.txt
```

Voir `systemd/memory-node.service.example`.

---

## Enseignements utiles (tuteur)

```text
c'est moi Vincent
quand tu entends c'est mauve ca ça veut dire c'est moi Vincent
arrête de me relancer   # renforce l'inhibition sociale si ask pending
MonWifi est le réseau local.
```

---

## Ce que ce prototype n’est pas encore

- Similarité sémantique robuste  
- Corroboration multi-sens complète  
- Fundamental/State automatiques fiables  
- Indépendance totale vis-à-vis des ponts type OpenClaw  

Le risque conscient : rester un « chatbot amélioré avec mémoire ».  
La boussole : **crible mémoire + exposants**, partout.
