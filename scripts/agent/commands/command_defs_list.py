"""command_defs_list.py — Built-in slash command definitions for AgentREPL.

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
        "rag stats|urls|clean|rebuild-fts|vec-rebuild|reconcile-url|recover|consistency; session stats|health|checkpoint|vacuum|purge|recover",
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
        "[verbose|normal]  Toggle debug mode; subcommands: verbose/normal=log level",
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
        "<approval_id> [reason]  Approve the pending workflow task",
    ),
    CommandDef(
        "/reject",
        True,
        False,
        "_cmd_reject",
        "<approval_id> [reason]  Reject the pending workflow task",
    ),
    CommandDef(
        "/plugin",
        True,
        False,
        "_cmd_plugin",
        "status  Show plugin load results (loaded, failed, conflicts)",
    ),
    CommandDef(
        "/skill",
        True,
        False,
        "_cmd_skill",
        "[name] [args]  List skills, or load skills/<name>/SKILL.md as ephemeral system context",
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
