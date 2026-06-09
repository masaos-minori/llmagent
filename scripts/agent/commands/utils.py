"""agent/commands/utils.py
Shared utilities for command mixins.

These helpers are used by multiple mixins and must not create circular imports.
"""

from __future__ import annotations

import logging

# Re-exported from agent.services.export_formatter for backward compatibility.
# New callers should import directly from agent.services.export_formatter.
from agent.services.export_formatter import (
    render_export,
    render_history_md,
    write_export,
)

logger = logging.getLogger(__name__)

__all__ = [
    "parse_flag_int",
    "parse_flag_str",
    "render_export",
    "render_history_md",
    "write_export",
]


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
