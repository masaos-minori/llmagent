#!/usr/bin/env python3
"""scripts/agent/commands/command_defs.py

Declarative slash-command definition classes for CommandRegistry.

Owns:
  ArgSpec        — one argument of a command or subcommand (token, required, default)
  SubcommandSpec — metadata for one subcommand (name, help, arguments)
  CommandDef     — metadata for one slash command (name, prefix, is_async, handler, help,
                   arguments, subcommands)

Does NOT own:
  _COMMANDS — the list of all built-in slash commands is defined in
              agent.commands.command_defs_list.  To add or remove a built-in
              command, edit that module, not this one.

Import from here:  from agent.commands.command_defs import ArgSpec, CommandDef, SubcommandSpec
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ArgSpec:
    """One argument of a command or subcommand.

    token is the literal argument text without its brackets (e.g. "n",
    "markdown|json", "--branch <branch>"); required renders it as <token>,
    otherwise as [token]. default is the value used when an optional argument
    is omitted (None = no default).
    """

    token: str
    required: bool = False
    default: str | None = None

    def render(self) -> str:
        """Return the argument as it appears in a usage line."""
        return f"<{self.token}>" if self.required else f"[{self.token}]"


def format_usage(command: str, subcommand: str, args: tuple[ArgSpec, ...]) -> str:
    """Return the usage line, e.g. "/session list [n]"."""
    parts = [command, subcommand, *(a.render() for a in args)]
    return " ".join(p for p in parts if p)


@dataclass
class SubcommandSpec:
    """Declarative metadata for one subcommand."""

    name: str
    help: str
    args: tuple[ArgSpec, ...] = ()


@dataclass
class CommandDef:
    """Declarative metadata for one slash command."""

    name: str  # e.g. "/help"
    prefix: bool  # True = prefix match (args passed); False = exact match (no args)
    is_async: bool
    handler: str  # method name on CommandRegistry
    help: str  # one-line description shown in /help output
    subcommands: list[SubcommandSpec] = field(default_factory=list)
    args: tuple[ArgSpec, ...] = ()  # arguments of the command itself (no subcommand)

    def usages(self) -> list[str]:
        """Return every usage line of this command (subcommand forms, else the bare form)."""
        if self.subcommands:
            return [format_usage(self.name, s.name, s.args) for s in self.subcommands]
        return [format_usage(self.name, "", self.args)]


__all__ = ["ArgSpec", "CommandDef", "SubcommandSpec", "format_usage"]
