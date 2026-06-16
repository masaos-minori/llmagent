#!/usr/bin/env python3
"""agent/commands/command_defs.py
Declarative slash-command definitions for CommandRegistry.

Provides:
  SubcommandSpec — metadata for one subcommand
  CommandDef     — metadata for one slash command
  _COMMANDS      — single source of truth for all built-in slash commands

Import from here:  from agent.commands.command_defs import _COMMANDS, CommandDef
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SubcommandSpec:
    """Declarative metadata for one subcommand."""

    name: str
    help: str


@dataclass
class CommandDef:
    """Declarative metadata for one slash command."""

    name: str  # e.g. "/help"
    prefix: bool  # True = prefix match (args passed); False = exact match (no args)
    is_async: bool
    handler: str  # method name on CommandRegistry
    help: str  # one-line description shown in /help output
    subcommands: list[SubcommandSpec] = field(default_factory=list)


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
        "Reload config/agent.toml and apply runtime-configurable parameters",
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
        "MCP server status, tool list, connectivity check; 'install <n>' scaffolds a new server",
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
        False,
        "_cmd_db",
        "stats | urls [--lang ja|en] [--limit N] | clean <url> | rebuild-fts | health | checkpoint | vacuum | purge | recover",
    ),
    CommandDef(
        "/note",
        True,
        False,
        "_cmd_note",
        "add <text> | list | delete <id>  Manage persistent notes",
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
]

__all__ = ["_COMMANDS", "CommandDef", "SubcommandSpec"]
