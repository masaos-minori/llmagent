#!/usr/bin/env python3
"""agent/commands/command_defs.py
Declarative slash-command definition classes for CommandRegistry.

Provides:
  SubcommandSpec — metadata for one subcommand
  CommandDef     — metadata for one slash command

Import from here:  from agent.commands.command_defs import CommandDef, SubcommandSpec
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SubcommandSpec:
    """Declarative metadata for one subcommand."""

    name: str
    help: str


@dataclass
class CommandDef:
    """Declarative metadata for one slash command."""

    name: str  # e.g. "/help"
    prefix: bool  # True = prefix match (args passed); False = exact match (no args)
    is_async: bool
    handler: str  # method name on CommandRegistry
    help: str  # one-line description shown in /help output
    subcommands: list[SubcommandSpec] = field(default_factory=list)


__all__ = ["CommandDef", "SubcommandSpec"]
