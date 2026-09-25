#!/usr/bin/env python3
"""scripts/agent/cli_view.py

CLI presentation layer: readline setup, multiline continuation input,
and progress display.

The Reader Protocol allows test doubles and alternative I/O backends
to replace the default terminal implementation without touching callers.
Writer functionality is now provided via delegation to an OutputPort instance.
"""

import asyncio
import concurrent.futures
import logging
import readline
from abc import ABC
from pathlib import Path
from typing import Protocol, runtime_checkable

from agent.commands.output_port import CliOutputPort, OutputPort

logger = logging.getLogger(__name__)

_INPUT_TIMEOUT_S = 30
_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class WriterBase(ABC):
    """Base class providing default implementations for output methods.

    Allows partial test doubles to satisfy the output interface without
    implementing all methods. Calling an unimplemented method raises
    NotImplementedError with a clear message.
    """

    def write_token(self, token: str) -> None:
        raise NotImplementedError("write_token must be implemented")

    def write_compress_notice(self, n: int) -> None:
        raise NotImplementedError("write_compress_notice must be implemented")

    def write_turn_start(self) -> None:
        raise NotImplementedError("write_turn_start must be implemented")

    def write_turn_end(self) -> None:
        raise NotImplementedError("write_turn_end must be implemented")

    def write_llm_error(self, e: Exception) -> None:
        raise NotImplementedError("write_llm_error must be implemented")

    def write_progress(self, msg: str) -> None:
        raise NotImplementedError("write_progress must be implemented")

    def clear_progress(self) -> None:
        raise NotImplementedError("clear_progress must be implemented")

    def write_warning(self, msg: str) -> None:
        raise NotImplementedError("write_warning must be implemented")

    def write_fatal(self, msg: str) -> None:
        raise NotImplementedError("write_fatal must be implemented")

    def write_startup_banner(
        self,
        chunk_count: str,
        n_tools: int,
        workflow_status: str = "",
        memory_mode: str | None = None,
    ) -> None:
        raise NotImplementedError("write_startup_banner must be implemented")


@runtime_checkable
class Reader(Protocol):
    """Input-side interface for multiline continuation prompts."""

    async def read_multiline(
        self,
        loop: asyncio.AbstractEventLoop,
        first_line: str,
    ) -> str:
        """Collect continuation lines when first_line ends with backslash."""
        ...


class CLIView(WriterBase):
    """Manages terminal I/O: readline history, tab completion, multiline
    continuation input, and progress status line.

    Delegates output operations to an OutputPort instance for separation of
    concerns between terminal management and output formatting.
    """

    HISTORY_FILE = Path.home() / ".agent_history"

    def __init__(
        self,
        slash_commands: list[str],
        port: OutputPort | None = None,
    ) -> None:
        """Initialize with available slash commands for tab completion.

        Args:
            slash_commands: Available slash commands for tab completion.
            port: OutputPort instance for delegating output operations.
                  Defaults to CliOutputPort if not provided.
        """
        self._slash_commands = slash_commands
        self._port = port or CliOutputPort()
        self._spinner_task: asyncio.Task[None] | None = None
        self._stop_spinner_event: asyncio.Event | None = None
        self._input_executor: concurrent.futures.ThreadPoolExecutor | None = None

    def __del__(self) -> None:
        """Clean up the input executor on garbage collection."""
        if self._input_executor is not None:
            self._input_executor.shutdown(wait=False)
            self._input_executor = None

    @property
    def port(self) -> OutputPort:
        """The OutputPort instance used for delegating output operations."""
        return self._port

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
            """Readline completer callback for slash commands."""
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
        self.stop_spinner()
        self._port.write_token(token)

    def write_compress_notice(self, n: int) -> None:
        """Notify the user that history was compressed."""
        self._port.write_compress_notice(n)

    def write_turn_start(self) -> None:
        """Print a blank line before each LLM streaming turn."""
        self._port.write_turn_start()

    def write_turn_end(self) -> None:
        """Print a blank line after the final LLM answer."""
        self._port.write_turn_end()

    def write_llm_error(self, e: Exception) -> None:
        """Notify the user of an LLM request failure."""
        self._port.write_llm_error(e)

    def write_progress(self, msg: str) -> None:
        """Overwrite the current line with a progress indicator."""
        self.stop_spinner()
        self._port.write_progress(msg)

    def clear_progress(self) -> None:
        """Erase the progress line."""
        self._port.clear_progress()

    async def start_spinner(self, msg: str = "Thinking") -> None:
        """Start an async spinner animation on the current line."""
        self.stop_spinner()
        self._stop_spinner_event = asyncio.Event()

        async def _spin() -> None:
            """Async spinner animation loop running on the current line."""
            assert self._stop_spinner_event is not None
            i = 0
            while not self._stop_spinner_event.is_set():
                frame = _SPINNER_FRAMES[i % len(_SPINNER_FRAMES)]
                print(f"\r  {frame} {msg}...", end="", flush=True)
                await asyncio.sleep(0.1)
                i += 1

        self._spinner_task = asyncio.create_task(_spin())

    def stop_spinner(self) -> None:
        """Stop the spinner and clear the line."""
        if self._spinner_task is not None and not self._spinner_task.done():
            assert self._stop_spinner_event is not None
            self._stop_spinner_event.set()
        print("\r" + " " * 40 + "\r", end="", flush=True)

    def write_warning(self, msg: str) -> None:
        """Print a startup or runtime warning prefixed with [warn]."""
        self._port.write_warning(msg)

    def write_fatal(self, msg: str) -> None:
        """Print a fatal error prefixed with [fatal]."""
        self._port.write_fatal(msg)

    def write_startup_banner(
        self,
        chunk_count: str,
        n_tools: int,
        workflow_status: str = "",
        memory_mode: str | None = None,
    ) -> None:
        """Print the agent startup line for display purposes."""
        self._port.write_startup_banner(
            chunk_count, n_tools, workflow_status, memory_mode
        )

    # --- OutputPort methods (delegated) ---

    def write(self, text: str) -> None:
        """Write plain text output."""
        self._port.write(text)

    def write_table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Write a formatted table with aligned columns."""
        self._port.write_table(headers, rows)

    def write_error(self, text: str) -> None:
        """Write an error message prefixed with '[error]'."""
        self._port.write_error(text)

    def write_success(self, text: str) -> None:
        """Write a success message prefixed with a space."""
        self._port.write_success(text)

    def write_no_data(self, text: str) -> None:
        """Write a no-data message prefixed with a space."""
        self._port.write_no_data(text)

    def write_validation_error(self, text: str) -> None:
        """Write a validation error message prefixed with '[usage]'."""
        self._port.write_validation_error(text)

    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None:
        """Write key-value pairs as aligned lines."""
        self._port.write_kv(pairs, key_width)

    def write_file(self, content: str, path: str, n_messages: int) -> None:
        """Write exported content to a file."""
        self._port.write_file(content, path, n_messages)

    def write_stderr(self, text: str) -> None:
        """Write text to stderr."""
        self._port.write_stderr(text)

    async def read_multiline(
        self,
        loop: asyncio.AbstractEventLoop,
        first_line: str,
    ) -> str:
        """Collect continuation lines when first_line ends with backslash.

        Strips the trailing backslash and joins all parts with newlines.
        Stops on a line without trailing backslash, an empty line, or EOF.

        Timeout protection: wraps the executor submission with asyncio.wait_for()
        to prevent indefinite hangs when the default ThreadPoolExecutor is
        saturated during shutdown. On TimeoutError, raises KeyboardInterrupt
        to allow user interruption rather than silently swallowing the error.
        """
        parts = [first_line[:-1]]
        while True:
            try:
                if self._input_executor is None:
                    self._input_executor = concurrent.futures.ThreadPoolExecutor(
                        max_workers=1
                    )
                future = self._input_executor.submit(lambda: input("... "))
                cont = await asyncio.wait_for(
                    asyncio.wrap_future(future), timeout=_INPUT_TIMEOUT_S
                )
            except TimeoutError:
                logger.warning("Multiline input timed out")
                raise KeyboardInterrupt
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
