## Goal
Map the `events.redelivered_from` uniqueness violation to the existing `already_redelivered` result in `redeliver_event()`, so the database (seq 01's index) is the enforcement layer while the result vocabulary and HTTP mapping stay unchanged (REQ-002).

## Scope
- Edit `scripts/eventbus/dlq_repo.py` only: one new `except` clause inside the existing `try` in `redeliver_event()` plus docstring wording.
- Reference only: `scripts/eventbus/schema.sql` (the index), `scripts/eventbus/dlq_route.py` (unchanged consumer), `tests/eventbus/test_eventbus_requeue_edge_cases.py` (seq 03 writes the tests).

## Assumptions
- sqlite3 reports the violation as `UNIQUE constraint failed: events.redelivered_from` on the local Python 3.13 SQLite build; the first implementation step confirms this text with a throwaway two-connection snippet or the seq 03 test before finalizing the matcher (Plan Assumption).
- The pre-insert check at lines 68-73 and the `not_in_dlq`/`not_found` classification at lines 83-94 stay exactly as they are.

## Design decisions
- Catch `sqlite3.IntegrityError` before the existing `except sqlite3.Error:` (lines 103-105) inside the same `try`, roll back, and return `already_redelivered` only when `"events.redelivered_from"` appears in the error message; every other error keeps the current rollback-and-raise path — so `test_requeue_insert_failure_rolls_back_and_keeps_connection_usable` (injected generic `IntegrityError("injected insert failure")`), `test_requeue_commit_failure_rolls_back_no_active_transaction` and `test_requeue_constraint_failure_rolls_back_without_partial_state` (real `event_id` collision) stay green as regression anchors.
- Return `RequeueResult("already_redelivered", True, True, None, None)` — the same tuple the pre-check path returns (line 73) — so `dlq_route.py` maps it to 409 with zero route changes.

## Alternatives considered
- `BEGIN IMMEDIATE` to serialize check-then-insert: rejected — the removed procedures invented it; it converts the loser into `SQLITE_BUSY` retry handling instead of a clean constraint result, and the index alone already closes the race (Plan Design Decision 4).
- Re-running a SELECT after the IntegrityError to re-classify: rejected — the constraint failure already names the violated index; no follow-up SQL is needed.

## Implementation
### Target file
`scripts/eventbus/dlq_repo.py`

### Procedure
1. Inside the `try` block of `redeliver_event()` (starts line 78), add before the existing `except sqlite3.Error:`:
   - `except sqlite3.IntegrityError as exc:` → `conn.rollback()` → if `"events.redelivered_from" in str(exc)`: `return RequeueResult("already_redelivered", True, True, None, None)`; else `raise`.
2. Reword the comment at line 66 ("Concurrency guard: ...") and the docstring paragraph (lines 60-64) so the pre-check is described as a fast classification path and the unique index `idx_events_redelivered_from` (new) as the enforcement layer.

### Method
Single added except clause ordered before the broader handler; preserve the existing rollback-before-decide behavior so no implicit transaction survives either path (the existing `in_transaction is False` assertions must hold).

### Details
- Current structure verified this cycle: `try` covers `UPDATE` (line 79), rowcount classification, `INSERT ... SELECT` (lines 95-100), `get_seq`, `commit`; one `except sqlite3.Error: conn.rollback(); raise` (lines 103-105).
- `get_seq` runs before `commit`, so a successful path is unchanged; the new except never reaches `get_seq`.

## Compatibility considerations
- `RequeueResult` fields and status strings unchanged; `dlq_route.py` untouched; HTTP 200/404/409 mapping unchanged (REQ-002).
- Callers see a new path that returns instead of raising only for the specific constraint; all other sqlite3 errors keep raising.

## Security considerations
N/A: no new inputs or SQL strings; the match is on an error message, not user data.

## Rollback considerations
Revert the commit: removing the except clause restores "every sqlite3.Error raises". A database already stamped 2 still has the index; behavior reverts to raising `IntegrityError` on a race — safe (fail loudly), but pair with seq 01's revert if rolling back fully.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q` (new tests from seq 03 plus the three existing failure-injection tests).
- `uv run pytest tests/eventbus tests/db tests/deploy -q`.
- `uv run ruff check scripts/ tests/`; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- A real `redelivered_from` violation returns `status == "already_redelivered"`, `already_redelivered is True`, connection `in_transaction is False`, no loser descendant row, original `dlq_requeue_count` unchanged.
- The three existing failure-injection tests still pass unmodified.
- POST `/dlq/{id}/requeue` in the violation path returns 409 (HTTP-level assertion in seq 03 if feasible at repo level only otherwise).

## Out of Scope
- Schema/index DDL (seq 01), test files (seq 03-05), docs (seq 06-08), `dlq_route.py`, transaction begin-mode changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-214500 | 20261028-214600 | Confirm the sqlite3 violation text first (Assumptions) except sqlite3.IntegrityError clause added before except sqlite3.Error; docstring and pre-check comment reworded (index = enforcement layer) |
| 2 | Add or update tests per Validation plan | Completed | — | — | Tests authored by seq 03 Tests authored by seq 03 (already in place) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-214600 | 20261028-215200 | sqlite3 message confirmed verbatim ('UNIQUE constraint failed: events.redelivered_from') in the pre-mapping red run; edge-cases file 10/10 green; 3 consecutive re-runs of the 2 new tests stable; full eventbus+db+deploy: 770 passed 1 skipped; ruff/mypy clean; bandit unchanged (3 Low findings, High severity 0) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Docs handled by seq 06-08 Docs handled by seq 06-08 |

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
- **Requirement ID**: REQ-002 (map the index violation to `already_redelivered`; other integrity errors still raise; vocabulary and HTTP mapping unchanged)
- **Source issue**: issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-200340
- **Related target files**: scripts/eventbus/dlq_repo.py