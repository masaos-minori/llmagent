#!/usr/bin/env python3
"""
agent_commands.py
Slash-command registry for AgentREPL.

CommandRegistry inherits command groups from six mixin classes.
All _cmd_* methods operate solely on AgentContext injected in __init__,
with no dependency on AgentREPL itself.

Mixin split:
  agent_cmd_session.py  — _SessionMixin:  /session commands
  agent_cmd_mcp.py      — _McpMixin:      /mcp commands
  agent_cmd_config.py   — _ConfigMixin:   /config, /stats, /set, /reload
  agent_cmd_context.py  — _ContextMixin:  /context, /clear, /undo, /history, /db
  agent_cmd_rag.py      — _RagMixin:      /rag, /tool, /note, /plan, /debug
  agent_cmd_ingest.py   — _IngestMixin:   /ingest, /export, /compact
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

import plugin_registry
from agent_cmd_config import _ConfigMixin
from agent_cmd_context import _budget_breakdown, _ContextMixin
from agent_cmd_ingest import _IngestMixin
from agent_cmd_mcp import _McpMixin
from agent_cmd_rag import _RagMixin
from agent_cmd_session import _SessionMixin
from agent_context import AgentContext

logger = logging.getLogger(__name__)

# Re-export for callers that import from this module
# agent_repl.py: from agent_commands import CommandRegistry, _budget_breakdown
# agent_repl_tool_exec.py: from agent_commands import mask_args
__all__ = ["CommandRegistry", "_budget_breakdown", "mask_args"]


def mask_args(args: dict, masked_fields: list[str]) -> dict:
    """Return a copy of args with masked_fields values replaced by '***'.

    Used before logging tool call arguments to prevent sensitive data leakage.
    """
    return {k: ("***" if k in masked_fields else v) for k, v in args.items()}


class CommandRegistry(
    _SessionMixin,
    _McpMixin,
    _ConfigMixin,
    _ContextMixin,
    _RagMixin,
    _IngestMixin,
):
    """Slash-command dispatcher for AgentREPL.

    All _cmd_* methods operate solely on AgentContext injected in __init__,
    with no dependency on AgentREPL itself.
    """

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    def _cmd_help(self) -> None:
        """Print help and available tool count."""
        ctx = self._ctx
        n_tools = len(ctx.cfg.tool_definitions)
        sid = (
            f"session {ctx.session.session_id}"
            if ctx.session.session_id
            else "no session"
        )
        print(
            "Agent REPL — type a question and press Enter.\n"
            "Each message is augmented with RAG context before being sent to the LLM.\n"
            "Conversation history is preserved within the session.\n"
            "\n"
            "Slash commands:\n"
            "  /help              Show this help\n"
            "  /mcp               MCP server status, tool list, connectivity check\n"
            "  /mcp install <n>   Scaffold a new MCP server template files (wizard)\n"
            "  /config            Current configuration and config file paths\n"
            "  /stats             Session statistics"
            " (turns, tool calls, RAG hits, error counts)\n"
            "  /context           Runtime context state"
            " (messages, chars, compression, system prompt)\n"
            "  /compact           Force immediate compression of conversation history\n"
            "  /clear [new]       Reset conversation history and session stats;"
            " 'new' also starts a new session\n"
            "  /session list [n]        List past sessions (default: 20)\n"
            "  /session load <id>       Restore a past session's conversation history\n"
            "  /session rename <title>  Rename the current session\n"
            "  /session delete <id>     Delete a past session and its messages\n"
            "  /db stats                Show document/chunk/session/message counts\n"
            "  /db urls [--lang ja|en] [--limit N]  List registered document URLs\n"
            "  /db clean <url>    Delete a document and its chunks from the DB\n"
            "  /db rebuild-fts    Rebuild the FTS5 chunks_fts index\n"
            "  /ingest <url|path> [--snippets-only]"
            "  Crawl/ingest a URL or local file into the RAG DB\n"
            "  /debug             Toggle RAG pipeline debug output\n"
            "  /rag               Show RAG step status\n"
            "  /rag on|off        Enable/disable RAG search\n"
            "  /rag mqe on|off    Enable/disable Multi-Query Expansion\n"
            "  /rag rerank on|off Enable/disable Cross-Encoder reranking\n"
            "  /rag search <q>    Dry-run RAG pipeline and display chunks"
            " (no LLM call)\n"
            "  /note add <text>   Add a persistent note\n"
            "  /note list         List all notes\n"
            "  /note delete <id>  Delete a note by ID\n"
            "  /tool list         List stored tool results (current session)\n"
            "  /tool show <idx>   Show full text of a stored tool result\n"
            "  /undo              Roll back the last user+assistant turn\n"
            "  /history [n]       Show last N user/assistant messages"
            " (default: 5)\n"
            "  /system [name]     Switch system prompt preset;"
            " list presets if no name given\n"
            "  /export [md|json] [file]  Export conversation history"
            " (default: md to stdout)\n"
            "  /set temperature <f>  Set LLM generation temperature (0.0–2.0)\n"
            "  /set max_tokens <n>   Set maximum tokens per LLM response\n"
            "  /reload            Reload config/agent.json and apply"
            " runtime-configurable parameters\n"
            "  /exit              Exit (Ctrl-D also works)\n"
            "\n"
            f"Tools: {n_tools}  |  LLM: {ctx.llm_url}  |  {sid}"
        )

    async def dispatch(self, line: str) -> bool:
        """Dispatch a slash command; return True if matched, False otherwise.

        Exact-match commands are looked up in a dict for conciseness.
        Prefix commands (/session, /ingest, /export) are handled separately
        because they pass trailing arguments to their handlers.
        """
        # exact-match sync commands: name → handler (no args)
        sync_cmds: dict[str, Callable[[], None]] = {
            "/help": self._cmd_help,
            "/config": self._cmd_config,
            "/stats": self._cmd_stats,
            "/context": self._cmd_context,
            "/debug": self._cmd_debug,
            "/plan": self._cmd_plan,
            "/undo": self._cmd_undo,
            "/reload": self._cmd_reload,
        }
        # exact-match async commands: name → coroutine handler (no args)
        async_cmds: dict[str, Callable[[], Any]] = {
            "/compact": self._cmd_compact,
        }

        if line in sync_cmds:
            sync_cmds[line]()
            return True
        if line in async_cmds:
            await async_cmds[line]()
            return True

        # prefix commands that accept trailing arguments: (prefix, handler, is_async)
        prefix_cmds: list[tuple[str, Callable[[str], Any], bool]] = [
            ("/mcp", self._cmd_mcp, True),
            ("/session", self._cmd_session, False),
            ("/clear", self._cmd_clear, False),
            ("/ingest", self._cmd_ingest, True),
            ("/export", self._cmd_export, False),
            ("/rag", self._cmd_rag, True),
            ("/history", self._cmd_history, False),
            ("/system", self._cmd_system, False),
            ("/db", self._cmd_db, False),
            ("/note", self._cmd_note, False),
            ("/tool", self._cmd_tool, False),
            ("/set", self._cmd_set, False),
        ]
        for prefix, handler, is_async in prefix_cmds:
            if line.startswith(prefix):
                args = line[len(prefix) :]
                if is_async:
                    await handler(args)
                else:
                    handler(args)
                return True

        # Plugin commands: exact-match and prefix-match (checked after built-ins)
        for cmd_name, (handler, is_prefix) in plugin_registry.iter_commands().items():
            if is_prefix and line.startswith(cmd_name):
                args = line[len(cmd_name) :]
                if asyncio.iscoroutinefunction(handler):
                    await handler(self._ctx, args)
                else:
                    handler(self._ctx, args)
                return True
            if not is_prefix and line == cmd_name:
                if asyncio.iscoroutinefunction(handler):
                    await handler(self._ctx, "")
                else:
                    handler(self._ctx, "")
                return True

        return False
