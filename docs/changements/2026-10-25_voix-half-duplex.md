# Fiche de changement — voix : ne plus se prendre pour quelqu’un

> **FR (source)** · **[English →](../en/changements/2026-10-25_voix-half-duplex.md)** · [`LANGUES.md`](../LANGUES.md)  
> Chronique : [phase W](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-w--corrections-voix-2353) ·
> Tests : [`test_voix.py`](../../prototypes/memory-node/tests/test_voix.py) ·
> [CHANGELOG](../../CHANGELOG.md) · [Toutes les fiches](README.md)

| Champ | Valeur |
|-------|--------|
| Date | 25.10.2026, 23:53, heure de Zurich |
| Fichiers | `prototypes/memory-node/autonomy.py`, `voice_memory.py`, `organism.py` ; script `maintenance/supprimer_vp002.py` ; donnée `state/voice_persons.json` (nœud) |
| Dépendances nouvelles | aucune |
| Statut | déployé sur le nœud ; reporté dans ce dépôt ; tests verts |

## 1. Pourquoi

Le nœud s’écoutait parler (`hear_self`) et enregistrait sa **propre voix de
synthèse** comme une personne : fausse fiche voix VP002. Son micro pouvait aussi
enregistrer pendant qu’il parlait.

## 2. Quoi

1. `hear_self` n’appelle plus `voice.process_wav`.
2. `voice_memory.py` ignore tout clip `tts_self_*`.
3. `organism.py` : half-duplex `SPEAKING` + garde 0,5 s ; attente bornée à 100 s.
4. Suppression de VP002 (`supprimer_vp002.py`, autres fiches vérifiées identiques).

Limite : `sensory_agent.py` (processus séparé) n’est pas couvert par `SPEAKING`.

## 3. Comment tester

```bash
python3 prototypes/memory-node/tests/test_voix.py   # données et sons fabriqués
```

## 4. Ce qui a été exécuté, et retour arrière

Commandes et démarche : [phase W](../EVOLUTION_MEMORY_NODE_2026-10.md#phase-w--corrections-voix-2353).
Le journal ne consigne pas de commande de retour arrière pour cette étape ; sur le
modèle des autres :

```bash
sudo systemctl stop memory-node && cd /opt/memorysystemai && tar xzf backups/voix_20261025T235340.tgz && sudo systemctl start memory-node && systemctl is-active memory-node
```
