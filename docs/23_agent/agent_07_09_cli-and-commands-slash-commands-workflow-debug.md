---
title: "Agent CLI and Commands - Slash Commands: Debug, Compact"
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
  - agent_07_10_cli-and-commands-slash-commands-memory-other.md
  - agent_01_system-overview.md
  - agent_06_01_tool-execution-and-approval-execution.md
  - agent_04_02_state-and-persistence-history-compression.md
---

# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

Documents the purpose and side effects of slash commands in the Debug and Compact categories.

## Design Intent

### Debug Category

A group of commands related to debug mode and debug log verbosity.

| Command | Form | Effect |
|---|---|---|
| `/debug` | `/debug` | Toggles debug mode, which controls RAG pipeline step output, and reports ON or OFF |
| `/debug` | `/debug verbose` | Sets the debug loggers to the DEBUG log level |
| `/debug` | `/debug normal` | Restores the debug loggers to the INFO log level |

### Compact Category

`/compact` forces immediate compression of the conversation history through `HistoryManager.force_compress()` (see `agent_04_02_state-and-persistence-history-compression.md`). It reports "Nothing to compact" when the history is too short. Session export is not a separate slash command; it is the `export` action of `/session`.

RAG search is not provided as a slash command — it is automatically called by the LLM as the `rag_run_pipeline` tool during normal conversation (via MCP). There is no dedicated slash command for direct user invocation.

## Responsibility Boundary

- **Debug**: Debug mode and debug log verbosity
- **Compact**: History compression

## Known Limitations

## Keywords

- debug category
- compact category
