#!/usr/bin/env python3
"""scripts/agent/commands/registry.py

Slash-command registry for AgentREPL.

CommandRegistry inherits command groups from mixin classes.
All _cmd_* methods operate solely on AgentContext injected in __init__,
with no dependency on AgentREPL itself.

Mixins (keep in sync with CommandRegistry base class list):
  cmd_session.py    — _SessionMixin:    /session commands
  cmd_mcp.py        — _McpMixin:        /mcp commands
  cmd_config.py     — _ConfigMixin:     /config, /stats, /reload
   cmd_context.py    — _ContextMixin:    /context, /clear, /undo, /history
   cmd_tooling.py    — _ToolingMixin:    /plan
  cmd_debug.py      — _DebugMixin:      /debug
  cmd_rag_export.py — _RagExportMixin:  /compact
  cmd_memory.py     — _MemoryMixin:     /memory

_COMMANDS ownership:
  _COMMANDS is IMPORTED from agent.commands.command_defs_list.
  It is NOT defined in this module.
  This module owns: dispatch behavior (dispatch(), _get_handler())
                    and the fail-fast handler validation in __init__.
"""

import logging
import sqlite3
from collections.abc import Callable
from typing import Any

from agent.commands.cmd_config import _ConfigMixin
from agent.commands.cmd_context import _ContextMixin
from agent.commands.cmd_debug import _DebugMixin
from agent.commands.cmd_mcp import _McpMixin
from agent.commands.cmd_memory import _MemoryMixin
from agent.commands.cmd_rag_export import _RagExportMixin
from agent.commands.cmd_session import _SessionMixin
from agent.commands.cmd_tooling import _ToolingMixin
from agent.commands.command_defs import CommandDef
from agent.commands.command_defs_list import _COMMANDS
from agent.commands.exceptions import CommandParseError, CommandValidationError
from agent.commands.output_port import CliOutputPort, OutputPort
from agent.context import AgentContext

__all__ = ["CommandRegistry"]

logger = logging.getLogger(__name__)


class CommandRegistry(
    _SessionMixin,
    _McpMixin,
    _ConfigMixin,
    _ContextMixin,
    _ToolingMixin,
    _DebugMixin,
    _RagExportMixin,
    _MemoryMixin,
):
    """Slash-command dispatcher for AgentREPL.

    All _cmd_* methods operate solely on AgentContext injected in __init__,
    with no dependency on AgentREPL itself.
    """

    def __init__(self, ctx: AgentContext, out: OutputPort | None = None) -> None:
        """Initialize the command registry with context, output port, and handler validation."""
        self._ctx = ctx
        self._out: OutputPort = out if out is not None else CliOutputPort()
        super().__init__(ctx, out)
        # Fail-fast: validate all handler strings refer to existing methods.
        for _cmd in _COMMANDS:
            if not hasattr(self, _cmd.handler):
                raise AttributeError(
                    f"CommandDef references unknown handler: {_cmd.handler!r}"
                )

    def _get_handler(self, cmd: CommandDef) -> Callable[..., Any]:
        """Return the bound callable for cmd.handler; raises AttributeError if missing."""
        handler = getattr(self, cmd.handler, None)
        if handler is None:
            raise AttributeError(
                f"CommandRegistry has no handler method {cmd.handler!r}"
            )
        return handler  # type: ignore[no-any-return]

    def _cmd_help(self) -> None:
        """Print help and available tool count."""

        ctx = self._ctx
        n_tools = len(ctx.cfg.tool.tool_definitions)
        sid = (
            f"session {ctx.session.session_id}"
            if ctx.session.session_id
            else "no session"
        )
        self._out.write("Agent REPL — type a question and press Enter.")
        self._out.write("Conversation history is preserved within the session.")
        self._out.write("")
        self._out.write("Slash commands:")
        for cmd in _COMMANDS:
            self._out.write(f"  {cmd.name:<22} {cmd.help}")
        self._out.write("")
        self._out.write("REPL control commands:")
        self._out.write("  /exit                       Exit the REPL")
        self._out.write("")
        self._out.write(f"Tools: {n_tools}  |  LLM: {ctx.cfg.llm.llm_url}  |  {sid}")

    @staticmethod
    async def _invoke_handler(
        handler: Callable[..., Any], cmd: CommandDef, *args: str
    ) -> None:
        """Call handler with args, awaiting it when cmd.is_async."""
        if cmd.is_async:
            await handler(*args)
        else:
            handler(*args)

    async def _run_matched_command(
        self, handler: Callable[..., Any], cmd: CommandDef, *args: str
    ) -> bool:
        """Invoke a matched handler, surfacing its errors at the command boundary.

        Wraps the invocation in a single ``except Exception`` branch so a failing
        slash command renders as a command-scoped ``[error]``/``[usage]`` tag and
        returns ``True`` (matched) instead of propagating to the REPL loop's
        turn-level ``[fatal]`` path. ``BaseException`` (e.g.
        ``asyncio.CancelledError``, ``KeyboardInterrupt``) keeps propagating.
        """
        try:
            await self._invoke_handler(handler, cmd, *args)
        except Exception as exc:  # noqa: BLE001 — command-boundary error surface; never swallow BaseException
            self._emit_command_error(cmd, exc)
        return True

    def _emit_command_error(self, cmd: CommandDef, exc: Exception) -> None:
        """Render and log a handler exception as a command-scoped error.

        ``CommandValidationError``/``CommandParseError`` (and subclasses) render as
        ``[usage]``; ``sqlite3.Error`` and any other exception render as ``[error]``
        with an explicit partial-effect note for the database case.
        """
        if isinstance(exc, (CommandValidationError, CommandParseError)):
            self._out.write_validation_error(str(exc))
        elif isinstance(exc, sqlite3.Error):
            self._out.write_error(f"{cmd.name}: {exc} — the effect may be partial")
        else:
            self._out.write_error(str(exc))
        logger.error("command %s failed: %s: %s", cmd.name, exc.__class__.__name__, exc)

    async def dispatch(self, line: str) -> bool:
        """Dispatch a slash command; return True if matched, False otherwise.

        Commands are looked up in _COMMANDS. Prefix commands use exact boundary
        matching (line == name or line.startswith(name + " ")) to prevent
        substring false-positives.
        """
        if not isinstance(line, str):
            raise TypeError(f"dispatch() requires str, got {type(line).__name__}")
        if not line:
            return False
        for cmd in _COMMANDS:
            handler = self._get_handler(cmd)
            if cmd.prefix:
                if line == cmd.name or line.startswith(cmd.name + " "):
                    args = line[len(cmd.name) :].strip()
                    return await self._run_matched_command(handler, cmd, args)
            else:
                if line == cmd.name:
                    return await self._run_matched_command(handler, cmd)

        return False
