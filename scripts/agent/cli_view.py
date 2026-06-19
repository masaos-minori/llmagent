#!/usr/bin/env python3
"""cli_view.py
CLI presentation layer: readline setup, multiline continuation input,
and progress display.

Writer and Reader Protocols allow test doubles and alternative I/O backends
to replace the default terminal implementation without touching callers.
"""

import asyncio
import logging
import readline
from pathlib import Path
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Writer(Protocol):
    """Output-side interface for LLM streaming and status messages."""

    def write_token(self, token: str) -> None: ...
    def write_compress_notice(self, n: int) -> None: ...
    def write_turn_start(self) -> None: ...
    def write_turn_end(self) -> None: ...
    def write_llm_error(self, e: Exception) -> None: ...
    def write_progress(self, msg: str) -> None: ...
    def clear_progress(self) -> None: ...
    def write_warning(self, msg: str) -> None: ...
    def write_startup_banner(
        self, chunk_count: str, n_tools: int, workflow_status: str = ""
    ) -> None: ...


@runtime_checkable
class Reader(Protocol):
    """Input-side interface for multiline continuation prompts."""

    async def read_multiline(
        self,
        loop: asyncio.AbstractEventLoop,
        first_line: str,
    ) -> str: ...


class CLIView:
    """Manages terminal I/O: readline history, tab completion, multiline
    continuation input, and progress status line.
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
                logger.debug("Could not read history file: %s", e)

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
            logger.debug("Could not write history file: %s", e)

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

    def write_progress(self, msg: str) -> None:
        """Overwrite the current line with a progress indicator."""
        print(f"  [rag] {msg:<24}", end="\r", flush=True)

    def clear_progress(self) -> None:
        """Erase the progress line."""
        print(" " * 32, end="\r", flush=True)

    def write_warning(self, msg: str) -> None:
        """Print a startup or runtime warning prefixed with [warn]."""
        print(f"[warn] {msg}")

    def write_startup_banner(
        self, chunk_count: str, n_tools: int, workflow_status: str = ""
    ) -> None:
        """Print the agent startup line showing DB chunks, tool count, and workflow status."""
        print(f"DB: {chunk_count} chunks | Tools: {n_tools}")
        if workflow_status:
            print(f"Workflow: {workflow_status}")
        print("Type /help for commands, /exit to quit.")

    def write_debug_rag(self, data: dict) -> None:
        """Render structured RAG pipeline debug data to stdout."""
        rrf_config: dict = data.get("rrf_config", {})
        print(
            f"  [debug] RRF config: use_rrf={rrf_config.get('use_rrf', True)} "
            f"rrf_k={rrf_config.get('rrf_k', 60)}"
        )

        queries: list[str] = data.get("queries", [])
        all_results: list[list[dict]] = data.get("all_results", [])
        merged: list[dict] = data.get("merged", [])
        reranked: list[dict] = data.get("reranked", [])

        print(f"  [debug] MQE queries ({len(queries)}):")
        for i, q in enumerate(queries, 1):
            print(f"    {i}: {q}")

        total = sum(len(r) for r in all_results)
        print(
            f"  [debug] search: {len(all_results)} result lists,"
            f" {total} total candidates",
        )

        use_rrf = data.get("use_rrf", True)
        rrf_k = data.get("rrf_k", 60)
        print(f"  [debug] fusion: use_rrf={use_rrf} rrf_k={rrf_k}")
        print(f"  [debug] RRF merge: {len(merged)} unique candidates (top 5):")
        for c in merged[:5]:
            print(
                f"    chunk_id={c.get('chunk_id')}"
                f" rrf={c.get('rrf_score', 0):.4f}"
                f" url={str(c.get('url', ''))[:60]}",
            )

        print(f"  [debug] reranked top-{len(reranked)}:")
        for c in reranked:
            score = c.get("rerank_score", c.get("rrf_score", 0))
            print(
                f"    chunk_id={c.get('chunk_id')}"
                f" score={score:.4f}"
                f" url={str(c.get('url', ''))[:60]}",
            )

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
