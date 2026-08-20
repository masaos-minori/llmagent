---
title: "Agent CLI and Commands - Purpose"
category: agent
tags:
  - agent
  - cli
  - purpose
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_04_cli-and-commands-purpose.md
---

# Agent CLI and Commands

- System Overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Documents the purpose and side effects of the REPL I/O model, CLIView responsibilities, multi-line input, and all slash command categories.

### Why this exists

As specified in the docstrings of `agent/repl.py`, `AgentREPL` is a thin coordinator; turn processing (LLM loop, tool calls) is delegated to `agent/orchestrator.py`, slash command dispatching to `agent/commands/registry.py`, and terminal I/O to `agent/cli_view.py`. Each file in this chapter reflects this separation of responsibilities.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

purpose
