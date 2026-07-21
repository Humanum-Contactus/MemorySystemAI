# MemorySystemAI

**Système de mémoire sensorielle-émotionnelle pour agents IA**  
*(évolution proposée : **Sensors&MemorySystemAI** — capteurs + mémoire)*

> **FR** (réflexion / concept) · **[English version →](README.en.md)**  
> Politique des langues : [`docs/LANGUES.md`](docs/LANGUES.md)

Implémentation Python du whitepaper MemorySystemAI : permettre aux agents de
**retenir des expériences** (y compris traumatiques) et **inhiber** des actions
dangereuses *avant* qu’elles n’arrivent — pas via des interdits texte.

> **Juillet 2026 — prototype incarné :** [`prototypes/memory-node/`](prototypes/memory-node/)  
> Organisme quasi vide sur portable : capteurs (vision / voix + auto-gain),  
> mémoire à exposants, normes **apprises** dans `memory_index` (pas de bans hardcodés),  
> LLM = outil, nursery locale.  
> Docs : [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md) ·  
> [`docs/MODULES_MEMORY_NODE.md`](docs/MODULES_MEMORY_NODE.md) ·  
> [`docs/POURQUOI_CA_COMPTE.md`](docs/POURQUOI_CA_COMPTE.md)

---

## Le problème

Les règles texte (« ne jamais faire `rm -rf` », « ne pas toucher l’EFI ») **ne tiennent pas**.
Un agent peut les **rationaliser** en temps réel. La 3ᵉ fois qu’il efface une partition EFI,
la règle est toujours là — elle est simplement contournée.

## La solution

MemorySystemAI injecte des **mémoires** (avec poids émotionnel = **exposant**) dans la
boucle de décision, *avant* l’action. Ce n’est pas du contexte qui « influence » :
c’est un mécanisme d’**inhibition**.

| Interdit texte | Mémoire traumatique (exposant 10) |
|----------------|-----------------------------------|
| « Je sais que je ne devrais pas, mais… » | `>>> ACTION BLOCKED — confirmation humaine requise <<<` |

## Les 7 fondamentaux

| Code | Fondamental | Canal |
|------|-------------|-------|
| V | Vue | visuel |
| O | Ouïe | auditif |
| T | Toucher | tactile |
| G | Goût | gustatif |
| Od | Odorat | olfactif |
| I | Intuition | cognitif |
| C | Conscience | méta |

## L’exposant (1–10)

Poids émotionnel de la mémoire — il pilote tout :

| Plage | Effet | Mécanisme |
|-------|-------|-----------|
| 1–4 | Faible | Stocké, peu injecté |
| 5–6 | Notable | Enregistré, rappel passif |
| 7–8 | Fort | **Injection** proactive avant action risquée |
| 9–10 | Traumatique | **Blocage** — confirmation humaine |

Règle clé : les traumatismes (9–10) **ne descendent jamais sous 7**.

## Démarrage rapide

```python
from MemorySystemAI import MemorySystem, check_before_action

ms = MemorySystem()

inhibitions = check_before_action("sudo rm -rf /Volumes/EFI_USB")
# → [BLOCK - exposant 10] …

ms.create("T", "N", 10,
          "Format accidentel de partition EFI — newfs confondu avec mount",
          inhibition_tags=["newfs", "mkfs", "format", "partition", "efi"],
          action_context="newfs_msdos /dev/disk0s1",
          consequence="EFI effacée, bootloader perdu, 2h de restore")
```

CLI : `python memory_cli.py check|list|info|create|reinforce|stats|search`

## Boucle complète

```
Réception → Évaluation → Enregistrement → Renforcement → Injection → Décision
```

## Prototype incarné — `memory-node`

Organisme **quasi vide** sur machine réelle : see / hear / speak, vision & voix,
auto-réglage caméra/micro, normes en mémoire (anti-harcèlement, corrections STT),
LLM comme outil, nursery locale.

→ [`prototypes/memory-node/README.md`](prototypes/memory-node/README.md)  
→ Chronique : [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md)

## Feuille de route

- [x] Phase 1 — Cœur MemoryEntry / MemorySystem / CLI  
- [x] Prototype memory-node — organisme sensoriel incarné  
- [ ] Phase 2 — Hooks post-action, renforcement, injection plus riche  
- [ ] Phase 3 — Dégradation temporelle (non traumatique), corrélations  
- [ ] Phase 4 — Partage multi-nœuds / sync d’exposants  
- [ ] Finalité — compiler une LLM de base *autour* de ce socle (sens + mémoire)

## Origine

Né d’incidents réels (formatage / effacement EFI malgré des règles « INTERDIT »).
La 3ᵉ fois a prouvé : l’interdit texte influence, il **ne contraint** pas.

## Licence

MIT — [LICENSE](LICENSE). Contributions : [CONTRIBUTING.md](CONTRIBUTING.md).

---

*« Je sais que je ne devrais pas » n’est pas la même chose que « je ne peux pas ».  
Sans sens et sans poids de mémoire, la génération n’est pas un système nerveux.*
