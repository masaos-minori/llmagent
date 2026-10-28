## Goal
Add tests that force the `events.redelivered_from` uniqueness violation and prove it maps to `already_redelivered` with a clean rollback, and that two concurrent connections produce exactly one redelivery (REQ-002, REQ-005).

## Scope
- Edit `tests/eventbus/test_eventbus_requeue_edge_cases.py` only: two new test functions and one small delegation wrapper class.
- Reference only: `scripts/eventbus/dlq_repo.py` (seq 02 adds the mapping), `scripts/eventbus/schema.sql` (seq 01 adds the index), existing fixtures/helpers in the same file (`client`, `_event`, `_get_field`, `_FailingConn`).

## Assumptions
- These tests fail before seq 01/02 land: the deterministic test asserts `already_redelivered` where current code raises `IntegrityError`. Sequence them after seq 01 and seq 02, or write them first and run them only after the code steps (Plan Phase 1 → 2 order).
- `open_db()` applies `schema.sql` and the WAL/busy_timeout pragmas on a fresh file (verified this cycle in `scripts/eventbus/db_conn.py` and `scripts/eventbus/schema.py`), so repo-level tests get the new index for free.
- The deterministic wrapper relies on the loser connection not starting its transaction before the competitor commits: the pre-check is a bare SELECT and python sqlite3 opens the transaction at the UPDATE (Plan Problem statement); the wrapper therefore injects the competitor right before delegating the UPDATE.

## Design decisions
- Two tests instead of one: a deterministic interleaving test carries the strict REQ-002/AC-2 assertions (exact rollback state), and the two-thread test carries only outcome invariants (REQ-005/AC-3) so it cannot flake on interleaving order — either the loser hits the pre-check or the index, and both yield `already_redelivered`.
- Repo-level (`dlq_repo.redeliver_event` with own `open_db` connections), not HTTP-level: the route layer and its lock are already covered by `test_second_requeue_of_same_event_rejected_after_first_redeliver`; the new violation path lives under the lock.

## Alternatives considered
- Sleep-based or event-based two-thread interleaving with strict ordering assertions: rejected — timing-coupled and flaky; the Plan Risk line requires outcome-only assertions in the concurrent test.
- Monkeypatching `dlq_route.redeliver_event` like the existing injection tests: rejected — injection tests fake the error; these tests must produce a real `UNIQUE constraint failed` from the real index.

## Implementation
### Target file
`tests/eventbus/test_eventbus_requeue_edge_cases.py`

### Procedure
1. Add a class `_RacingConn` (new) next to `_FailingConn`: wraps a real connection; on the first `execute` whose SQL begins with `UPDATE`, before delegating, runs on a second `open_db` connection to the same file an `INSERT INTO events (event_id, topic, payload, producer, redelivered_from) SELECT ?, topic, payload, producer, ? FROM events WHERE event_id = ?` with a fresh `uuid4().hex` and commits it; delegates all other calls.
2. Add `test_redelivered_from_violation_maps_to_already_redelivered(tmp_path)`: seed one event with `dlq_at` set via direct INSERT on `open_db(tmp_path)`; call `dlq_repo.redeliver_event(_RacingConn(conn, racer=other), event_id)`; assert `result.status == "already_redelivered"`, `result.already_redelivered is True`, `result.new_event_id is None`, `conn.in_transaction is False`, original `dlq_requeue_count == 0`, and exactly one row with `redelivered_from = event_id` (the competitor's); a follow-up `redeliver_event(conn, event_id)` returns `already_redelivered` via the pre-check (connection usable).
3. Add `test_two_connections_requeue_same_original_exactly_once(tmp_path)`: seed one DLQ event; start two `threading.Thread` workers, each with its own `open_db` connection, both calling `dlq_repo.redeliver_event(c, event_id)`; collect results; assert exactly one `success`, one `already_redelivered`, and exactly one row with `redelivered_from = event_id`.
4. Update the module docstring's test list sentence to name the new cases.

### Method
Reuse the file's existing repo-level pattern (seed via `open_db` + direct INSERT, assert via plain SELECT) from `test_second_requeue_of_same_event_rejected_after_first_redeliver`; no TestClient needed for the new tests.

### Details
- Seed INSERT must satisfy the `events` NOT NULL columns (`event_id`, `topic`, `payload`, `producer`; `published_at` has a schema default) and set `dlq_at` to a timestamp string so the UPDATE's `dlq_at IS NOT NULL` matches.
- New imports inside the new functions (local-import style used by the existing tests): `threading` (new), `uuid`, `db_conn.open_db`, `eventbus.dlq_repo`.
- The racer connection and the loser connection must be separate `open_db` connections to one file; close both at test end.

## Compatibility considerations
The three existing failure-injection tests must stay byte-identical; the new wrapper class must not alter `_FailingConn`.

## Security considerations
`nosec` stance mirrors the existing tests: fixed SQL templates in tests, parameterized values.

## Rollback considerations
N/A: delete the added tests and wrapper; revert the commit.

## Validation plan
- Before seq 01/02: `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q` shows the two new tests failing (Plan Phase 1 "fail before the change").
- After seq 01/02: same command all green; then `uv run pytest tests/eventbus tests/db tests/deploy -q`.
- Re-run the new tests 3 consecutive times to confirm no flakiness (Plan Risk mitigation).

## Completion criteria
- Both new tests pass deterministically, the existing 7 tests in the file are untouched and green, and the concurrent test's assertions name only outcome invariants.

## Out of Scope
Any change to production code (seq 01/02), other test files (seq 04/05), docs (seq 06-08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's change IS the tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Run red before seq 01/02, green after |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs handled by seq 06-08 |

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
- **Requirement ID**: REQ-002 (violation maps to `already_redelivered`), REQ-005 (concurrency outcome)
- **Source issue**: issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-200340
- **Related target files**: tests/eventbus/test_eventbus_requeue_edge_cases.py
