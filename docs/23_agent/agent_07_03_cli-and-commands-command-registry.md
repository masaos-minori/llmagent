---
title: "Agent CLI and Commands - CommandRegistry"
area: agent
tags:
  - agent
  - cli
  - command-registry
related:
  - agent_00_document-guide.md
  - agent_07_01_cli-and-commands-cli-reference.md
  - agent_07_02_cli-and-commands-cliview.md
  - agent_07_04_cli-and-commands-purpose.md
  - agent_07_05_cli-and-commands-repl-io.md
  - agent_07_06_cli-and-commands-hot-reload.md
  - agent_07_07_cli-and-commands-slash-commands-session-mcp.md
  - agent_07_08_cli-and-commands-slash-commands-context-db.md
  - agent_07_09_cli-and-commands-slash-commands-workflow-debug.md
  - agent_07_10_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

Documents the responsibilities of `CommandRegistry`, which handles dispatching all slash commands, and the separation of responsibilities between modules.

## Design Intent

### Role of CommandRegistry

`CommandRegistry` is located in `agent/commands/registry.py` and dispatches all slash commands via `dispatch(line)`.

### Separation of Responsibilities

| Component | Responsible for | Not responsible for |
|---|---|---|
| `command_defs.py` | `CommandDef`, `SubcommandSpec` dataclasses | Command list |
| `command_defs_list.py` | Built-in command definitions | Dispatch logic |
| `registry.py` | Dispatch behavior, imports command list from `command_defs_list` | Definition of command list |

### Built-in Command Index

Index of the built-in slash commands defined in `_COMMANDS`; `/exit` is additionally reserved by the REPL itself. Subcommands, arguments and flags are intentionally not repeated here: see the per-command chapters ([agent_07_07](agent_07_07_cli-and-commands-slash-commands-session-mcp.md) to [agent_07_10](agent_07_10_cli-and-commands-slash-commands-memory-other.md)) and the `help` text of each `CommandDef` in the source (Explicit in code — `scripts/agent/commands/command_defs_list.py`, `scripts/agent/repl.py`).

| Command | Purpose |
|---|---|
| `/help` | Show the command help |
| `/config` | Show the current configuration and config file paths |
| `/stats` | Show session statistics |
| `/context` | Show the runtime context state |
| `/plan` | Toggle plan mode |
| `/undo` | Roll back the last user+assistant turn |
| `/reload` | Reload config files and apply runtime-configurable parameters |
| `/compact` | Force immediate compression of conversation history |
| `/diff` | Show diffs for files written/edited this session |
| `/mcp` | Show MCP server status, tool list and connectivity |
| `/session` | Manage sessions and session database maintenance |
| `/clear` | Reset conversation history, optionally starting a new session |
| `/history` | Show recent user/assistant messages |
| `/system` | Switch the system prompt preset |
| `/memory` | Manage long-term memory entries |
| `/debug` | Toggle debug mode / log level |
| `/audit` | Browse audit log events |
| `/approve` | Approve the pending workflow task |
| `/reject` | Reject the pending workflow task |
| `/skill` | List skills or load a skill as ephemeral system context |
| `/mdq` | Markdown query operations (status, index, search, outline, etc.) |

### Adding New Commands

Add a `CommandDef(...)` entry to `command_defs_list.py` and implement the corresponding handler in the appropriate mixin file.

## Responsibility Boundary

- `CommandRegistry` is responsible **only for dispatching**. Command implementations are distributed among individual mixin classes.
- `CommandRegistry.__init__` performs fail-fast validation of handler strings.

## Key Constraints

- A slash command that is not registered, including legacy commands such as `/db`, is rejected as an unknown command (`Unknown command: ... (type /help for commands)`); no compatibility alias is provided.
- `/debug` rejects an unknown subcommand explicitly (`Unknown subcommand: ...`) instead of ignoring it.

## Known Limitations

- `AgentREPL.SLASH_COMMANDS` (for tab completion) is derived from `command_defs_list._COMMANDS` plus REPL-reserved commands via `completion_command_names()`, so it does not drift from the dispatch table.

## Keywords

CommandRegistry
responsibility boundary
known limitation
