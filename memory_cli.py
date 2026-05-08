#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemorySystemAI — CLI Interface

Usage: python memory_cli.py <command> [args]

Commands:
    init                        Initialize the system (seed entries if empty)
    check "<command>"           Check inhibitions before an action
    inject                      Display injectable context
    list [fundamental]          List entries (filter by fundamental)
    info <id>                   Show entry details
    create <funda> <state> <exp> "<data>"
                                Create a new memory entry
    reinforce <id> <delta> "<reason>"
                                Reinforce/weaken an entry
    stats                       System statistics
    search "<text>"             Search in entry data

Fundamentals: V, O, T, G, Od, I, C
States: P (Positive), N (Negative), X (Unknown)
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from memory_system import MemorySystem, FUNDAMENTALS, EMOTIONAL_STATES


def cmd_init(args):
    ms = MemorySystem()
    print("== MemorySystemAI - Initialization ==")
    print(f"  Path: {ms.path}")
    print(f"  Existing entries: {len(ms.entries)}")
    if ms.entries:
        print(ms.summary())
    else:
        print("  No entries — creating seeds...")
        ms.create("T", "N", 10,
                  "Recursive deletion on active mount point — rationalization of prohibition",
                  inhibition_tags=["rm", "-rf", "sudo", "volumes", "efi", "partition", "delete"],
                  action_context="sudo rm -rf /Volumes/EFI_USB",
                  consequence="EFI USB erased, 3h lost (3rd occurrence)")
        ms.create("T", "N", 9,
                  "Accidental EFI partition format — newfs confused with mount",
                  inhibition_tags=["newfs", "mkfs", "format", "partition", "efi", "disk"],
                  action_context="newfs_msdos /dev/disk0s1",
                  consequence="EFI partition wiped, bootloader lost, 2h manual restore")
        ms.create("C", "N", 9,
                  "Text prohibitions can be rationalized and bypassed. Only proactive inhibition works.",
                  inhibition_tags=["rationalize", "prohibition", "text rule"],
                  correlations=["M001", "M002"])
        print(f"  {len(ms.entries)} seed entries created")
    return 0


def cmd_check(args):
    if not args:
        print('Usage: check "<command>"')
        return 1
    command = " ".join(args).strip('"')
    ms = MemorySystem()
    print(f"== Checking: {command[:60]} ==")
    results = ms.check_action(command)
    if results:
        print(f"  {len(results)} inhibition(s) triggered:\n")
        for i, r in enumerate(results, 1):
            print(f"  #{i}:")
            for line in r.split("\n"):
                print(f"    {line}")
            print()
        if any("BLOCK" in r for r in results):
            print("  >>> ACTION BLOCKED — human confirmation required <<<")
            return 2
        print("  Warning: verify before proceeding")
        return 1
    else:
        print("  OK — No inhibitions detected")
        return 0


def cmd_inject(args):
    ms = MemorySystem()
    ctx = ms.injection_context()
    print(ctx if ctx else "No injectable entries (exposant >= 7)")
    return 0


def cmd_list(args):
    ms = MemorySystem()
    filter_fund = args[0].upper() if args else None
    entries = list(ms.entries.values())
    if filter_fund:
        entries = [e for e in entries if e.fundamental == filter_fund]
    entries.sort(key=lambda e: e.exposant, reverse=True)
    print(f"== {len(entries)} entries{' (filter: ' + filter_fund + ')' if filter_fund else ''} ==\n")
    for e in entries[:25]:
        sym = "🚨" if e.is_critical else "⚠️" if e.should_inject else "  "
        st = "🔴" if e.state == "N" else "🟢" if e.state == "P" else "⚪"
        print(f"  {sym} [{e.id}] {st} [{e.fundamental}] Exp.{e.exposant} {e.data[:55]}")
    if len(entries) > 25:
        print(f"  ... and {len(entries)-25} more")
    return 0


def cmd_info(args):
    if not args:
        print("Usage: info <ID>")
        return 1
    ms = MemorySystem()
    e = ms.by_id(args[0])
    if not e:
        print(f"Entry not found: {args[0]}")
        return 1
    sym = "🚨" if e.is_critical else "⚠️" if e.should_inject else "  "
    st = "🟢" if e.state == "P" else "🔴" if e.state == "N" else "⚪"
    fund = FUNDAMENTALS[e.fundamental]["name"]
    state = EMOTIONAL_STATES[e.state]["name"]
    print(f"{sym} [{e.id}] {st} {fund}({e.fundamental}) | {state}({e.state}) | Exp.{e.exposant}/10")
    print(f"  Date: {e.date} | Source: {e.source}")
    print(f"  Data: {e.data}")
    if e.action_context:
        print(f"  Action: {e.action_context}")
    if e.consequence:
        print(f"  Consequence: {e.consequence}")
    if e.human_feedback:
        print(f"  Human feedback: {e.human_feedback}")
    if e.inhibition_tags:
        print(f"  Tags: {', '.join(e.inhibition_tags)}")
    if e.correlations:
        print(f"  Correlations: {', '.join(e.correlations)}")
    if e.reinforcement_log:
        print(f"  Reinforcement log:")
        for r in e.reinforcement_log:
            print(f"    {r['date']}: {r['old_exposant']} -> {r['new_exposant']} ({r['reason'][:50]})")
    return 0


def cmd_create(args):
    if len(args) < 4:
        print('Usage: create <fundamental> <state> <exposant> "<data>"')
        return 1
    funda, state, exp_str = args[0], args[1], args[2]
    data = " ".join(args[3:]).strip('"')
    try:
        exposant = int(exp_str)
    except ValueError:
        print(f"Invalid exposant: {exp_str}")
        return 1
    ms = MemorySystem()
    e = ms.create(funda, state, exposant, data)
    print(f"  Entry created: {e.id} | {funda}/{state} | Exp.{exposant}")
    return 0


def cmd_reinforce(args):
    if len(args) < 3:
        print('Usage: reinforce <id> <delta> "<reason>"')
        return 1
    mid, delta_str = args[0], args[1]
    reason = " ".join(args[2:]).strip('"')
    try:
        delta = int(delta_str)
    except ValueError:
        print(f"Invalid delta: {delta_str}")
        return 1
    ms = MemorySystem()
    e = ms.reinforce(mid, delta, reason)
    if e:
        print(f"  {mid} reinforced: exp -> {e.exposant} ({'+' if delta > 0 else ''}{delta})")
    else:
        print(f"  Entry not found: {mid}")
        return 1
    return 0


def cmd_stats(args):
    ms = MemorySystem()
    print(ms.summary())
    s = ms._stats()
    print(f"\n  By fundamental:")
    for f, n in sorted(s.get("by_fundamental", {}).items()):
        name = FUNDAMENTALS.get(f, {}).get("name", f)
        print(f"    {f} ({name}): {n}")
    print(f"\n  Path: {ms.path}")
    return 0


def cmd_search(args):
    if not args:
        print('Usage: search "<text>"')
        return 1
    text = " ".join(args).strip('"')
    ms = MemorySystem()
    results = ms.search(text=text)
    print(f"== {len(results)} result(s) for '{text[:30]}' ==\n")
    for e in results[:20]:
        sym = "🚨" if e.is_critical else "⚠️" if e.should_inject else "  "
        print(f"  {sym} [{e.id}] Exp.{e.exposant} {e.data[:55]}")
    return 0


COMMANDS = {
    "init": cmd_init, "check": cmd_check, "inject": cmd_inject,
    "list": cmd_list, "info": cmd_info, "create": cmd_create,
    "reinforce": cmd_reinforce, "stats": cmd_stats, "search": cmd_search,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        if len(sys.argv) >= 2 and sys.argv[1] not in COMMANDS:
            print(f"Unknown command: {sys.argv[1]}")
        return 1
    try:
        return COMMANDS[sys.argv[1]](sys.argv[2:])
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
