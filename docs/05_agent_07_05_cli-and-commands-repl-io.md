---
title: "Agent CLI and Commands - REPL Input/Output Model"
category: agent
tags:
  - agent
  - cli
  - repl-io
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_05_cli-and-commands-repl-io.md
---

# Agent CLI and Commands

- System Overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

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

### Implementation Details

- The prompt is a property that returns a fixed value `"> "` without session ID; no dynamic string generation is performed. The notation `agent[:#N]>` which embeds the session_id does not exist in the current code.
- `CLIView.read_multiline()`'s multi-line continuation displays a `... ` prompt, but this is a continuation-specific prompt string inside `read_multiline` and does not change the REPL prompt itself. Once back to normal input, the fixed value `"> "` is used again.
- A `KeyboardInterrupt` while waiting for input is caught within the input process, outputs `write_turn_end()`, and returns `None`. Since the calling loop breaks upon receiving `None`, **Ctrl-C while waiting for input terminates the REPL similarly to EOF** (it does not just interrupt the current line and return to the prompt).
- Upon receiving SIGTERM, `shutdown_requested` and `_shutdown_event` are set, and the running turn is waited for up to 10 seconds (`_GRACEFUL_TIMEOUT`) before forced termination (graceful shutdown).
- `/exit` is determined by `_should_exit()`, which also determines loop termination if `shutdown_requested` is set.

## Responsibility Boundary

- `AgentREPL` is a thin coordinator; turn processing is delegated to the orchestrator, slash command dispatching to `CommandRegistry`, and terminal I/O to `CLIView`.

## Key Constraints

- The prompt is a fixed string `"> "` and does not dynamically display session ID or status.
- Ctrl-C while waiting for input terminates the entire REPL rather than interrupting the current line.

## Operational Notes

- The continuation prompt for multi-line input is `... `, which is different from the REPL prompt.
- Graceful shutdown timeout is 10 seconds.

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

REPL input/output model
