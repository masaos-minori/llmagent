#!/usr/bin/env python3
"""registry.py
Slash-command registry for AgentREPL.

CommandRegistry inherits command groups from mixin classes.
All _cmd_* methods operate solely on AgentContext injected in __init__,
with no dependency on AgentREPL itself.

Mixin split:
  cmd_session.py  — _SessionMixin:  /session commands
  cmd_mcp.py      — _McpMixin:      /mcp commands
  cmd_config.py   — _ConfigMixin:   /config, /stats, /set, /reload
  cmd_context.py  — _ContextMixin:  /context, /clear, /undo, /history, /system
  cmd_db.py       — _DbMixin:       /db
  cmd_tooling.py  — _ToolingMixin:  /tool, /plan
 cmd_debug.py    — _DebugMixin:    /debug
  cmd_ingest.py   — _IngestMixin:   /ingest, /export, /compact
  cmd_memory.py   — _MemoryMixin:   /memory
  cmd_mdq.py      — _MdqMixin:      /mdq commands
"""

import asyncio
from collections.abc import Awaitable, Callable

from shared import plugin_registry

from agent.commands.cmd_audit import _AuditMixin
from agent.commands.cmd_config import _ConfigMixin
from agent.commands.cmd_context import _ContextMixin
from agent.commands.cmd_db import _DbMixin
from agent.commands.cmd_debug import _DebugMixin
from agent.commands.cmd_ingest import _IngestMixin
from agent.commands.cmd_mcp import _McpMixin
from agent.commands.cmd_mdq import _MdqMixin
from agent.commands.cmd_memory import _MemoryMixin
from agent.commands.cmd_plugins import _PluginsMixin
from agent.commands.cmd_session import _SessionMixin
from agent.commands.cmd_tooling import _ToolingMixin
from agent.commands.cmd_workflow import _WorkflowMixin
from agent.commands.command_defs import CommandDef
from agent.commands.output_port import CliOutputPort, OutputPort
from agent.context import AgentContext

__all__ = ["CommandRegistry"]


# Single source of truth for all built-in slash commands.
# Exact-match commands are listed first, followed by prefix commands.
_COMMANDS: list[CommandDef] = [
    # ── Exact-match sync ─────────────────────────────────────────────────────
    CommandDef("/help", False, False, "_cmd_help", "Show this help"),
    CommandDef(
        "/config",
        False,
        False,
        "_cmd_config",
        "Current configuration and config file paths",
    ),
    CommandDef(
        "/stats",
        False,
        False,
        "_cmd_stats",
        "Session statistics (turns, tool calls, RAG hits, error counts)",
    ),
    CommandDef(
        "/context",
        False,
        False,
        "_cmd_context",
        "Runtime context state (messages, chars, compression, system prompt)",
    ),
    CommandDef("/plan", False, False, "_cmd_plan", "Toggle plan mode"),
    CommandDef(
        "/undo", False, False, "_cmd_undo", "Roll back the last user+assistant turn"
    ),
    CommandDef(
        "/reload",
        False,
        False,
        "_cmd_reload",
        "Reload all config/*.toml files and apply runtime-configurable parameters",
    ),
    # ── Exact-match async ────────────────────────────────────────────────────
    CommandDef(
        "/compact",
        False,
        True,
        "_cmd_compact",
        "Force immediate compression of conversation history",
    ),
    # ── Prefix sync ──────────────────────────────────────────────────────────
    CommandDef(
        "/mcp",
        True,
        True,
        "_cmd_mcp",
        "MCP server status, tool list, connectivity check",
    ),
    CommandDef(
        "/session",
        True,
        False,
        "_cmd_session",
        "list [n] | load <id> | rename <title> | delete <id>",
    ),
    CommandDef(
        "/clear",
        True,
        False,
        "_cmd_clear",
        "Reset conversation history; 'new' also starts a new session",
    ),
    CommandDef(
        "/ingest",
        True,
        True,
        "_cmd_ingest",
        "<url|path> [--snippets-only]  Crawl/ingest a URL or local file into the RAG DB",
    ),
    CommandDef(
        "/rag",
        True,
        True,
        "_cmd_rag",
        "search <query> [--debug]  Search the RAG knowledge base",
    ),
    CommandDef(
        "/export",
        True,
        False,
        "_cmd_export",
        "[md|json] [file]  Export conversation history (default: md to stdout)",
    ),
    CommandDef(
        "/history",
        True,
        False,
        "_cmd_history",
        "[n]  Show last N user/assistant messages (default: 5)",
    ),
    CommandDef(
        "/system",
        True,
        False,
        "_cmd_system",
        "[name]  Switch system prompt preset; list presets if no name given",
    ),
    CommandDef(
        "/db",
        True,
        True,
        "_cmd_db",
        "stats | urls [--lang ja|en] [--limit N] | clean <url> | rebuild-fts | health | checkpoint | vacuum | purge | recover",
    ),
    CommandDef(
        "/tool",
        True,
        False,
        "_cmd_tool",
        "list | show <idx>  Inspect stored tool results",
    ),
    CommandDef(
        "/set",
        True,
        False,
        "_cmd_set",
        "temperature <f> | max_tokens <n>  Set LLM generation parameters",
    ),
    CommandDef(
        "/memory",
        True,
        False,
        "_cmd_memory",
        "list|search|pin|unpin|delete|show|prune  Manage long-term memory entries",
    ),
    CommandDef(
        "/debug",
        True,
        False,
        "_cmd_debug",
        "[audit|verbose|normal]  Toggle debug; subcommands: audit=tail log, verbose/normal=log level",
    ),
    CommandDef(
        "/audit",
        True,
        False,
        "_cmd_audit",
        "tail [N] | turn <task_id> | tool <name>  Browse audit log events",
    ),
    CommandDef(
        "/approve",
        True,
        False,
        "_cmd_approve",
        "[reason]  Approve the pending workflow task",
    ),
    CommandDef(
        "/plugin",
        True,
        False,
        "_cmd_plugin",
        "status  Show plugin load results (loaded, failed, conflicts)",
    ),
    # ── Prefix async ───────────────────────────────────────────────────────────
    CommandDef(
        "/mdq",
        True,
        True,
        "_cmd_mdq",
        "status | index <path> [--force] | refresh <path> [--force] | search <query> | outline <path> | get <chunk_id> | grep <pattern>",
    ),
]


class CommandRegistry(
    _SessionMixin,
    _McpMixin,
    _ConfigMixin,
    _ContextMixin,
    _DbMixin,
    _ToolingMixin,
    _DebugMixin,
    _AuditMixin,
    _IngestMixin,
    _MemoryMixin,
    _WorkflowMixin,
    _PluginsMixin,
    _MdqMixin,
):
    """Slash-command dispatcher for AgentREPL.

    All _cmd_* methods operate solely on AgentContext injected in __init__,
    with no dependency on AgentREPL itself.
    """

    def __init__(self, ctx: AgentContext, out: OutputPort | None = None) -> None:
        self._ctx = ctx
        self._out: OutputPort = out if out is not None else CliOutputPort()
        # Fail-fast: validate all handler strings refer to existing methods.
        for _cmd in _COMMANDS:
            if not hasattr(self, _cmd.handler):
                raise AttributeError(
                    f"CommandDef references unknown handler: {_cmd.handler!r}"
                )

    def _get_handler(
        self, cmd: CommandDef, is_async: bool, /
    ) -> Callable[[str], None] | Callable[[str], Awaitable[None]]:
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
        self._out.write(f"Tools: {n_tools}  |  LLM: {ctx.cfg.llm.llm_url}  |  {sid}")

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
            handler = self._get_handler(cmd, cmd.is_async)
            if cmd.prefix:
                if line == cmd.name or line.startswith(cmd.name + " "):
                    args = line[len(cmd.name) :]
                    if cmd.is_async:
                        await handler(args)  # type: ignore[misc]
                    else:
                        handler(args)
                    return True
            else:
                if line == cmd.name:
                    if cmd.is_async:
                        await handler("")  # type: ignore[misc]
                    else:
                        handler("")
                    return True

        # Plugin commands: exact-match and prefix-match (checked after built-ins)
        return await self._dispatch_plugin(line)

    async def _dispatch_plugin(self, line: str) -> bool:
        """Dispatch to the first matching registered plugin command; return True if matched."""
        for cmd_name, (handler, is_prefix) in plugin_registry.iter_commands().items():
            args: str = ""
            if is_prefix and line.startswith(cmd_name):
                args = line[len(cmd_name) :]
            elif not is_prefix and line == cmd_name:
                pass  # args stays empty
            else:
                continue
            if asyncio.iscoroutinefunction(handler):
                await handler(self._ctx, args)
            else:
                handler(self._ctx, args)
            return True
        return False
