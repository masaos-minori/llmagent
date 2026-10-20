---
title: "Agent CLI and Commands - REPL Input/Output Model"
area: agent
tags:
  - agent
  - cli
  - repl-io
related:
  - agent_00_document-guide.md
  - agent_07_01_cli-and-commands-cli-reference.md
  - agent_07_02_cli-and-commands-cliview.md
  - agent_07_03_cli-and-commands-command-registry.md
  - agent_07_04_cli-and-commands-purpose.md
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

Documents the design intent and operational decisions for the REPL input/output model.

## Design Intent

### REPL Input/Output Model

- **Prompt:** `> ` (fixed string)
- **Normal Input:** Any text → forwarded to `Orchestrator.handle_turn()`
- **Slash Commands:** Lines starting with `/` → `CommandRegistry.dispatch(line)`
- **Multi-line Input:** Lines ending with `\` → continued with `... ` prompt
- **EOF / Ctrl-D:** Graceful shutdown (REPL input returns `None` and exits the loop)
- **Ctrl-C:** Caught within input; during input wait, it leads to REPL termination similar to EOF (handled differently from interruption during tool loop execution in current implementation)

### Shutdown Behavior

- On SIGTERM the shutdown flag and event are set, and the running turn is awaited for a bounded grace period (`_GRACEFUL_TIMEOUT_S`) before forced termination. `/exit` and the shutdown flag both end the loop (Explicit in code — `scripts/agent/repl.py`).

## Responsibility Boundary

- `AgentREPL` is a thin coordinator; turn processing is delegated to the orchestrator, slash command dispatching to `CommandRegistry`, and terminal I/O to `CLIView`.

## Key Constraints

- The prompt is a fixed string `"> "` and does not display session ID or status; the `... ` continuation prompt is specific to multi-line input.
- Ctrl-C while waiting for input terminates the entire REPL rather than interrupting the current line.

## Keywords

- REPL input/output model
