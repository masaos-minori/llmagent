---
title: "Agent CLI and Commands - Slash Commands: Context, Plan"
area: agent
tags:
  - agent
  - cli
  - slash-commands
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_09_cli-and-commands-slash-commands-context-db.md
---

# Agent CLI and Commands

- System Overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Documents the purpose and side effects of slash commands in the Context and Plan categories.

## Design Intent

### Context Category

A group of commands for managing context information and history.

| Command | Side Effect | Related State |
|---|---|---|
| `/context` | None | Displays history size, budget, system prompt, workflow mode, and pending approval status |
| `/compact` | LLM call (compression) | Immediately compresses history |
| `/system [name]` | Updates `history[0]` | `ctx.conv.system_prompt_name` |

### Plan Category

| Command | Side Effect | Related State |
|---|---|---|
| `/plan` | None | Toggles `ctx.conv.plan_mode` |

## Responsibility Boundary

- **Context**: Displaying context information and managing history
- **Plan**: Toggling plan mode

## Key Constraints

- Unknown

## Operational Notes

- Unknown

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

context category
plan category
