"""scripts/agent/commands/output_port.py

OutputPort Protocol and CliOutputPort implementation for command handlers.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agent.output_tags import OutputTag


@runtime_checkable
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

    # --- Writer Protocol methods (merged) ---

    def write_token(self, token: str) -> None:
        """Write one streaming token to stdout without a trailing newline."""
        ...

    def write_compress_notice(self, n: int) -> None:
        """Notify the user that history was compressed."""
        ...

    def write_turn_start(self) -> None:
        """Print a blank line before each LLM streaming turn."""
        ...

    def write_turn_end(self) -> None:
        """Print a blank line after the final LLM answer."""
        ...

    def write_llm_error(self, e: Exception) -> None:
        """Notify the user of an LLM request failure."""
        ...

    def write_progress(self, msg: str) -> None:
        """Overwrite the current line with a progress indicator."""
        ...

    def clear_progress(self) -> None:
        """Erase the progress line."""
        ...

    def write_warning(self, msg: str) -> None:
        """Print a startup or runtime warning prefixed with [warn]."""
        ...

    def write_fatal(self, msg: str) -> None:
        """Print a fatal error prefixed with [fatal]."""
        ...

    def write_startup_banner(
        self,
        chunk_count: str,
        n_tools: int,
        workflow_status: str = "",
        memory_mode: str | None = None,
    ) -> None:
        """Print the agent startup line for display purposes."""
        ...

    # --- ExportOutputPort Protocol methods (merged) ---

    def write_file(self, content: str, path: str, n_messages: int) -> None:
        """Write exported content to a file."""
        ...

    # --- Additional method ---

    def write_stderr(self, text: str) -> None:
        """Write text to stderr."""
        ...


class CliOutputPort:
    """Concrete OutputPort that writes to stdout via print().

    Implements the unified OutputPort Protocol including merged Writer and
    ExportOutputPort Protocol methods.
    """

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
            # Output headers only when there are no rows
            widths = [max(len(h), 0) for h in headers]
            header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
            print(header_line)
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

    # --- Writer Protocol methods (merged) ---

    def write_token(self, token: str) -> None:
        """Write one streaming token to stdout without a trailing newline."""
        print(token, end="", flush=True)

    def write_compress_notice(self, n: int) -> None:
        """Notify the user that history was compressed."""
        print(f"  {OutputTag.CONTEXT} history compressed ({n} messages summarized)")

    def write_turn_start(self) -> None:
        """Print a blank line before each LLM streaming turn."""
        print()

    def write_turn_end(self) -> None:
        """Print a blank line after the final LLM answer."""
        print()

    def write_llm_error(self, e: Exception) -> None:
        """Notify the user of an LLM request failure."""
        print(f"\n{OutputTag.ERROR} {e}\n")

    def write_progress(self, msg: str) -> None:
        """Overwrite the current line with a progress indicator."""
        print(f"  {msg:<24}", end="\r", flush=True)

    def clear_progress(self) -> None:
        """Erase the progress line."""
        print(" " * 32, end="\r", flush=True)

    def write_warning(self, msg: str) -> None:
        """Print a startup or runtime warning prefixed with [warn]."""
        print(f"{OutputTag.WARN} {msg}")

    def write_fatal(self, msg: str) -> None:
        """Print a fatal error prefixed with [fatal]."""
        print(f"{OutputTag.FATAL} {msg}")

    def write_startup_banner(
        self,
        chunk_count: str,
        n_tools: int,
        workflow_status: str = "",
        memory_mode: str | None = None,
    ) -> None:
        """Print the agent startup line for display purposes."""
        print(f"DB: {chunk_count} chunks | Tools: {n_tools}")
        if memory_mode is not None:
            print(f"Memory: {memory_mode}")
        if workflow_status:
            print(f"Workflow: {workflow_status}")
        print("Type /help for commands, /exit to quit.")

    # --- ExportOutputPort Protocol methods (merged) ---

    def write_file(self, content: str, path: str, n_messages: int) -> None:
        """Write exported content to a file."""
        with open(path, "w") as f:
            f.write(content)
        print(f"Exported {n_messages} messages to {path}")

    # --- Additional method ---

    def write_stderr(self, text: str) -> None:
        """Write text to stderr."""
        import sys

        sys.stderr.write(text)
