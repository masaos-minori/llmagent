# Implementation Procedure: dlq_repo.py outbox row operations

## Goal

Add the `dlq_outbox` (new) row operations to `scripts/eventbus/dlq_repo.py` so the worker and
reconciliation access the outbox through the existing DLQ data-access module (REQ-002,
REQ-004, REQ-005, REQ-007; plan AC-1, AC-4, AC-5).

## Scope

**In scope:**
- Six new repo functions (list in Design decisions) operating on `dlq_outbox` (new).

**Out of scope:**
- `redeliver_event` (`dlq_repo.py:43`) and the requeue transaction — unchanged.
- Worker/promotion logic (row 03), config (row 07).

## Assumptions
- Verified at HEAD `124e340b4`: `dlq_repo.py` is 123 lines; `redeliver_event` at `:43` is the
  existing DLQ data-access precedent (plain `sqlite3.Connection` parameterized SQL).
- `dlq_outbox` (new) exists (rows 01/02 or test-harness schema).

## Design decisions
- `insert_outbox_row(db, event_id, requested_at) -> None` (new): `INSERT INTO dlq_outbox
  (event_id, requested_at, status, attempts) VALUES (?,?, 'pending', 0)` — called inside the
  caller's promotion transaction only (never commits itself; REQ-002 atomicity lives with the
  `dlq_at` UPDATE).
- `fetch_due_pending(db, now_iso) -> list[sqlite3.Row]` (new): `SELECT ... WHERE status =
  'pending' AND (next_attempt_at IS NULL OR next_attempt_at <= ?) ORDER BY requested_at`.
- `mark_done(db, event_id, completed_at) -> None` (new).
- `record_attempt_failure(db, event_id, last_error, next_attempt_at, terminal: bool) -> None`
  (new): `attempts = attempts + 1`, set `last_error`, `next_attempt_at` (new); when `terminal`,
  `status = 'failed'` — one locked transaction per failed event (REQ-005).
- `get_outbox_state(db, event_id) -> sqlite3.Row | None` (new) — reconcile/lookup helper.
- `done_outbox_event_ids(db) -> set[str]` (new) — the done-set used by the orphan classifier
  in row 03 (REQ-007).
- All functions are sync, parameterized, no internal `commit()` except none: commit lives in
  the caller's locked closure (row 03 `run_locked` (new) steps), mirroring `redeliver_event`'s
  caller-managed transaction style.

## Alternatives considered
- Putting outbox SQL inline in `dlq.py`: rejected — the frozen target table assigns outbox
  row operations to `dlq_repo.py` (module boundary already owns DLQ requeue data access).

## Implementation
### Target file
`scripts/eventbus/dlq_repo.py`

### Procedure
1. Append the six functions with docstrings in the module's existing style.

### Method
Pure additions; no existing function touched.

### Details
- Column names as literals in constant SQL fragments (`# nosec B608` convention where a
  fragment is concatenated).
- `fetch_due_pending` (new) returns whole rows so the worker reads `event_id`, `attempts` without a
  second query.

## Compatibility considerations
- New module surface only; existing importers unaffected.

## Security considerations
- Parameterized values only; `last_error` text is written by the worker from local OSErrors.

## Rollback considerations
- Removing these functions requires reverting row 03 (their only caller) in the same commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_dlq_outbox.py` (row 10 exercises every
  function through the worker) and `tests/eventbus/test_eventbus_dlq.py` (promotion insert).

## Completion criteria
- Pending→done/failed lifecycle, attempt/backoff persistence, and done-set lookup all work
  through repo functions with no commits outside caller transactions.

## Out of Scope
- Worker loop and backoff arithmetic (row 03), wiring (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the six outbox repo functions | Pending | — | — | |
| 2 | Run row 10/09 tests green | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-004`, `REQ-005`, `REQ-007`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `scripts/eventbus/dlq_repo.py`
