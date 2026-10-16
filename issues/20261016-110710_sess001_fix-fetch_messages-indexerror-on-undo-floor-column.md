# Fix fetch_messages IndexError and out-of-context DB read

## Priority
High

## Summary
`SessionMessageRepository.fetch_messages()` has two defects. The first, an `IndexError` on a leftover line, fails 57 existing tests. The second, a messages query issued after the DB connection is closed, makes the method raise `RuntimeError` with the real `SQLiteHelper` and is hidden by the tests' fake helper. Fix both and add a test that does not mask the second one.

## Background
Found on 2026-10-16 while running the full suite for the pinned-memory change (`plans/done/20261016-093429_plan.md`). The same 57 tests fail with and without that change (confirmed by stashing the change), so they are unrelated to it. The `IndexError` was introduced by commit `646d97916` (`feat(agent): add /undo compression boundary and memory module operations`), whose diff for this file is exactly one added line reading `session_rows[0][1]`; the `/undo` floor itself came from `d578e4498`, which already read the floor as `session_rows[0][0]`. The second defect dates from `c9d564322` (2026-08-17), which moved the messages query out of the `with` block.

Adversarial verification on 2026-10-16 (results folded into the sections below): temporarily deleting the added line made all 113 tests in the four modules pass (57 previously failing), so the `IndexError` is the single cause of the 57 failures; a script using the real `SQLiteHelper` on a temporary DB showed that `fetchall()` after the `with` block raises `RuntimeError: DB not open`.

## Problem
In `scripts/agent/session_message_repo.py` `fetch_messages()`:
- The query is `SELECT undo_floor_message_id FROM sessions WHERE session_id = ?`, so each row has one column.
- The method reads `session_rows[0][0]` into `undo_floor`, then `session_rows[0][1]` into `undo_floor_message_id` when the session is found (line 215). Index 1 does not exist, so every call for an existing session raises `IndexError`.
- `undo_floor_message_id` is never used afterwards; the return value uses `undo_floor`. The line appears to be a leftover duplicate.
- Failing tests, all with the identical error (57 in total): `tests/agent/test_session_message_repo.py` (29), `tests/agent/test_agent_session.py` (18), `tests/agent/test_history_compression_consistency.py` (6), `tests/agent/test_regression_undo_artifact.py` (4).
- Second defect (confirmed with the real helper, not through `fetch_messages()` itself): `SQLiteHelper.__exit__` closes the connection and resets it to `None`, but `fetch_messages()` runs the messages query `rows = db.fetchall(...)` after the `with` block. `fetchall()` then raises `RuntimeError: DB not open — call open() first`. This path is reached only for an existing session, so fixing the `IndexError` alone does not make restore work against a real DB.
- The tests do not see the second defect: they patch `SQLiteHelper` with a fake that never closes the connection (`tests/agent/test_session_message_repo.py`), which is why the four modules pass once the first defect is removed.
- `fetch_messages()` is called by `scripts/agent/session.py` and `scripts/agent/services/session_restore.py` (`restore_session`), and `restore_session` has no handler for these exceptions, so restoring an existing session is expected to fail at runtime. The exact user-facing effect through `cmd_session.py` and whether a caller above it catches the error were not run (unknown).

## Reason for Change
Session restore for any existing session is expected to raise, which is a correctness failure in a core path. 57 red tests hide other regressions, and the fake-helper tests would keep passing while the real path stays broken.

## Implementation Intent
- Remove the duplicate, unused read so the method has one source for the undo floor, and run the messages query while the connection is still open, and keep the documented return contract: `(messages, session_found, undo_floor_message_id)` with `([], False, 0)` for a missing session and `([], True, 0)` for a session with no messages.
- Add one test that exercises `fetch_messages()` through a helper that really closes its connection on exit, so the second defect cannot pass unnoticed again.
- Re-run the four test modules; if a remaining failure has a different cause, record it instead of widening the change.

## Target Files or Areas
- `scripts/agent/session_message_repo.py` (`fetch_messages`)
- `tests/agent/test_session_message_repo.py`, `tests/agent/test_agent_session.py`, `tests/agent/test_history_compression_consistency.py`, `tests/agent/test_regression_undo_artifact.py` (verification; change only if a test itself is stale)

## Required Changes
- Delete the out-of-range read in `fetch_messages()` (line 215 at the time of writing; verified to be the only cause of the 57 failures).
- Move the messages query inside the `with SQLiteHelper(...)` block (or otherwise keep the connection open for it), without changing the return contract.
- Add a regression test using a closing helper (see Testing Expectations).
- Check whether the return paths `([], True, 0)` for an empty session should return the persisted undo floor instead of 0, against the docstring and `session_restore.py` use; do not change it without a failing test or documented contract that requires it.

## Constraints
- Keep the `fetch_messages()` signature and return type unchanged.
- No compatibility shims; do not touch the `sessions` schema.
- Tests must not open production DBs.

## Acceptance Criteria
- `fetch_messages()` no longer raises for an existing session, both with the test fake and with a helper that closes its connection on exit.
- The 57 tests listed in Problem pass.
- The full suite shows no new failure compared with the 57-test baseline.
- `ruff`, `mypy --no-namespace-packages scripts/`, and `lint-imports` report no new findings.

## Testing Expectations
- Run the four failing test modules, then the full suite once.
- Add a test that patches `SQLiteHelper` with a fake whose `__exit__` closes the connection and whose `fetchall()` raises when it is closed; it must fail before the fix and pass after.
- If no existing test covers a session with a non-zero undo floor returning that floor from `fetch_messages()`, add one at the repository boundary.

## Documentation Impact
Not expected. Check that the `fetch_messages` docstring still matches the behavior; update `docs/*.md` only if a documented contract changes.

## Out of Scope
- The pinned-memory retrieval change and mem001 (`/memory` specification).
- Redesigning the `/undo` compression floor.
- Production deployment.

## Dependencies
- Related to the `/undo` floor work in commits `d578e4498` and `646d97916`; no open issue under `issues/` covers this failure (checked: only mem001 and mcp004 are open, neither touches `session_message_repo.py`).
- Re-verify against current source if another change touches `session_message_repo.py` before this is picked up.

## Unresolved Questions
- Resolved by verification: `fetchall()` after the `with` block is not safe with the real helper; it raises `RuntimeError` (see Problem). Whether any code path or release already ran this against a real DB successfully is unknown.
- Whether other methods of `SessionMessageRepository` (or other classes using `SQLiteHelper`) also query after the `with` block. Not checked; out of scope here unless found in the same method.
- Whether `([], True, 0)` for an existing session with no messages should carry the stored undo floor. Assumed to stay 0 unless a test or contract says otherwise.
- Resolved by verification: the four modules have no failure other than the `IndexError`; with the added line deleted, 113 passed.

## AI Implementation Instruction
Fix only the out-of-range read and the out-of-context messages query described above. Do not refactor `session_message_repo.py`, do not alter the return contract, and ask if a remaining failure has a different cause. Never touch `/opt/llm`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-110710
- **Related target files**: scripts/agent/session_message_repo.py, tests/agent/test_session_message_repo.py, tests/agent/test_agent_session.py, tests/agent/test_history_compression_consistency.py, tests/agent/test_regression_undo_artifact.py
