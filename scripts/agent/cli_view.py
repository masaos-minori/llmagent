#!/usr/bin/env python3
"""cli_view.py
CLI presentation layer: readline setup, multiline continuation input,
and RAG pipeline progress display.
"""

import asyncio
import logging
import readline
from pathlib import Path

logger = logging.getLogger(__name__)


class CLIView:
    """Manages terminal I/O: readline history, tab completion, multiline
    continuation input, and RAG pipeline progress status line.
    """

    HISTORY_FILE = Path.home() / ".agent_history"

    def __init__(self, slash_commands: list[str]) -> None:
        self._slash_commands = slash_commands

    def setup_readline(self) -> None:
        """Configure readline for bash-equivalent editing and tab completion."""
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set editing-mode emacs")
        readline.set_history_length(1000)

        if self.HISTORY_FILE.exists():
            try:
                readline.read_history_file(str(self.HISTORY_FILE))
            except OSError as e:
                logger.debug(f"Could not read history file: {e}")

        cmds = self._slash_commands

        def _completer(text: str, state: int) -> str | None:
            options = [c for c in cmds if c.startswith(text)]
            return options[state] if state < len(options) else None

        readline.set_completer(_completer)
        # Delimit only on whitespace so slash commands complete correctly
        readline.set_completer_delims(" \t\n")

    def write_history(self) -> None:
        """Persist readline history to disk."""
        try:
            readline.write_history_file(str(self.HISTORY_FILE))
        except OSError as e:
            logger.debug(f"Could not write history file: {e}")

    def write_token(self, token: str) -> None:
        """Write one streaming token to stdout without a trailing newline."""
        print(token, end="", flush=True)

    def write_compress_notice(self, n: int) -> None:
        """Notify the user that history was compressed."""
        print(f"  [context] history compressed ({n} messages summarized)")

    def write_turn_start(self) -> None:
        """Print a blank line before each LLM streaming turn."""
        print()

    def write_turn_end(self) -> None:
        """Print a blank line after the final LLM answer."""
        print()

    def write_llm_error(self, e: Exception) -> None:
        """Notify the user of an LLM request failure."""
        print(f"\nError: {e}\n")

    def rag_status(self, msg: str) -> None:
        """Overwrite the current line with a RAG progress indicator."""
        print(f"  [rag] {msg:<24}", end="\r", flush=True)

    def rag_clear(self) -> None:
        """Erase the RAG progress line."""
        print(" " * 32, end="\r", flush=True)

    async def read_multiline(
        self,
        loop: asyncio.AbstractEventLoop,
        first_line: str,
    ) -> str:
        """Collect continuation lines when first_line ends with backslash.

        Strips the trailing backslash and joins all parts with newlines.
        Stops on a line without trailing backslash, an empty line, or EOF.
        """
        parts = [first_line[:-1]]
        while True:
            try:
                cont = await loop.run_in_executor(None, lambda: input("... "))
            except (EOFError, KeyboardInterrupt):
                break
            if not cont:
                break
            if cont.endswith("\\"):
                parts.append(cont[:-1])
            else:
                parts.append(cont)
                break
        return "\n".join(parts)
