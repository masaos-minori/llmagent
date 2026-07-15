#!/usr/bin/env python3
"""registry.py

Slash-command registry for AgentREPL.

CommandRegistry inherits command groups from mixin classes.
All _cmd_* methods operate solely on AgentContext injected in __init__,
with no dependency on AgentREPL itself.

Mixins (keep in sync with CommandRegistry base class list):
  cmd_session.py    — _SessionMixin:    /session commands
  cmd_mcp.py        — _McpMixin:        /mcp commands
  cmd_config.py     — _ConfigMixin:     /config, /stats, /reload
cmd_context.py    — _ContextMixin:    /context, /clear, /undo, /history, /system
   cmd_tooling.py    — _ToolingMixin:    /plan
  cmd_debug.py      — _DebugMixin:      /debug
  cmd_audit.py      — _AuditMixin:      /audit
  cmd_rag_export.py — _RagExportMixin:  /compact
  cmd_memory.py     — _MemoryMixin:     /memory
  cmd_workflow.py   — _WorkflowMixin:   /approve, /reject
  cmd_plugins.py    — _PluginsMixin:    /plugin
  cmd_mdq.py        — _MdqMixin:        /mdq commands
  cmd_skill.py      — _SkillMixin:      /skill commands

_COMMANDS ownership:
  _COMMANDS is IMPORTED from agent.commands.command_defs_list.
  It is NOT defined in this module.
  This module owns: dispatch behavior (dispatch(), _get_handler(),
                    _dispatch_plugin()) and the fail-fast handler
                    validation in __init__.
"""

import inspect
from collections.abc import Callable
from typing import Any

from agent.commands.cmd_audit import _AuditMixin
from agent.commands.cmd_config import _ConfigMixin
from agent.commands.cmd_context import _ContextMixin
from agent.commands.cmd_debug import _DebugMixin
from agent.commands.cmd_mcp import _McpMixin
from agent.commands.cmd_mdq import _MdqMixin
from agent.commands.cmd_memory import _MemoryMixin
from agent.commands.cmd_plugins import _PluginsMixin
from agent.commands.cmd_rag_export import _RagExportMixin
from agent.commands.cmd_session import _SessionMixin
from agent.commands.cmd_skill import _SkillMixin
from agent.commands.cmd_tooling import _ToolingMixin
from agent.commands.cmd_workflow import _WorkflowMixin
from agent.commands.command_defs import CommandDef
from agent.commands.command_defs_list import _COMMANDS
from agent.commands.output_port import CliOutputPort, OutputPort
from agent.context import AgentContext
from shared import plugin_registry

__all__ = ["CommandRegistry"]


class CommandRegistry(
    _SessionMixin,
    _McpMixin,
    _ConfigMixin,
    _ContextMixin,
    _ToolingMixin,
    _DebugMixin,
    _AuditMixin,
    _RagExportMixin,
    _MemoryMixin,
    _WorkflowMixin,
    _PluginsMixin,
    _MdqMixin,
    _SkillMixin,
):
    """Slash-command dispatcher for AgentREPL.

    All _cmd_* methods operate solely on AgentContext injected in __init__,
    with no dependency on AgentREPL itself.
    """

    def __init__(self, ctx: AgentContext, out: OutputPort | None = None) -> None:
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
                    if cmd.is_async:
                        await handler(args)
                    else:
                        handler(args)
                    return True
            else:
                if line == cmd.name:
                    if cmd.is_async:
                        await handler()
                    else:
                        handler()
                    return True

        # Plugin commands: exact-match and prefix-match (checked after built-ins)
        return await self._dispatch_plugin(line)

    async def _dispatch_plugin(self, line: str) -> bool:
        """Dispatch to the first matching registered plugin command; return True if matched."""
        for cmd_name, (handler, is_prefix) in plugin_registry.iter_commands().items():
            args: str = ""
            if is_prefix and (line == cmd_name or line.startswith(cmd_name + " ")):
                args = line[len(cmd_name) :].strip()
            elif not is_prefix and line == cmd_name:
                pass  # args stays empty
            else:
                continue
            if inspect.iscoroutinefunction(handler):
                await handler(self._ctx, args)
            else:
                handler(self._ctx, args)
            return True
        return False
