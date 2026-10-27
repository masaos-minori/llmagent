# Recover from transient memory-injection failure instead of disabling memory permanently

## Priority
Medium

## Summary
A single transient failure while injecting or reading agent memory permanently sets
`memory_disabled` for the whole REPL session. Make the failure recoverable: retry on
later turns, or provide an explicit reset path.

## Background
From a python-code-review pass over the REPL turn-execution path (finding F-004).
Evidence (Explicit in code):
- `scripts/agent/conversation_state_manager.py` sets `ctx.conv.memory_disabled =
  True` when memory context injection fails.
- `scripts/agent/startup_prompt_setup.py` sets it when startup memory reading
  fails.
- A repo-wide search finds no code path that ever sets it back to `False`; the
  user-facing warning is shown only once (`scripts/agent/repl_input_loop.py`).

## Problem
One transient SQLite error (e.g. lock contention, `sqlite-vec` load hiccup) silently
disables memory augmentation for the rest of the session. The user cannot re-enable
it without restarting the REPL, and the only signal was a single warning.

## Reason for Change
Silent capability loss degrades answer quality for the rest of a long session, and
the failure it guards against is typically transient. Current behavior treats a
transient fault as permanent.

## Implementation Intent
Treat `memory_disabled` as a per-turn condition rather than a session latch: attempt
injection again on subsequent turns (optionally with backoff), clear the flag when
an attempt succeeds, and make the degraded state visible in status output. If a
permanent disable is ever intended, expose it through an explicit user action
(e.g. a `/memory` subcommand) rather than an internal error path.

## Target Files or Areas
- `scripts/agent/conversation_state_manager.py` (injection failure handling)
- `scripts/agent/startup_prompt_setup.py` (startup read failure)
- `scripts/agent/repl_input_loop.py` (warning/flag display path)
- `scripts/agent/context.py` (`ConversationState.memory_disabled`)

## Required Changes
- Retry injection on later turns after a failure, and clear `memory_disabled` on
  success.
- Keep (or re-show) a degraded-state indicator while injection is currently failing.
- Add regression tests for: failure -> disabled -> next turn success -> re-enabled.

## Constraints
- Do not retry so aggressively that a persistent DB failure spams logs or stalls
  turns (bounded retries / backoff).
- Preserve current behavior for genuinely unrecoverable failures (memory stays off,
  with visible state).

## Acceptance Criteria
- After one failed injection followed by a successful one, memory injection is
  active again (test).
- While disabled, the state is visible to the user (status or warning path).
- Existing memory-injection tests pass unchanged.

## Testing Expectations
- Unit test simulating injection failure then success (flag transitions).
- Unit test that a persistent failure does not raise or spam (bounded retry).
- `mypy`/`ruff` pass.

## Documentation Impact
Document the memory-degraded state: when it appears, that it is retried, and how
the user can tell memory is currently not injected (failure behavior, operational
note).

## Out of Scope
- Memory subsystem internals (retrieval quality, storage schema).
- Startup abort policy changes.

## Dependencies
- N/A: none

## Unresolved Questions
- 不明: whether permanent disable was an intentional safety choice (stop injecting
  after any DB anomaly) — confirm before adding automatic retry.

## AI Implementation Instruction
Keep the change inside the injection-failure handling boundary; do not restructure
the memory subsystem. Retry must be bounded and logged at warning level only on
transition. Do not change startup abort semantics.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-224838
- **Related target files**: `scripts/agent/conversation_state_manager.py`, `scripts/agent/startup_prompt_setup.py`, `scripts/agent/repl_input_loop.py`, `scripts/agent/context.py`
