# Make DLQ requeue transactional, lock-safe, and timestamp-safe

## Priority
High

## Summary
Move the complete DLQ requeue state transition into one repository-owned transaction under one global-lock acquisition, return a typed result so the route performs no follow-up SQL, make DLQ list count and items one snapshot, and bind the requeue timestamp as a SQL parameter.

## Background
Confirmed against HEAD (adversarial re-verification):
- `redeliver_event()` in `scripts/eventbus/dlq_repo.py` runs an `UPDATE` of `dlq_requeue_count` and an `INSERT ... SELECT` of the redelivery row and calls `conn.commit()` only on the success path. There is no `rollback()` on any failure path. The shared connection is opened with Python's default `isolation_level` (`scripts/eventbus/db_conn.py`), so the `UPDATE` opens an implicit transaction that stays open if the `INSERT` raises, and the next request on the same connection can commit it.
- The `UPDATE`, `INSERT` and `commit` already run inside `run_with_db_lock` (`_redeliver` in `scripts/eventbus/dlq_route.py`), so concurrent requeues are already serialized. What runs outside the lock is only the follow-up SQL in the route: the `new_seq` lookup and the 404/409 reclassification (`db.execute(...)` after `run_with_db_lock` returns). `redeliver_event()` returns `(False, None)` for both "not found" and "already redelivered", which is why the route re-queries and can observe a different state than the repository did.
- `dlq_list()` calls `run_with_db_lock` twice (count, then fetch), so `total` and `items` are not one snapshot. `count_dlq` and `fetch_dlq` live in `scripts/eventbus/event_repo.py`.
- The timestamp fragment `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` is interpolated through an f-string when `now is None`. No caller passes `now` (the only production caller is `dlq_route.py`), so the injection boundary is latent: it exists only for a future caller that passes an explicit value, and the explicit-ISO path has never been exercised.
Aggregated from three memo items: atomic requeue, the global DB lock boundary, and parameterized requeue timestamps.

## Problem
A failed insert can leave an uncommitted `dlq_requeue_count` update on the shared connection, which a later request may commit. The requeue count, lineage row and returned sequence do not describe one atomic result. The route performs SQL outside the global lock and reclassifies 404/409 from a second, unlocked read. Separate count and page queries can return inconsistent pagination metadata. An optional timestamp is interpolated into SQL instead of bound as data (latent: no current caller passes one).

## Reason for Change
Partial success corrupts the operational audit trail (each committed `dlq_requeue_count` increment must correspond to exactly one redelivery row), and the shared-connection contract is violated on the route path.

## Implementation Intent
Keep the existing lineage model. Make the repository own the whole transition (update, insert, sequence lookup, commit/rollback, 404/409 classification) and return a complete typed result; the route only maps the result to HTTP. Timestamps are generated or accepted as data and bound as parameters. DLQ list reads count and items under one lock acquisition.

## Target Files or Areas
`scripts/eventbus/dlq_repo.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/event_repo.py` (`count_dlq`, `fetch_dlq`), `scripts/eventbus/db.py` (re-exports), `scripts/eventbus/route_helpers.py` (`run_with_db_lock`), tests `tests/eventbus/test_eventbus_dlq.py`, `test_eventbus_dlq_pagination.py`, `test_eventbus_requeue_edge_cases.py`, `test_eventbus_concurrent.py`, `test_eventbus_dlq_promotion.py`; design documents `docs/24_eventbus/` (DLQ/offset documents) and `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`.

## Required Changes
- Introduce a typed requeue result: status, original-event existence, already-redelivered state, new event ID, new sequence.
- Wrap the original-row update, redelivery insert, sequence lookup and commit in one explicit transaction; roll back on every update, insert, lookup or commit failure.
- Remove direct SQLite access from `dlq_route.py`; classify 404 and 409 inside the locked repository operation.
- Fetch DLQ `total` and `items` under one lock acquisition and one consistent snapshot.
- Bind the timestamp as a SQL parameter; use `now_iso()` or the schema default for the default path.
- Document the invariant that each committed requeue-count increment corresponds to exactly one redelivery row.

## Constraints
The HTTP contract of `/dlq/requeue` and `/dlq` (status codes, response fields `requeued`, `new_event_id`, `new_seq`) stays unchanged. SQLite access stays on the single shared connection guarded by the global DB lock.

## Acceptance Criteria
- The original-row update and the redelivery insert commit together or both roll back.
- A failed requeue leaves no active transaction on the shared connection and a later request cannot commit state left by it.
- `dlq_route.py` contains no direct SQLite calls.
- `new_event_id` and `new_seq` come from the same atomic result.
- DLQ `total` and `items` describe one snapshot.
- An explicit timestamp is parameterized and stored correctly; the default path uses `now_iso()` or the schema default.

## Testing Expectations
Regression and failure-injection tests: insert failure after the original-row update; commit failure with rollback verification; constraint failure; concurrent requeue requests; promotion while listing the DLQ; pagination snapshot consistency; default and explicit timestamp paths; connection remains usable after every failed path. Then ruff, mypy and the EventBus test directory.

## Documentation Impact
Yes: the DLQ requeue invariant (one committed increment equals one redelivery row), the transaction and lock boundary, and failure behavior in the EventBus DLQ design documents.

## Out of Scope
Requeue delivery semantics (live push versus replay) and DLQ file reconciliation (see the M-02 issue); NACK idempotency; schema changes.

## Dependencies
Siblings under `issues/`: none touch EventBus. Related memo tasks: H-04 and H-05 (same lock and connection model); M-02 (requeue delivery semantics). Fix order: this issue is independent and may go first.
Note: the memo's claim that concurrent requeue requests race is not confirmed for the update/insert path (serialized by the lock); concurrency tests should target the unlocked follow-up reads and the failed-transaction carry-over instead.
Note: the memo's claim that concurrent requeue requests race is not confirmed for the update/insert path (serialized by the lock); concurrency tests should target the unlocked follow-up reads and the failed-transaction carry-over instead.

## Unresolved Questions
- Does the explicit-timestamp parameter of `redeliver_event()` stay part of the repository API, or may it be removed (no caller passes it)? Needs confirmation; either choice satisfies the parameter-binding criterion.
- Should the typed result replace the `(bool, str | None)` return, or wrap it? Re-exports in `scripts/eventbus/db.py` must stay consistent.

## AI Implementation Instruction
- Read the listed implementation, tests, and design documents before editing; keep changes minimal and do not rewrite unrelated files.
- Preserve the existing public contract unless this issue explicitly names a contract change; an unresolved owner decision is reported, not guessed.
- Do not resolve an implementation defect by changing documentation alone.
- Keep transaction, locking, authorization, durability and fail-closed boundaries explicit.
- Add or update automated tests for every acceptance criterion; do not implement out-of-scope items.

## Traceability
- **Workflow phase**: `issue-creator` (converted from `memo-issue.md`, task `H-01`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-154325
- **Related target files**: `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/route_helpers.py`
