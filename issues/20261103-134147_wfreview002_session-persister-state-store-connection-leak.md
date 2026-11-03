# SessionPersister opens a StateStore for diagnostics and never closes it

## Priority
Medium

## Summary
`SessionPersister.persist_session_diagnostics()` constructs `StateStore()` to aggregate workflow statistics and never calls `close()`, leaking one write-mode SQLite connection to `workflow.sqlite` per persisted session. Wrap the store in a context-managed or `finally`-closed lifecycle.

## Background
Adversarial code review of `scripts/agent/workflow/` and its integration points (2026-11-03). Evidence:

- Confirmed: `scripts/agent/session_persister.py:88-107` — the diagnostics block does `from agent.workflow.state_store import StateStore; store = StateStore()` and then runs four queries; the `try` block has no `finally` and no `store.close()` call on any path.
- Confirmed: `scripts/agent/workflow/state_store.py:49-57` — `StateStore.__init__` opens the workflow database with `SQLiteHelper.open(write_mode=True, row_factory=True)`, and `close()` is the documented teardown.
- Confirmed: elsewhere the codebase does close stores it opens per operation: `scripts/agent/workflow_engine_adapter.py:292-326` (`_init_workflow_task` closes a store it created itself) and `scripts/agent/workflow_engine_adapter.py:255-259` (the `execute_turn` `finally` closes an owned store). The persister is the outlier.
- Confirmed: `tests/agent/test_session_persister.py` patches `StateStore` with mocks (`patch("agent.workflow.state_store.StateStore", ...)`), so the real open/close lifecycle is never exercised there.

## Problem
Every session that ends with diagnostics started leaks a write-mode connection. Over a long-running REPL or repeated batch invocations this accumulates open file handles and WAL readers on `workflow.sqlite`; nothing in the current code or tests detects it.

## Reason for Change
The fix is small and local, and connection lifecycle discipline is a stated resource rule for this codebase (stores opened by a caller are closed by the same caller, as the adapter demonstrates). Leaving it open also risks lock contention against the engine's `begin_immediate()` transactions while a stale write connection idles.

## Implementation Intent
Make the diagnostics store ownership explicit: create it inside a `try`/`finally` (or `contextlib.closing` if `StateStore` supports it) so `close()` runs on every exit path, including the `except (RuntimeError, sqlite3.Error)` path that currently swallows errors.

## Target Files or Areas
- `scripts/agent/session_persister.py`
- `scripts/agent/workflow/state_store.py` (only if a context-manager protocol is added there)
- `tests/agent/test_session_persister.py`

## Required Changes
- Close the `StateStore` instance created in `persist_session_diagnostics()` on all paths (success, DB error, and the `execute_attempts is None` guard path).
- Add a test that the created store's `close()` is called exactly once on both the success path and the DB-error path (a mock spy on `close` is sufficient; a real-DB variant is preferred if cheap).
- No behavior change to the values reported in the diagnostics summary.

## Constraints
- The diagnostics failure posture stays non-fatal: closing must not introduce a new exception path that escapes `persist_session_diagnostics()` (the module already logs-and-continues on store failures).
- Do not change `StateStore` ownership semantics for the engine/adapter path; this issue is scoped to the persister-owned instance.

## Acceptance Criteria
- A test asserts `close()` is called on both success and error paths of the diagnostics block.
- No unclosed `StateStore()` construction remains in `scripts/agent/session_persister.py`.
- Full workflow + persister test run and lint/type checks stay green.

## Testing Expectations
- Unit test with a mock store asserting exactly-once `close()` on the success path and on the `sqlite3.Error` path.
- Existing `tests/agent/test_session_persister.py` cases keep passing unchanged.
- Lint/type checks per `rules/toolchain.md`.

## Documentation Impact
No user-facing docs required. Optionally note the store-ownership rule (caller who opens a `StateStore` closes it) if the docs describe `StateStore` lifecycle in `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`.

## Out of Scope
- Whether `Orchestrator` should close its process-lifetime `self._state_store` (`scripts/agent/orchestrator.py:91`) at shutdown — that store lives for the process and is not a per-call leak; record as informational, not changed here.
- The session_id semantics of the aggregated counts (separate issue: `issues/20261103-134147_wfreview001_workflow-diagnostics-empty-session-id.md`).

## Dependencies
- Related (same function, independent fix): `issues/20261103-134147_wfreview001_workflow-diagnostics-empty-session-id.md`.

## Unresolved Questions
- N/A: none.

## AI Implementation Instruction
Keep the change minimal: ownership + `finally`-based close plus a close-spy test. Do not refactor the diagnostics block beyond what closing requires, and do not swallow close failures silently without logging.

## Traceability
- **Workflow phase**: `python-code-review` (adversarial review of `scripts/agent/workflow/` and integration points), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261103-134147
- **Related target files**: `scripts/agent/session_persister.py`, `scripts/agent/workflow/state_store.py`, `tests/agent/test_session_persister.py`
