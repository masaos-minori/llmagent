"""scripts/agent/commands/utils.py

Shared utilities for command mixins.

These helpers are used by multiple mixins and must not create circular imports.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from agent.commands.exceptions import CommandValidationError

logger = logging.getLogger(__name__)

__all__ = [
    "ParsedArgs",
    "parse_command_args",
    "parse_int_arg",
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


def parse_int_arg(
    raw: str | bool | None,
    *,
    usage: str,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    """Parse a command argument into an int, raising on invalid or out-of-range input.

    `raw is None` means the argument was absent -> return `default`. A present-but-invalid
    value raises `CommandValidationError` (mapped to `[usage]` by dispatch()); a bare
    `--flag` (True) also raises. `minimum`/`maximum` are inclusive bounds.
    """
    if raw is None:
        return default
    if isinstance(raw, bool):
        # A bare --flag sets the flag to True; int(True) == 1 would silently accept it.
        # Reject it so the command renders a usage error (AC-1), not a parsed 1.
        raise CommandValidationError(usage)
    try:
        value = int(raw)
    except (ValueError, TypeError):
        raise CommandValidationError(usage) from None
    if minimum is not None and value < minimum:
        raise CommandValidationError(usage)
    if maximum is not None and value > maximum:
        raise CommandValidationError(usage)
    return value
