---
title: "Agent CLI and Commands - Slash Commands: Memory and Other"
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
  - agent_07_07_cli-and-commands-slash-commands-session-mcp.md
  - agent_07_08_cli-and-commands-slash-commands-context-plan.md
  - agent_07_09_cli-and-commands-slash-commands-workflow-debug.md
  - agent_01_system-overview.md
---

# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

Documents the purpose and side effects of slash commands in the Memory and Other categories.

## Design Intent

### Memory Category

A group of commands for long-term memory. `/memory rebuild` imports records from the JSONL archive into SQLite; it is a dry run unless `--confirm` is passed, and deletes and pin/unpin changes are not replayed (Explicit in code — `scripts/agent/commands/memory_rebuild_ops.py`).

### Other Category

`/help` displays this help output.

## Responsibility Boundary

- **Memory**: Management of long-term memory entries
- **Other**: Help display

## Keywords

- memory category
