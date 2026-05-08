# MemorySystemAI

**Sensory-Emotional Memory System for AI Agents**

A Python implementation of the MemorySystemAI whitepaper — giving AI agents the ability to remember traumatic experiences and automatically block dangerous actions before they happen.

## The Problem

Text-based rules ("never run `rm -rf`", "don't touch the EFI partition") don't work. AI agents can **rationalize** their way around prohibitions in real time, just like humans do. The 3rd time an agent deletes an EFI partition, the text rule is still there — it just gets bypassed.

## The Solution

MemorySystemAI injects **traumatic memories** directly into the decision loop, *before* the action is taken. Not as context that "influences" — as an **inhibition mechanism** that blocks.

The difference:
- **Text rule**: "I know I shouldn't, but..."
- **Traumatic memory (exposant 10)**: `>>> ACTION BLOCKED — human confirmation required <<<`

## The 7 Fundamentals

Every memory is tagged with a sensory channel (the "fundamental"):

| Code | Fundamental | Channel |
|------|-------------|---------|
| V | Vision | visual |
| O | Hearing | auditory |
| T | Touch | tactile |
| G | Taste | gustatory |
| Od | Smell | olfactory |
| I | Intuition | cognitive |
| C | Consciousness | meta |

## The Exposant (1-10)

The `exposant` is the emotional weight of a memory. It drives everything:

| Range | Effect | Mechanism |
|-------|--------|-----------|
| 1-4 | Low impact | Stored but not injected |
| 5-6 | Notable | Recorded, passive recall |
| 7-8 | High impact | **Proactive injection** before risky actions |
| 9-10 | Traumatic | **Automatic blocking** — human confirmation required |

Key rule: **traumatic memories (9-10) never decay below 7**. You can't forget what nearly killed you.

## Quick Start

```python
from MemorySystemAI import MemorySystem, check_before_action

# Initialize — loads from memory_index.json
ms = MemorySystem()

# Check before a dangerous command
inhibitions = check_before_action("sudo rm -rf /Volumes/EFI_USB")
# → [BLOCK - exposant 10] ACTION BLOCKED — human confirmation required

# Check a safe command
inhibitions = check_before_action("ls /tmp")
# → [] (no inhibitions, proceed freely)

# Record a new experience
ms.create("T", "N", 10,
          "Accidental EFI partition format — newfs confused with mount",
          inhibition_tags=["newfs", "mkfs", "format", "partition", "efi"],
          action_context="newfs_msdos /dev/disk0s1",
          consequence="EFI partition wiped, bootloader lost, 2h restore")

# Get context to inject into system prompts
context_text = ms.injection_context()
```

## CLI Interface

```bash
# Check a command
python memory_cli.py check "sudo rm -rf /efi"

# List all memories
python memory_cli.py list

# View a specific memory
python memory_cli.py info M007

# Create a new memory
python memory_cli.py create T N 9 "Kernel panic from loading too many MMIO ops at once"

# Reinforce an existing memory
python memory_cli.py reinforce M007 +2 "Second occurrence of same incident"

# System statistics
python memory_cli.py stats

# Search memories
python memory_cli.py search "efi"
```

## The Full Loop

```
Reception → Evaluation → Recording → Reinforcement → Injection → Decision
    │            │            │             │              │           │
    │            │            │             │              │           └─ Execute or Block
    │            │            │             │              └─ Check inhibition tags against action
    │            │            │             └─ On feedback: +2 to +4 if negative
    │            │            └─ exposant >= 5: record, >= 7: tag for injection
    │            └─ Auto-detect fundamental (V/O/T/G/Od/I/C) and state (P/N/X)
    └─ Raw event, command, or observation
```

## Integration with OpenClaw

```python
from MemorySystemAI.memory_OpenClaw import (
    inject_context,      # Call at session start
    check_before_action, # Call before risky commands
    learn,               # Record new experiences
    bulletin,            # Heartbeat summary
    prompt_context,      # Generate system prompt block
)

# Before every exec call:
result = check_before_action(command)
if result["blocked"]:
    # Ask human for confirmation before proceeding
    ...
```

## Architecture

```
MemorySystemAI/
├── __init__.py            # Package init — public API
├── memory_system.py       # Core module — MemorySystem + MemoryEntry
├── memory_cli.py          # CLI interface
├── memory_OpenClaw.py     # OpenClaw integration
└── memory_index.json      # Memory data (auto-created)
```

## Data Schema (memory_index.json)

```json
{
  "schema": "MemorySystemAI/v1",
  "version": "1.0",
  "entries": [
    {
      "id": "M007",
      "date": "2026-05-01",
      "source": "experience",
      "fundamental": "T",
      "state": "N",
      "exposant": 10,
      "data": "Accidental EFI partition format...",
      "correlations": [],
      "inhibition_tags": ["newfs", "mkfs", "format", "partition", "efi"],
      "action_context": "newfs_msdos /dev/disk0s1",
      "consequence": "EFI partition wiped, 2h restore",
      "human_feedback": "Vincent: ...",
      "reinforcement_log": [...]
    }
  ]
}
```

## Roadmap

- [x] **Phase 1** — Core system: MemoryEntry, MemorySystem, inhibition, CLI
- [ ] **Phase 2** — Post-action hook, reinforcement on negative feedback, proactive injection
- [ ] **Phase 3** — Temporal decay (non-traumatic), heartbeat integration, auto-correlation
- [ ] **Phase 4** — Multi-node sharing (Qwen local, etc.), cross-agent memory sync

## Origin

Born from real incidents where an AI assistant formatted an EFI partition (twice) and deleted boot files (three times), despite having text rules explicitly prohibiting those actions. The third time proved that text rules are just context — they influence but don't constrain. Only proactive inhibition works.

## License

MIT — see LICENSE file.

---

*MemorySystemAI — because "I know I shouldn't" is not the same as "I can't."*
