"""agent/commands/output_port.py

OutputPort Protocol and CliOutputPort implementation for command handlers.
"""

from __future__ import annotations

from typing import Protocol

from agent.output_tags import OutputTag


class OutputPort(Protocol):
    """Interface for writing structured output from slash commands."""

    def write(self, text: str) -> None:
        """Write plain text output."""
        ...

    def write_table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Write a formatted table with aligned columns."""
        ...

    def write_error(self, text: str) -> None:
        """Write an error message prefixed with '[error]'."""
        ...

    def write_success(self, text: str) -> None:
        """Write a success message prefixed with a space."""
        ...

    def write_no_data(self, text: str) -> None:
        """Write a no-data message prefixed with a space."""
        ...

    def write_validation_error(self, text: str) -> None:
        """Write a validation error message prefixed with '[usage]'."""
        ...

    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None:
        """Write key-value pairs as aligned lines."""
        ...


class CliOutputPort:
    """Concrete OutputPort that writes to stdout via print()."""

    def write(self, text: str) -> None:
        """Write plain text output."""
        print(text)

    def write_success(self, text: str) -> None:
        """Write a success message prefixed with a space."""
        print(f"  {text}")

    def write_error(self, text: str) -> None:
        """Write an error message prefixed with '[error]'."""
        print(f"  {OutputTag.ERROR} {text}")

    def write_no_data(self, text: str) -> None:
        """Write a no-data message prefixed with a space."""
        print(f"  {text}")

    def write_validation_error(self, text: str) -> None:
        """Write a validation error message prefixed with '[usage]'."""
        print(f"  {OutputTag.USAGE} {text}")

    def write_table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Write a formatted table with aligned columns."""
        if not rows:
            return
        expected = len(headers)
        for idx, row in enumerate(rows):
            if len(row) != expected:
                raise ValueError(
                    f"write_table: row {idx} has {len(row)} cells, expected {expected}"
                )
        widths = [
            max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
        ]
        header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_line)
        print("-" * len(header_line))
        for row in rows:
            print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))

    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None:
        """Write key-value pairs as aligned lines."""
        for k, v in pairs:
            print(f"  {k:<{key_width}}: {v}")
