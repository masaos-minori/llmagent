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
- **Multi-line Input:** Lines ending with `\` → continued with `... ` prompt; the continuation is collected by the input controller and bounded by a timeout, and partial text is never submitted automatically after a timeout (interactive: send, continue, or discard is offered; non-interactive: discarded) (`TestMultilineTimeoutThenNextPrompt`)
- **EOF / Ctrl-D:** Graceful shutdown (REPL input returns `None` and exits the loop)
- **Ctrl-C:** Acts by input state (`ReplInputController.handle_interrupt`): at the prompt it discards the line and prompts again, during a turn it cancels only that turn, during a maintenance job it requests job cancellation (the job seam is wired by the maintenance-job work), and while shutdown is in progress it requests an interrupt on the step in progress; the process exits through the force-exit path only when `shutdown_force_exit_on_second_sigint` is true (`TestInterruptByState`)
- **Ctrl-D, `/exit`, SIGTERM, console close:** Ctrl-D (EOF) and `/exit` end the loop normally; SIGTERM and the Windows close, logoff, and shutdown events begin graceful shutdown. Every shutdown request arms one deadline (`shutdown_deadline_seconds`) that later requests cannot extend (`TestSignalDuringPromptEndsLoop`)
- **Input Controller:** `ReplInputController` (`agent/repl_input_controller.py`) is the only owner of stdin. Every prompt (normal, multiline, tool approval, Memory delete, Memory prune) is one immutable request with a request id, kind, creation time, and operation id, and ends with exactly one outcome: `completed`, `timed_out`, `cancelled`, `eof`, or `shutdown`. At most one request is active, and a destructive confirmation is refused while an earlier blocking read is unresolved (`TestSingleOwner`)
- **Input Reader:** Reads run on one daemon reader thread, not on the loop executor, so a read that is cancelled or still pending when the loop exits does not hold the process open (`TestPromptReadDoesNotUseAnExecutor`, `TestAbandonedReadDoesNotDelayProcessExit`)
- **Late Lines Are Discarded:** A read result is delivered only to the request that started it. A line that arrives after its request timed out or was cancelled is dropped and never reaches a later prompt, so a stale `y` cannot answer an approval or confirmation (`TestCancelledRequestDelivery`). A blocking stdin read cannot be interrupted, so the abandoned read still owns the terminal line: the next line typed after Ctrl-C or a timeout is consumed and dropped before the following prompt reads, and the prompt says so

### Shutdown Behavior

- On SIGTERM the `shutdown_requested` flag and the shared shutdown event are set. At the prompt this ends the loop immediately (`TestSignalDuringPromptEndsLoop`); during a turn the in-flight dispatch is cancelled and the wait for that cancellation is bounded by the remaining time of the armed shutdown budget, falling back to `_GRACEFUL_TIMEOUT_S` when no budget is attached to the loop (`TestMidTurnSignalIsBounded`). `/exit` and the shutdown flag both end the loop (Explicit in code — `scripts/agent/repl.py`). Process exit time is bounded by this shutdown path, not by a keystroke arriving at an idle prompt (`TestAbandonedReadDoesNotDelayProcessExit`).
- Once the shutdown phase is draining, new commands and turns are refused with one warning line stating the phase, and refused writes are counted in the shutdown report. A pending approval or confirmation whose read is still open when shutdown begins resolves with the `shutdown` outcome.

## Responsibility Boundary

- `AgentREPL` is a thin coordinator; turn processing is delegated to the orchestrator, slash command dispatching to `CommandRegistry`, and terminal I/O to `CLIView`.

## Key Constraints

- The prompt is a fixed string `"> "` and does not display session ID or status; the `... ` continuation prompt is specific to multi-line input.
- Ctrl-C does not end the REPL by itself except through the configured force-exit opt-in: it discards the prompt line, cancels the current turn, requests job cancellation, or requests an interrupt on the shutdown step in progress, and it forces process exit only when `shutdown_force_exit_on_second_sigint` is true and shutdown is already in progress; otherwise only SIGTERM, console close, Ctrl-D, and `/exit` shut down (`TestInterruptByState`, `test_configured_force_exit_is_read_once_at_construction`).

## Keywords

- REPL input/output model
