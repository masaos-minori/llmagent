## Goal
- Close the `StateStore` that `SessionPersister.persist_session_diagnostics()` opens, on every exit path, without changing the reported values or the non-fatal posture (`REQ-001`: close on success, query failure, and guard paths; `REQ-002`: a failing close never escapes; `REQ-003`: tests for both).

## Scope
**Release unit**: N/A: not part of a release unit
- Edits `persist_session_diagnostics` in `scripts/agent/session_persister.py` and adds tests in the companion `tests/agent/test_session_persister.py`.
- `persist_session_memories` is not touched (procedures of the memlogleak001 Plan own it).

## Assumptions
- `StateStore.close()` delegates to `SQLiteHelper.close()`, which catches only `OSError`; a `sqlite3.Error` from the underlying connection can propagate, so the close must be wrapped.
- Compatible overlap with `plans/20261104-114342_memlogleak001_memory-persist-logs-messages.md` (same two files): that Plan edits `persist_session_memories` and adds tests in `TestPersistSessionMemoriesGate`; this change touches `persist_session_diagnostics` and adds a separate test class, so the regions are disjoint. If that Plan is implemented first, rebase this edit onto its result.
- `plans/20261105-085618_wfreview001_...` (archived) changes only the orchestrator and adds a new test file, so it does not collide.

## Design decisions
- Bind the store to a local `store` before the queries and close it in a `finally` that cannot raise: a failing `close()` is logged as a warning with the session id and swallowed.
- Keep the lazy runtime import of `StateStore` inside the `try` (the module avoids a circular import at module level); for typing, add the import to the existing `TYPE_CHECKING` block.

## Alternatives considered
- `contextlib.closing`: rejected because `StateStore` has no context-manager protocol and a close failure would still escape.
- Sharing the orchestrator's process-lifetime store: rejected because it changes ownership and is outside the Issue.

## Implementation
### Target file
`scripts/agent/session_persister.py`

### Procedure
1. Under the existing `if TYPE_CHECKING:` block add `from agent.workflow.state_store import StateStore`.
2. In `persist_session_diagnostics`, inside the `if session_id is not None:` block that currently runs the four queries, declare `store: StateStore | None = None` before the `try`, assign `store = StateStore()` where the instance is created today, and add a `finally` to that `try`.
3. The `finally` closes the store only when it is not `None`, calling `store.close()` inside `try/except (sqlite3.Error, OSError)`; on failure it logs `logger.warning("Failed to close workflow StateStore for session %s: %s", session_id, exc)`.

### Method
- Leave the `except (RuntimeError, sqlite3.Error): pass` clause and the `execute_attempts is None` guard exactly as they are; the `finally` runs after both.
- A constructor failure leaves `store` as `None`, so nothing is closed.
- Use the module's existing `%s` log style; no new import besides the `TYPE_CHECKING` one.

### Details
- Do not change any value of the summary: `task_count`, `workflow_count`, `retry_count`, `artifacts` are computed as before.
- The log call must not include the exception traceback; `logger.warning` with the message is enough.

### Companion test files
- `tests/agent/test_session_persister.py`
  - Procedure: add a class `TestPersistSessionDiagnosticsStoreClose` (new) after `TestPersistSessionDiagnosticsContainment`. Each test patches `agent.workflow.state_store.StateStore` inside the test with `patch(..., return_value=store)`, where `store = MagicMock(spec=StateStore)` (the spec makes a renamed getter fail the test); the inner patch overrides the `db` fixture's `RuntimeError` patch for the test's duration. Tests: `test_closes_store_on_success` (new): getters return ints and `[]`, assert `store.close.assert_called_once()`; `test_closes_store_when_a_query_raises_sqlite_error` (new): `get_task_count.side_effect = sqlite3.Error("db")`, assert one close and no exception; `test_closes_store_when_attempt_count_is_none` (new): `get_execute_attempt_count.return_value = None`, assert one close; `test_close_failure_is_logged_and_contained` (new): `close.side_effect = sqlite3.Error("close failed")`, run under `caplog.at_level(logging.WARNING, logger="agent.session_persister")`, assert the call returns normally, a warning mentions "close", and the summary row is still saved (`db.count() == 1`).
  - Validation: run the new class before the source edit and confirm the first three fail on the current code (no `close` call), then confirm all pass after it; `uv run pytest tests/agent/test_session_persister.py -v`.
  - Import `StateStore` for the spec inside each test or at module top from `agent.workflow.state_store`; the existing module-level patch targets stay unchanged.

## Compatibility considerations
- No public signature changes; the summary payload is identical. One extra connection close per session end.
- A close failure now produces a warning log line where before there was none.

## Security considerations
- N/A: no input, secret, or trust boundary involved; the log line carries the session id and an exception message only.

## Rollback considerations
- Revert the commit; the leak returns but nothing persistent changes.

## Validation plan
- `uv run pytest tests/agent/test_session_persister.py tests/agent/workflow tests/agent/test_repl_error_handling.py`.
- `uv run ruff check scripts/agent/session_persister.py tests/agent/test_session_persister.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `uv run python tools/check_module_size.py`; `uv run python tools/check_mock_patch_targets.py`.
- Structural check: `rg "StateStore\(\)" scripts/agent/session_persister.py` shows one construction, followed by a `finally` that closes it.

## Completion criteria
- `close()` is called exactly once on the success path, the query-error path, and the `None`-guard path; a raising `close()` leaves the method returning normally with a warning; all existing persister tests pass unchanged.

## Out of Scope
- Closing the orchestrator's `self._state_store`, `StateStore` API changes, and the session id semantics of the counts.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the close-spy tests to the companion file and confirm the first three fail on the current code | Pending | — | — | |
| 2 | Add the `TYPE_CHECKING` import and the non-raising `finally` close | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (close on every path), `REQ-002` (non-raising close), `REQ-003` (close-spy tests)
- **Source issue**: issues/20261103-134147_wfreview002_session-persister-state-store-connection-leak.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-085730_wfreview002_session-persister-state-store-connection-leak.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092514
- **Related target files**: `scripts/agent/session_persister.py`, `tests/agent/test_session_persister.py`
