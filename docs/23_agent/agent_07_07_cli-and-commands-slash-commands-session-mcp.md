---
title: "Agent CLI and Commands - Slash Commands: Session, MCP, Config/Stats"
area: agent
tags:
  - agent
  - cli
  - slash-commands
related:
  - agent_00_document-guide.md
  - agent_07_01_cli-and-commands-cli-reference.md
  - agent_07_02_cli-and-commands-cliview.md
  - agent_07_03_cli-and-commands-command-registry.md
  - agent_07_04_cli-and-commands-purpose.md
  - agent_07_05_cli-and-commands-repl-io.md
  - agent_07_06_cli-and-commands-hot-reload.md
  - agent_07_08_cli-and-commands-slash-commands-context-plan.md
  - agent_07_09_cli-and-commands-slash-commands-workflow-debug.md
  - agent_07_10_cli-and-commands-slash-commands-memory-other.md
  - agent_01_system-overview.md
---

# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

Documents the purpose and side effects of slash commands in the Session, MCP, and Config/Stats categories.

## Design Intent

### Session Category

A group of commands for session management and history operations. `/clear [new]` resets the history, and `/clear new` also starts a new DB session. `/undo` pops the most recent user+assistant turn from both the history and the DB. Memory and the DB are trimmed from the exact same set of deleted rows; when they had already diverged, `/undo` still converges them — it trims memory to exactly the rows it deletes, and if those rows cannot be matched it reloads memory from the DB and logs the decision. Messages that existed when the history was last compressed (automatic, `/compact`, or fallback truncation) cannot be undone; `/undo` then reports that nothing can be undone and changes nothing. The boundary is stored in `sessions.undo_floor_message_id` and survives `/session load`.

#### History and export

| Command | Form | Effect |
|---|---|---|
| `/history` | `/history [n]` | Shows the last `n` user and assistant messages of the in-memory history (default 5), one line each with a truncated preview; tool messages are not shown |
| `/session export` | `/session export [markdown\|md\|json] [file]` | Exports the current in-memory conversation history |

`/history` accepts `n` in `1..200`; a non-integer, `0`, a negative, or a value above `200` is a usage error that prints nothing, and an empty history is reported as no data; omitting `n` keeps the default of 5. For `/session export`, the format defaults to Markdown (`md` is the permanent short form of `markdown`); `json` writes the message list as indented JSON. The arguments may appear in either order, and any argument that is not a format is taken as the output file. Without a file the export is written to the terminal; with a file it is written there as UTF-8 and the message count is reported, and a write failure is reported as an export error. The export covers only the history currently held in memory, not a stored session that has not been loaded, and it neither modifies nor deletes any session or memory data.

#### Session DB operation subcommands

`/session` without a subcommand runs `list`. The data subcommands manage session rows directly; the maintenance subcommands operate on the session and RAG databases (see agent_04_03 for the services they call).

| Form | Effect |
|---|---|
| `/session list [n]` | Shows recent sessions with their message count (default 20); `n` accepts `1..200`, and a non-integer, `0`, a negative, or a value above `200` is a usage error |
| `/session load <id>` | Resumes a session by id |
| `/session rename <title>` | Sets the title of the current session |
| `/session delete <id>` | Removes a session by id |
| `/session stats` | Shows session database statistics |
| `/session health` | Shows session database integrity and size |
| `/session checkpoint [PASSIVE\|FULL\|RESTART\|TRUNCATE]` | Runs a WAL checkpoint; without a mode the configured mode is used |
| `/session vacuum` | Rebuilds the session database file |
| `/session purge [--max-sessions <n>] [--max-age-days <n>]` | Purges old sessions; `--max-sessions` accepts an integer `>= 1` (a bare flag, `0`, a negative, or a non-integer is an error), `--max-age-days` accepts an integer `>= 0` (`0` keeps its documented "disabled" meaning; a negative or non-integer is an error), and an absent flag uses the retention default; the session currently active in the agent is never removed — when a purge would have deleted it, the success line reports `(kept active session <id>)` and the kept session count may exceed `--max-sessions` by one |
| `/session recover [backup_path]` | Checks integrity and restores from the backup when corruption is found |
| `/session rag-consistency` | Checks the consistency of the RAG database |
| `/session rag-rebuild-fts` | Rebuilds `chunks_fts` from `chunks` |
| `/session rag-rebuild-vec` | Rebuilds `chunks_vec` from `chunks` |

#### Long-running and off-loop subcommands

The maintenance, export, and RAG subcommands — `/session stats`, `/session health`, `/session checkpoint`, `/session vacuum`, `/session purge`, `/session recover`, `/session rag-consistency`, `/session rag-rebuild-fts`, `/session rag-rebuild-vec`, and `/session export` — open their own SQLite connection and run **outside the event loop** through the offloaded `db_dispatch` table, so they may take seconds while the REPL stays responsive. A shutdown request does not interrupt an in-progress storage call: the call runs to completion, and process shutdown joins the worker thread until it finishes. This is the behavior the offload produces (REQ-006); these subcommands are not cancellable at shutdown. The `is_async` contract that makes this dispatch safe is documented in [agent_07_03](agent_07_03_cli-and-commands-command-registry.md), and `tests/agent/commands/test_command_blocking_offload.py` guards both the loop responsiveness and the completion semantics.

### Session and Memory Separation

`/session load`, `/session delete`, `/session export`, and `/session purge`
operate on conversation sessions and messages only. They never delete or
restore long-term memory. Memories extracted from a deleted session remain
available for reuse across later sessions. `/undo` likewise rolls back conversation history only and never deletes or modifies long-term memory.

### MCP Category

`/mcp` / `/mcp status` provides a health view of the **currently running** MCP server settings; it is not a preview of pending `/reload` changes.

`/mcp tools` prints the RuntimeToolRegistry diagnostics table.

The output of `/mcp status` includes a list of servers, a list of servers in DEGRADED/UNAVAILABLE states, and serialization event statistics.

### Config / Stats Category

A group of commands for displaying and monitoring configuration files.

| Command | Form | Effect |
|---|---|---|
| `/config` | `/config` | Shows the current configuration and the configuration file paths; changes nothing |
| `/stats` | `/stats` | Shows session statistics (turns, tool calls, RAG hits, error counts) and the current debug mode; changes nothing |
| `/reload` | `/reload` | Reloads all configuration files, applies the runtime-configurable parameters, and updates `ctx.cfg` to synchronize with services |

None of these commands takes a subcommand or argument.

## Responsibility Boundary

- **Session**: Lifecycle management of sessions and history
- **MCP**: Health and tool list of MCP servers
- **Config/Stats**: Displaying configuration and metrics

## Keywords

- slash command reference
- session category
- mcp category
- config/stats category
