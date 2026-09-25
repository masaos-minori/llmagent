---
title: "Agent CLI and Commands - CommandRegistry"
area: agent
tags:
  - agent
  - cli
  - command-registry
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_03_cli-and-commands-command-registry.md
---

# Agent CLI and Commands

- System Overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

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

### Adding New Commands

Add a `CommandDef(...)` entry to `command_defs_list.py` and implement the corresponding handler in the appropriate mixin file.

## Responsibility Boundary

- `CommandRegistry` is responsible **only for dispatching**. Command implementations are distributed among individual mixin classes.
- `CommandRegistry.__init__` performs fail-fast validation of handler strings.

## Key Constraints

- Unknown

## Operational Notes

- Unknown

## Known Limitations

- `AgentREPL.SLASH_COMMANDS` (for tab completion) and `command_defs_list._COMMANDS` (for dispatching) are maintained separately and currently have discrepancies. Since `SLASH_COMMANDS` does not include `/memory`, `/audit`, `/plan`, `/skill`, or `/mdq`, these commands can be dispatched but are not available for tab completion.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

CommandRegistry
responsibility boundary
known limitation
