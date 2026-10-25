# MemorySystemAI

**Système de mémoire sensorielle-émotionnelle pour agents IA**  
*(évolution proposée : **Sensors&MemorySystemAI** — capteurs + mémoire)*

> **FR** (réflexion / concept) · **[English version →](README.en.md)**  
> Politique des langues : [`docs/LANGUES.md`](docs/LANGUES.md)

---

## Commencer par le fondement

Le cœur du projet n’est pas le code du prototype : c’est le **whitepaper**.

### 📄 [MemorySystemAI Whitepaper v1](whitepaper/MemorySystemAI_Whitepaper_v1.md)

Vincent Vermeille — Mai 2026 (FR/EN dans le même document)

> Un système nerveux artificiel pour IA : mémoire sensorielle, exposants émotionnels
> et inhibition apprise. Les règles texte influencent ; elles ne **contrainent** pas.
> Boucle : **Action → Évaluation → Exposant → Injection → Décision**.

C’est la base de réflexion (souvent en français) : diagnostic empirique (incidents EFI),
architecture des 7 fondamentaux, exposants, feuille de route jusqu’à une modulation
plus native. **Tout le reste du dépôt en découle.**

Lecture complémentaire : [`01_CONCEPT_FONDAMENTAL.txt`](01_CONCEPT_FONDAMENTAL.txt) ·
[`docs/POURQUOI_CA_COMPTE.md`](docs/POURQUOI_CA_COMPTE.md)

---

## Ce que le dépôt contient ensuite

Implémentation Python du whitepaper : permettre aux agents de **retenir des expériences**
et **inhiber** des actions dangereuses *avant* qu’elles n’arrivent.

> **Juillet 2026 — prototype incarné :** [`prototypes/memory-node/`](prototypes/memory-node/)  
> Première ébauche artisanale sur machine réelle (capteurs, mémoire à exposants,
> normes apprises, LLM = outil). Utile pour *voir* le concept vivre — pas pour le remplacer.  
> Chronique : [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md)

---

## Le problème (résumé)

Les règles texte (« ne jamais faire `rm -rf` », « ne pas toucher l’EFI ») **ne tiennent pas**.
Un agent peut les **rationaliser** en temps réel. La 3ᵉ fois qu’il efface une partition EFI,
la règle est toujours là — elle est simplement contournée.

## La solution (résumé)

MemorySystemAI injecte des **mémoires** (poids émotionnel = **exposant**) dans la
boucle de décision, *avant* l’action. Ce n’est pas du contexte qui « influence » :
c’est un mécanisme d’**inhibition**.

| Interdit texte | Mémoire traumatique (exposant 10) |
|----------------|-----------------------------------|
| « Je sais que je ne devrais pas, mais… » | `>>> ACTION BLOCKED — confirmation humaine requise <<<` |

Détail : **[whitepaper](whitepaper/MemorySystemAI_Whitepaper_v1.md)**.

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

| Plage | Effet | Mécanisme |
|-------|-------|-----------|
| 1–4 | Faible | Stocké, peu injecté |
| 5–6 | Notable | Enregistré, rappel passif |
| 7–8 | Fort | **Injection** proactive avant action risquée |
| 9–10 | Traumatique | **Blocage** — confirmation humaine |

Règle clé : les traumatismes (9–10) **ne descendent jamais sous 7**.

## Philosophie

Démarche empirique et pédagogique : code commenté pour un débutant, bibliothèque
standard d'abord, chaque dépendance justifiée, formats ouverts (JSON, texte,
Markdown), aucun service fermé obligatoire, et un journal qui raconte la démarche
(hypothèse, essai, résultat, leçon). Le but : que le savoir ne parte pas avec les
personnes. Règle de base : si les assistants disparaissent, n’importe qui doit pouvoir
comprendre, relire et refaire nos actions, sans abonnement, service payant ni outil fermé. Règles détaillées : [CONTRIBUTING.md — Philosophie du projet](CONTRIBUTING.md#philosophie-du-projet).

## Démarrage rapide (code)

```python
from MemorySystemAI import MemorySystem, check_before_action

ms = MemorySystem()

inhibitions = check_before_action("sudo rm -rf /Volumes/EFI_USB")

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

→ [`prototypes/memory-node/README.md`](prototypes/memory-node/README.md)  
→ Chronique : [`docs/EVOLUTION_MEMORY_NODE_2026-07.md`](docs/EVOLUTION_MEMORY_NODE_2026-07.md)  
→ Chronique octobre 2026 (contradictions) : [`docs/EVOLUTION_MEMORY_NODE_2026-10.md`](docs/EVOLUTION_MEMORY_NODE_2026-10.md)  
→ **Toute la documentation** : [`docs/README.md`](docs/README.md)  
→ **Installer et tester** : [`docs/INSTALLATION.md`](docs/INSTALLATION.md) · [`CHANGELOG.md`](CHANGELOG.md)

```bash
# test rapide, sans installation ni service
python3 prototypes/memory-node/tests/test_contradictions.py
```

## Feuille de route

- [x] Phase 1 — Cœur MemoryEntry / MemorySystem / CLI  
- [x] Prototype memory-node — organisme sensoriel incarné (ébauche)  
- [ ] Phase 2 — Hooks post-action, renforcement, injection plus riche  
- [ ] Phase 3 — Dégradation temporelle (non traumatique), corrélations  
- [ ] Phase 4 — Partage multi-nœuds / sync d’exposants  
- [ ] Finalité — compiler une LLM de base *autour* de ce socle (sens + mémoire)

## Origine

Né d’incidents réels (formatage / effacement EFI malgré des règles « INTERDIT »).
Récit complet dans le [whitepaper](whitepaper/MemorySystemAI_Whitepaper_v1.md).

## Licence

MIT — [LICENSE](LICENSE). Contributions : [CONTRIBUTING.md](CONTRIBUTING.md).

---

*« Je sais que je ne devrais pas » n’est pas la même chose que « je ne peux pas ».  
Sans sens et sans poids de mémoire, la génération n’est pas un système nerveux.*
