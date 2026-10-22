"""scripts/agent/commands/command_defs_list.py — Built-in slash command definitions for AgentREPL.

This module is the SINGLE SOURCE OF TRUTH for the _COMMANDS list.
All built-in slash commands are defined here and only here.

Owns:
  _COMMANDS: list[CommandDef] — ordered list of all built-in slash commands.
                                Exact-match commands are listed first;
                                prefix commands follow.

Does NOT own:
  CommandDef / SubcommandSpec / ArgSpec dataclasses — defined in agent.commands.command_defs.

The subcommand and argument contract (SubcommandSpec / ArgSpec) is the canonical
source checked against the Agent command docs by tools/check_docs_consistency.py
(GV-023); update the docs together with it.

To add a built-in command:
  1. Append (or insert) a CommandDef(...) entry in _COMMANDS below.
  2. Implement the corresponding _cmd_<name> handler in the appropriate mixin.
  3. Do NOT add CommandDef entries anywhere else.
"""

from __future__ import annotations

from agent.commands.command_defs import ArgSpec, CommandDef, SubcommandSpec

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
        help="Runtime context state: history amount, budget, mode and pending-approval state",
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
    # ── Prefix sync ──────────────────────────────────────────────────────────
    CommandDef(
        name="/mcp",
        prefix=True,
        is_async=True,
        handler="_cmd_mcp",
        help="[status|tools]  MCP server status, tool list, connectivity check",
        subcommands=[
            SubcommandSpec("status", "MCP server status (default)"),
            SubcommandSpec("tools", "RuntimeToolRegistry diagnostics"),
        ],
    ),
    CommandDef(
        name="/session",
        prefix=True,
        is_async=True,
        handler="_cmd_session",
        help="list [n] | load <id> | rename <title> | delete <id>"
        " | export markdown|md|json [file] | stats|health|checkpoint|vacuum|purge|recover|rag-consistency|rag-rebuild-fts|rag-rebuild-vec",
        subcommands=[
            SubcommandSpec("list", "List sessions", (ArgSpec("n", default="20"),)),
            SubcommandSpec("load", "Resume a session", (ArgSpec("id", required=True),)),
            SubcommandSpec(
                "rename", "Set the session title", (ArgSpec("title", required=True),)
            ),
            SubcommandSpec(
                "delete", "Delete a session", (ArgSpec("id", required=True),)
            ),
            SubcommandSpec(
                "export",
                "Export the in-memory history",
                (ArgSpec("markdown|md|json", default="markdown"), ArgSpec("file")),
            ),
            SubcommandSpec("stats", "Session DB statistics"),
            SubcommandSpec("health", "Session DB health"),
            SubcommandSpec(
                "checkpoint",
                "Run a WAL checkpoint",
                (ArgSpec("PASSIVE|FULL|RESTART|TRUNCATE"),),
            ),
            SubcommandSpec("vacuum", "VACUUM the session DB"),
            SubcommandSpec(
                "purge",
                "Purge old sessions",
                (ArgSpec("--max-sessions <n>"), ArgSpec("--max-age-days <n>")),
            ),
            SubcommandSpec(
                "recover", "Integrity check and restore", (ArgSpec("backup_path"),)
            ),
            SubcommandSpec("rag-consistency", "RAG DB consistency check"),
            SubcommandSpec("rag-rebuild-fts", "Rebuild chunks_fts"),
            SubcommandSpec("rag-rebuild-vec", "Rebuild chunks_vec"),
        ],
    ),
    CommandDef(
        name="/clear",
        prefix=True,
        is_async=False,
        handler="_cmd_clear",
        help="Reset conversation history; 'new' also starts a new session",
        args=(ArgSpec("new"),),
    ),
    CommandDef(
        name="/history",
        prefix=True,
        is_async=False,
        handler="_cmd_history",
        help="[n]  Show the content of recent user/assistant messages (default: 5)",
        args=(ArgSpec("n", default="5"),),
    ),
    CommandDef(
        name="/memory",
        prefix=True,
        is_async=False,
        handler="_cmd_memory",
        help="status|list|delete|pin|unpin|prune|reindex|rebuild  Manage long-term memory entries",
        subcommands=[
            SubcommandSpec("status", "Embedding, circuit state, retrieval mode"),
            SubcommandSpec(
                "list",
                "List entries",
                (
                    ArgSpec("n", default="20"),
                    ArgSpec("--type semantic|episodic"),
                    ArgSpec("--pinned"),
                    ArgSpec("--query <text>"),
                ),
            ),
            SubcommandSpec(
                "pin", "Pin an entry", (ArgSpec("memory_id", required=True),)
            ),
            SubcommandSpec(
                "unpin", "Unpin an entry", (ArgSpec("memory_id", required=True),)
            ),
            SubcommandSpec(
                "delete", "Delete one entry", (ArgSpec("memory_id", required=True),)
            ),
            SubcommandSpec(
                "prune",
                "Delete old entries after confirmation",
                (ArgSpec("--days <n>"),),
            ),
            SubcommandSpec(
                "reindex",
                "Rebuild FTS/vec indexes only",
                (ArgSpec("--fts|--vec"),),
            ),
            SubcommandSpec(
                "rebuild",
                "Rebuild from the JSONL archive",
                (ArgSpec("--confirm"), ArgSpec("--allow-loss")),
            ),
        ],
    ),
    CommandDef(
        name="/debug",
        prefix=True,
        is_async=False,
        handler="_cmd_debug",
        help="[verbose|normal]  Toggle debug mode; subcommands: verbose/normal=log level",
        subcommands=[
            SubcommandSpec("verbose", "Debug loggers at DEBUG level"),
            SubcommandSpec("normal", "Debug loggers at INFO level"),
        ],
    ),
]
