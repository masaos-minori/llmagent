# Replace fragmented CLI input and approval handling with one request-bound controller

## Priority
High

## Summary
Create one `ReplInputController` that owns stdin for normal prompts, multiline input, tool approval, Memory confirmation, and Ctrl-C handling, and remove delayed-input handoff, direct synchronous `input()` calls, and approval paths that are not bound to a specific request.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 1). Related archived work: `issues/done/20261104-112115_cliview002_stdin-line-lost-after-multiline-timeout.md`, `issues/done/20261003-180327_cliview001_multiline-input-timeout-crashes-repl.md`, `issues/done/20261021-093421_repl001_sigint-sigterm-never-reach-repl-input-loop.md` (re-verify against current source after them).

Evidence (`Explicit in code`, by reading and `rg`): `scripts/agent/stdin_reader.py` documents that a line arriving after its request was cancelled "goes to the newest pending request" (lines 39-43); `scripts/agent/commands/memory_data_ops.py:50` calls `input(prompt)` directly; `scripts/agent/signal_handler.py:61` registers the same `_sigterm_handler` for SIGTERM and SIGINT, and it sets the shutdown flag. The claims about CLIView policy, approval preview fallback, and the Windows ctypes fallback are from the backlog and `Needs confirmation`.

## Problem
A delayed line from a timed-out or cancelled request can be delivered to a newer waiter, so a stale `y` or `yes` can approve the wrong operation. Memory delete and prune use a second reader that competes for stdin and blocks the event loop. Ctrl-C always follows the shutdown path, so it cannot cancel only the current line, turn, or job. Approval preview behavior (fail-closed versus static fallback, redaction) is inconsistent.

## Reason for Change
Security and input-integrity risk on the approval boundary; later session, maintenance, and command work must use the corrected input model.

## Implementation Intent
Exactly one stdin read is active at a time and each result is delivered only to the request that started it; cancelled and timed-out input is discarded. Destructive confirmation and tool approval are bound to an immutable request id, risk level, and preview. Ctrl-C acts according to the active state. The view layer renders only.

## Target Files or Areas
- `scripts/agent/stdin_reader.py`, `cli_view.py`, `repl_input_loop.py`, `signal_handler.py`, `tool_approval.py`, `tool_output.py`
- `scripts/agent/commands/memory_data_ops.py`
- `docs/23_agent/agent_07_02_cli-and-commands-cliview.md`, `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` (the backlog's `docs/agent_07_*` paths do not exist)
- Tests: `tests/agent/test_stdin_reader.py` (exists); `tests/agent/test_tool_approval.py` (absent, create) and signal and Windows control-event tests

## Required Changes
- Introduce `ReplInputController` as the sole stdin owner; give each request a unique `request_id`, `prompt_kind`, creation time, operation id, and lifecycle state for normal, multiline, tool-approval, Memory-delete, and Memory-prune prompts.
- Bind a completed read to the waiter captured when it started; remove delivery to the newest waiter; discard results of timed-out or cancelled requests; remove all direct `input()` calls; allow at most one active read; refuse destructive confirmation while an older blocking read is unresolved.
- Return `completed`, `timed_out`, `cancelled`, `eof`, and `shutdown` outcomes; do not auto-submit partial multiline input (interactive: offer send, continue, discard; non-interactive: discard); keep CLIView to rendering.
- Approval: bind to request id and operation id; add required-versus-optional preview metadata; fail closed when a required HIGH-risk preview fails; make the MEDIUM fallback an explicit setting; build static previews from masked arguments; one secret masker for dry-run output and errors; redact before truncating; audit preview source, fallback reason, request id, and outcome without the answer text.
- Signals: prompt Ctrl-C discards input, turn Ctrl-C cancels the turn, job Ctrl-C requests job cancellation, Ctrl-D and `/exit` shut down normally, SIGTERM and console close begin graceful shutdown; fix the Windows ctypes fallback; define and test optional double-Ctrl-C force exit.

## Constraints
- Stdin is process-global; a blocking `input()` in a thread cannot be interrupted, so design for discard rather than cancel.
- Do not record answer text in audit.
- Windows behavior can only be tested through the control-event abstraction (`不明` for a real console).

## Acceptance Criteria
- [ ] Delayed `y` and `yes` cannot approve later operations; only one stdin reader exists per process.
- [ ] Memory confirmation cannot race with an existing stdin read; CLIView contains no input-state policy.
- [ ] Timed-out multiline input is never silently submitted.
- [ ] A required HIGH-risk preview cannot silently fall back; tokens, signed URLs, paths, and raw exceptions do not appear in approval prompts.
- [ ] Ctrl-C behavior depends on prompt, turn, job, or shutdown state as specified.

## Testing Expectations
- Multiline timeout followed by tool approval and Memory confirmation; consecutive approval requests with no answer crossover.
- Ctrl-C and SIGTERM for every prompt kind; required and optional preview failures by risk level; preview redaction before truncation; Windows control-event handling.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Remove the delayed-input handoff specification; update CLIView responsibility boundaries; document input outcomes, Ctrl-C semantics, and approval fail-closed behavior.

## Out of Scope
- Session transitions (`issues/20261119-145300_cliplc002_session-transition-generation.md`); maintenance jobs and job cancellation (`issues/20261119-145301_cliplc003_maintenance-job-framework.md`); shutdown deadline (`issues/20261119-145302_cliplc004_bounded-shutdown-machine.md`); command parsing and export (`issues/20261119-145309_cliplc011_export-command-contracts.md`).

## Dependencies
- Blocks `issues/20261119-145300_cliplc002_session-transition-generation.md`, `issues/20261119-145301_cliplc003_maintenance-job-framework.md`, `issues/20261119-145302_cliplc004_bounded-shutdown-machine.md`, and `issues/20261119-145309_cliplc011_export-command-contracts.md`.
- No open sibling issue or plan touches these files; archived siblings are listed above and must be re-verified.

## Unresolved Questions
- `不明`: whether a blocking read can be made interruptible on the target platforms or only discarded.
- `不明`: double-Ctrl-C force-exit policy and MEDIUM-fallback default.

## AI Implementation Instruction
Write the stale-`y` crossover and Memory-confirmation race tests first. Keep changes to the input, approval, signal, and Memory prompt paths. Do not reintroduce a second stdin reader. Stop and report if a Windows-only path cannot be tested.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145259
- **Related target files**: `scripts/agent/stdin_reader.py`, `scripts/agent/cli_view.py`, `scripts/agent/repl_input_loop.py`, `scripts/agent/signal_handler.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_output.py`, `scripts/agent/commands/memory_data_ops.py`
