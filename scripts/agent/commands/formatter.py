"""agent/commands/formatter.py
Shared output helpers for command mixins.

All display output from command handlers should go through these functions
to ensure consistent formatting across commands.
"""

from __future__ import annotations


def print_success(msg: str) -> None:
    """Print a success message."""
    print(f"  {msg}")


def print_error(msg: str) -> None:
    """Print an error message."""
    print(f"  [error] {msg}")


def print_no_data(msg: str) -> None:
    """Print a no-data / empty-result message."""
    print(f"  {msg}")


def print_validation_error(msg: str) -> None:
    """Print a usage / validation error message."""
    print(f"  [usage] {msg}")


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a plain-text table with auto-sized columns."""
    if not rows:
        return
    widths = [max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))


def print_kv_list(pairs: list[tuple[str, str]], key_width: int = 22) -> None:
    """Print a key-value list with aligned colons."""
    for k, v in pairs:
        print(f"  {k:<{key_width}}: {v}")
