"""
MemorySystemAI — Sensory-Emotional Memory System for AI
========================================================

A memory system that gives AI agents the ability to remember
traumatic experiences and automatically block dangerous actions.

Based on the MemorySystemAI v1 whitepaper.

Quick start:
    from MemorySystemAI import MemorySystem, check_before_action

    # Initialize
    ms = MemorySystem()

    # Check before a risky command
    inhibitions = check_before_action("sudo rm -rf /efi")
    # Returns list of inhibition messages if dangerous, empty if safe
"""

from .memory_system import (
    MemorySystem,
    MemoryEntry,
    FUNDAMENTALS,
    EMOTIONAL_STATES,
    THRESHOLD_RECORD,
    THRESHOLD_INJECT,
    THRESHOLD_BLOCK,
    init,
    check_before_action,
    is_blocked,
    learn,
    context,
    bulletin,
)

__version__ = "1.0.0"
__all__ = [
    "MemorySystem", "MemoryEntry",
    "FUNDAMENTALS", "EMOTIONAL_STATES",
    "THRESHOLD_RECORD", "THRESHOLD_INJECT", "THRESHOLD_BLOCK",
    "init", "check_before_action", "is_blocked", "learn", "context", "bulletin",
]
