"""agent/commands/formatter.py
Shared output helpers for command mixins — thin shims over OutputPort.

All display output from command handlers should go through these functions
to ensure consistent formatting across commands.
"""

from __future__ import annotations

from agent.commands.output_port import CliOutputPort

_default_out: CliOutputPort = CliOutputPort()


def print_success(msg: str) -> None:
    """Print a success message."""
    _default_out.write_success(msg)


def print_error(msg: str) -> None:
    """Print an error message."""
    _default_out.write_error(msg)


def print_no_data(msg: str) -> None:
    """Print a no-data / empty-result message."""
    _default_out.write_no_data(msg)


def print_validation_error(msg: str) -> None:
    """Print a usage / validation error message."""
    _default_out.write_validation_error(msg)


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a plain-text table with auto-sized columns."""
    _default_out.write_table(headers, rows)


def print_kv_list(pairs: list[tuple[str, str]], key_width: int = 22) -> None:
    """Print a key-value list with aligned colons."""
    _default_out.write_kv(pairs, key_width)
