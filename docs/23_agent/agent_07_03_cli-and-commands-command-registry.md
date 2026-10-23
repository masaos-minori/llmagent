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
  - agent_07_08_cli-and-commands-slash-commands-context-plan.md
  - agent_07_09_cli-and-commands-slash-commands-workflow-debug.md
  - agent_07_10_cli-and-commands-slash-commands-memory-other.md
  - agent_01_system-overview.md
---

# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

Documents the responsibilities of `CommandRegistry`, which handles dispatching all slash commands, and the separation of responsibilities between modules.

## Design Intent

### Role of CommandRegistry

`CommandRegistry` is located in `agent/commands/registry.py` and dispatches all slash commands via `dispatch(line)`.

### Separation of Responsibilities

Command definition types, the built-in command list, and dispatch behavior live in separate modules: the registry imports the command list and owns only dispatch. Command implementations are distributed among handler mixins.

### Built-in Command Index

Index of the built-in slash commands defined in `_COMMANDS`; `/exit` is additionally reserved by the REPL itself. Subcommands, arguments and flags are intentionally not repeated here: see the per-command chapters ([agent_07_07](agent_07_07_cli-and-commands-slash-commands-session-mcp.md) to [agent_07_10](agent_07_10_cli-and-commands-slash-commands-memory-other.md)) and the `help` text of each `CommandDef` in the source (Explicit in code — `scripts/agent/commands/command_defs_list.py`, `scripts/agent/repl.py`).

| Command | Purpose |
|---|---|
| `/help` | Show the command help |
| `/config` | Show the current configuration and config file paths |
| `/stats` | Show session statistics |
| `/context` | Show history amount, budget, mode and pending-approval state |
| `/plan` | Toggle plan mode |
| `/undo` | Roll back the last user+assistant turn added after the last history compression |
| `/reload` | Reload config files and apply runtime-configurable parameters |
| `/compact` | Force immediate compression of conversation history |
| `/mcp` | Show MCP server status, tool list and connectivity |
| `/session` | Manage sessions and session database maintenance |
| `/clear` | Reset conversation history, optionally starting a new session |
| `/history` | Show the content of recent user/assistant messages |
| `/memory` | Manage long-term memory (status, list, delete, pin, prune, reindex, rebuild) |
| `/debug` | Toggle debug mode / log level |

### Adding New Commands

Add a `CommandDef(...)` entry to `command_defs_list.py` (with `SubcommandSpec`/`ArgSpec` for its subcommands and arguments) and implement the corresponding handler in the appropriate mixin file. Set `is_async` to match the handler's kind — `True` for an `async def` handler, `False` for a sync callable — because `CommandRegistry.__init__` checks it at startup and a mismatch raises a `TypeError` before the REPL runs, not when the command is invoked. Document each usage line in the per-command chapter; `check_docs_consistency.py --domain agent` verifies the contract.

`AgentREPL.SLASH_COMMANDS` (for tab completion) is derived from `command_defs_list._COMMANDS` plus REPL-reserved commands via `completion_command_names()`, so it does not drift from the dispatch table.

## Responsibility Boundary

- `CommandRegistry` is responsible **only for dispatching**. Command implementations are distributed among individual mixin classes.
- `CommandRegistry.__init__` performs fail-fast validation of handler strings **and** their kind: each `CommandDef.is_async` must match whether its handler is a coroutine function or a sync callable, and a mismatch raises a `TypeError` at construction (startup), not when the command runs.

## Key Constraints

- A slash command that is not registered, including legacy commands such as `/db`, is rejected as an unknown command (`Unknown command: ... (type /help for commands)`); no compatibility alias is provided.
- `/debug` rejects an unknown subcommand explicitly (`Unknown subcommand: ...`) instead of ignoring it.

## Output Tags and Severities

Four REPL output tags participate in the command/turn surface. Each has exactly one emitting component:

- `[fatal]` — emitted by `ReplInputLoop._surface_turn_error` (`scripts/agent/repl_input_loop.py`) for turn-level failures that do **not** originate from a command handler.
- `[error]` — emitted by `CommandRegistry` via `OutputPort.write_error` for a command-handler exception that is not a command-domain validation/parse error and not a `sqlite3.Error` (for example a runtime error raised inside a handler). A `sqlite3.Error` is also rendered here by the storage path, prefixed with a statement that the effect may be partial.
- `[usage]` — emitted by `CommandRegistry` via `OutputPort.write_validation_error` for a command-domain validation/parse error (`CommandValidationError`, `CommandParseError`, and subclasses such as `UnknownPresetError` / `UnknownTierError`).
- `[non-fatal]` — emitted for non-blocking runtime notices (for example the disabled-memory warning).

A command-handler error is handled at the `CommandRegistry` dispatch boundary: it renders `[error]` or `[usage]` and returns a matched result, so `_surface_turn_error` (`[fatal]`) is **not** reached. A command error is therefore not a turn failure. Tag values themselves live in `scripts/agent/output_tags.py` and are not modified by this change.

## Known Limitations

Not applicable.

## Keywords

- CommandRegistry
- responsibility boundary
- known limitation
