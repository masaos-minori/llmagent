# `TestPersistSessionDiagnostics` patches the wrong logger module for the sensitive-fields warning

## Priority
Medium

## Summary
`TestPersistSessionDiagnostics::test_warns_when_artifacts_present` and
`::test_warns_when_rag_stage_outcomes_present` (`tests/agent/test_repl.py`) fail with
`AssertionError: Expected 'warning' to have been called once. Called 0 times.` — even
though the captured log output shows the expected warning ("Session diagnostics contain
sensitive fields...") was actually emitted. Confirmed wrong-mock-patch-target: the tests
patch `agent.wal_checkpoint_manager.logger`, but the warning is emitted via
`scripts/agent/session_persister.py`'s own module-level
`logger = logging.getLogger(__name__)`.

## Background
Confirmed by the captured log line itself in the test failure output:
`agent.session_persister:session_persister.py:141`. The warning fires correctly in
production; only the test's `mock.patch(...)` target is wrong — the same class of
defect as `diagstore01` (patching the wrong module for a logger/dependency), though a
different pair of modules is involved here (`wal_checkpoint_manager` vs.
`session_persister`).

## Problem
Both tests patch `"agent.wal_checkpoint_manager.logger"` (or an equivalent
`mock_logger` fixture bound to that module), expecting to intercept the sensitive-fields
warning. Since the warning is actually logged through
`session_persister.py`'s own module-level logger, the patch never observes the call —
the mock's `.warning` is never invoked because it is watching the wrong object
entirely.

## Reason for Change
2 tests intended to verify that persisting session diagnostics containing sensitive
fields (artifacts, RAG stage outcomes) triggers a warning currently provide no real
coverage of that behavior — they fail regardless of whether the warning logic is
correct, and would also silently stop catching a real regression in the warning logic
itself (a false negative risk) if the patch target were left wrong indefinitely.

## Implementation Intent
Change the patch target in both tests from `agent.wal_checkpoint_manager.logger` to
`agent.session_persister.logger` (matching where the warning is actually emitted).
Confirm no other assertion in these two tests implicitly depends on the wrong module
being patched (e.g. no assertion checks `wal_checkpoint_manager`-specific behavior that
happens to also need mocking).

## Target Files or Areas
- `tests/agent/test_repl.py` (`TestPersistSessionDiagnostics::test_warns_when_artifacts_present`,
  `::test_warns_when_rag_stage_outcomes_present`)
- `scripts/agent/session_persister.py` (reference only — confirms the actual
  module-level `logger` binding and the warning's exact log line; not a modification
  target)

## Required Changes
- Change both tests' `mock.patch(...)` target from `agent.wal_checkpoint_manager.logger`
  to `agent.session_persister.logger`.
- No change to `scripts/agent/session_persister.py`.

## Constraints
Do not modify `scripts/agent/session_persister.py`'s warning logic or message text —
the warning itself is confirmed correct; only the test's patch target is wrong.

## Acceptance Criteria
- [ ] Both tests patch `agent.session_persister.logger`
- [ ] `uv run pytest "tests/agent/test_repl.py::TestPersistSessionDiagnostics" -q`
  passes for both cases
- [ ] No change to `scripts/agent/session_persister.py`

## Testing Expectations
- `uv run pytest "tests/agent/test_repl.py::TestPersistSessionDiagnostics" -q` — both
  cases pass with the mock now actually observing the emitted warning

## Documentation Impact
N/A: test-only patch-target fix; no documented behavior change.

## Out of Scope
- `TestGetWorkflowStatus`'s 2 failures — tracked separately as `repl002`.
- `TestRunSqliteErrorMessage`'s 2 failures — tracked separately as `repl004`.
- `TestSigtermHandlerTurnActiveGuard`'s 1 failure — tracked separately as `repl005`.
- Any change to `scripts/agent/session_persister.py`.

## Dependencies
N/A: none. Discovered while investigating `test_repl.py`'s post-`repl001`-fix remaining
failures — independent of that fix.

## Unresolved Questions
N/A: none — root cause confirmed directly from the captured log line in the test's own
failure output.

## AI Implementation Instruction
Change only the two `mock.patch(...)` target strings; do not modify
`scripts/agent/session_persister.py` or the warning message text.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260909-130453
- **Related target files**: see Target Files or Areas above
