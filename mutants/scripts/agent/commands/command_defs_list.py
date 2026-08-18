"""scripts/agent/commands/command_defs_list.py — Built-in slash command definitions for AgentREPL.

This module is the SINGLE SOURCE OF TRUTH for the _COMMANDS list.
All built-in slash commands are defined here and only here.

Owns:
  _COMMANDS: list[CommandDef] — ordered list of all built-in slash commands.
                                Exact-match commands are listed first;
                                prefix commands follow.

Does NOT own:
  CommandDef / SubcommandSpec dataclasses — defined in agent.commands.command_defs.

To add a built-in command:
  1. Append (or insert) a CommandDef(...) entry in _COMMANDS below.
  2. Implement the corresponding _cmd_<name> handler in the appropriate mixin.
  3. Do NOT add CommandDef entries anywhere else.
"""

from __future__ import annotations

from agent.commands.command_defs import CommandDef

# Single source of truth for all built-in slash commands.
# Exact-match commands are listed first, followed by prefix commands.
_COMMANDS: list[CommandDef] = [
    # ── Exact-match sync ─────────────────────────────────────────────────────
    CommandDef(
        name="/help",
        prefix=False,
        is_async=False,
        handler="_cmd_help",
        help="Show this help",
    ),
    CommandDef(
        name="/config",
        prefix=False,
        is_async=False,
        handler="_cmd_config",
        help="Current configuration and config file paths",
    ),
    CommandDef(
        name="/stats",
        prefix=False,
        is_async=False,
        handler="_cmd_stats",
        help="Session statistics (turns, tool calls, RAG hits, error counts)",
    ),
    CommandDef(
        name="/context",
        prefix=False,
        is_async=False,
        handler="_cmd_context",
        help="Runtime context state (messages, chars, compression, system prompt)",
    ),
    CommandDef(
        name="/plan",
        prefix=False,
        is_async=False,
        handler="_cmd_plan",
        help="Toggle plan mode",
    ),
    CommandDef(
        name="/undo",
        prefix=False,
        is_async=False,
        handler="_cmd_undo",
        help="Roll back the last user+assistant turn",
    ),
    CommandDef(
        name="/reload",
        prefix=False,
        is_async=False,
        handler="_cmd_reload",
        help="Reload all config/*.toml files and apply runtime-configurable parameters",
    ),
    # ── Exact-match async ────────────────────────────────────────────────────
    CommandDef(
        name="/compact",
        prefix=False,
        is_async=True,
        handler="_cmd_compact",
        help="Force immediate compression of conversation history",
    ),
    CommandDef(
        name="/diff",
        prefix=False,
        is_async=True,
        handler="_cmd_diff",
        help="Show diffs for files written/edited this session",
    ),
    # ── Prefix sync ──────────────────────────────────────────────────────────
    CommandDef(
        name="/mcp",
        prefix=True,
        is_async=True,
        handler="_cmd_mcp",
        help="MCP server status, tool list, connectivity check",
    ),
    CommandDef(
        name="/session",
        prefix=True,
        is_async=True,
        handler="_cmd_session",
        help="list [n] | load <id> | rename <title> | delete <id>"
        " | export markdown|json [file] | stats|health|checkpoint|vacuum|purge|recover|rag-consistency|rag-rebuild-fts",
    ),
    CommandDef(
        name="/clear",
        prefix=True,
        is_async=False,
        handler="_cmd_clear",
        help="Reset conversation history; 'new' also starts a new session",
    ),
    CommandDef(
        name="/history",
        prefix=True,
        is_async=False,
        handler="_cmd_history",
        help="[n]  Show last N user/assistant messages (default: 5)",
    ),
    CommandDef(
        name="/system",
        prefix=True,
        is_async=False,
        handler="_cmd_system",
        help="[name]  Switch system prompt preset; list presets if no name given",
    ),
    CommandDef(
        name="/memory",
        prefix=True,
        is_async=False,
        handler="_cmd_memory",
        help="list|search|pin|unpin|delete|show|prune  Manage long-term memory entries",
    ),
    CommandDef(
        name="/debug",
        prefix=True,
        is_async=False,
        handler="_cmd_debug",
        help="[verbose|normal]  Toggle debug mode; subcommands: verbose/normal=log level",
    ),
    CommandDef(
        name="/audit",
        prefix=True,
        is_async=False,
        handler="_cmd_audit",
        help="tail [N] | turn <task_id> | tool <name>  Browse audit log events",
    ),
    CommandDef(
        name="/approve",
        prefix=True,
        is_async=False,
        handler="_cmd_approve",
        help="<approval_id> [reason]  Approve the pending workflow task",
    ),
    CommandDef(
        name="/reject",
        prefix=True,
        is_async=False,
        handler="_cmd_reject",
        help="<approval_id> [reason]  Reject the pending workflow task",
    ),
    CommandDef(
        name="/skill",
        prefix=True,
        is_async=True,
        handler="_cmd_skill",
        help="[name] [args]  List skills, or load skills/<name>/SKILL.md as ephemeral system context",
    ),
    # ── Prefix async ───────────────────────────────────────────────────────────
    CommandDef(
        name="/mdq",
        prefix=True,
        is_async=True,
        handler="_cmd_mdq",
        help="status | index <path> [--force] | refresh <path> [--force] | search <query> | outline <path> | get <chunk_id> | grep <pattern>",
    ),
]
