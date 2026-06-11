"""agent/commands/output_port.py
OutputPort Protocol and CliOutputPort implementation for command handlers.
"""

from __future__ import annotations

from typing import Protocol


class OutputPort(Protocol):
    def write(self, text: str) -> None: ...
    def write_table(self, headers: list[str], rows: list[list[str]]) -> None: ...
    def write_error(self, text: str) -> None: ...
    def write_success(self, text: str) -> None: ...
    def write_no_data(self, text: str) -> None: ...
    def write_validation_error(self, text: str) -> None: ...
    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None: ...


class CliOutputPort:
    """Concrete OutputPort that writes to stdout via print()."""

    def write(self, text: str) -> None:
        print(text)

    def write_success(self, text: str) -> None:
        print(f"  {text}")

    def write_error(self, text: str) -> None:
        print(f"  [error] {text}")

    def write_no_data(self, text: str) -> None:
        print(f"  {text}")

    def write_validation_error(self, text: str) -> None:
        print(f"  [usage] {text}")

    def write_table(self, headers: list[str], rows: list[list[str]]) -> None:
        if not rows:
            return
        widths = [
            max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
        ]
        header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_line)
        print("-" * len(header_line))
        for row in rows:
            print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))

    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None:
        for k, v in pairs:
            print(f"  {k:<{key_width}}: {v}")
