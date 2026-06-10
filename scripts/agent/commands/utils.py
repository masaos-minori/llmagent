"""agent/commands/utils.py
Shared utilities for command mixins.

These helpers are used by multiple mixins and must not create circular imports.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

# Re-exported from agent.services.export_formatter for backward compatibility.
# New callers should import directly from agent.services.export_formatter.
from agent.services.export_formatter import (
    render_export,
    render_history_md,
    write_export,
)

logger = logging.getLogger(__name__)

__all__ = [
    "ParsedArgs",
    "parse_command_args",
    "parse_flag_int",
    "parse_flag_str",
    "render_export",
    "render_history_md",
    "write_export",
]


@dataclass
class ParsedArgs:
    """Structured result of command argument parsing."""

    subcommand: str | None = None
    positional: list[str] = field(default_factory=list)
    flags: dict[str, str | bool] = field(default_factory=dict)
    error: str | None = None  # None = parse success


def parse_command_args(tokens: list[str]) -> ParsedArgs:
    """Parse command tokens into a structured ParsedArgs.

    First non-flag token is the subcommand; subsequent non-flag tokens are positional.
    --flag value pairs populate flags; bare --flag sets the flag to True.
    """
    result = ParsedArgs()
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("--"):
            key = t[2:]
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                result.flags[key] = tokens[i + 1]
                i += 2
            else:
                result.flags[key] = True
                i += 1
        elif result.subcommand is None:
            result.subcommand = t
            i += 1
        else:
            result.positional.append(t)
            i += 1
    return result


def parse_flag_int(tokens: list[str], flag: str) -> int | None:
    """Return the integer value following `flag` in tokens, or None."""
    for i, t in enumerate(tokens):
        if t == flag and i + 1 < len(tokens):
            try:
                return int(tokens[i + 1])
            except ValueError:
                pass
    return None


def parse_flag_str(tokens: list[str], flag: str) -> str | None:
    """Return the string value following `flag` in tokens, or None."""
    for i, t in enumerate(tokens):
        if t == flag and i + 1 < len(tokens):
            return tokens[i + 1]
    return None
