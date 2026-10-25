# Plan: Make DLQ requeue transactional, lock-safe, and timestamp-safe

## Goal
Make the DLQ requeue transition atomic, lock-bound, and free of SQL-injection surface by moving the whole state change into `scripts/eventbus/dlq_repo.py` as one transaction under one global-lock acquisition, returning a typed result so `scripts/eventbus/dlq_route.py` performs no follow-up SQL, snapshotting the DLQ list under one lock, and binding the requeue timestamp as a SQL parameter.

## Priority
High

## Scope
- **In-Scope**:
  - Introduce a typed requeue result (`status`, `original_event_exists`, `already_redelivered`, `new_event_id`, `new_seq`) in `scripts/eventbus/dlq_repo.py`.
  - Wrap the original-row update, redelivery insert, sequence lookup, and commit/rollback in one explicit transaction; roll back on every failure path.
  - Classify 404 vs 409 inside the locked repository operation; remove direct SQLite access from `scripts/eventbus/dlq_route.py`.
  - Fetch DLQ `total` and `items` under one lock acquisition and one consistent snapshot in `scripts/eventbus/dlq_route.py`.
  - Bind the requeue timestamp as a SQL parameter using `now_iso()` (or the schema default); keep the optional `now` argument bound as data.
  - Add regression and failure-injection tests for every acceptance criterion.
  - Document the requeue invariant and the transaction/lock boundary in the EventBus DLQ design documents.
- **Out-of-Scope**:
  - Requeue delivery semantics (live push versus replay) and DLQ file reconciliation (issue M-02).
  - NACK idempotency.
  - Schema changes.
  - Any change to the HTTP contract of `/dlq/requeue` and `/dlq` (status codes, response fields `requeued`, `new_event_id`, `new_seq`).
- **Dependencies**:
  - Siblings under `issues/`: none touch EventBus; this issue is independent and may go first.
  - Related memo tasks H-04 and H-05 share the same global-lock and single-shared-connection model but do not block this Plan.
  - M-02 (requeue delivery semantics) is referenced but does not block this Plan.

## Background
Confirmed against HEAD by adversarial re-verification (Step 2/Step 3):
- `redeliver_event()` in `scripts/eventbus/dlq_repo.py` runs an `UPDATE` of `dlq_requeue_count` (conditional on `dlq_at IS NOT NULL`) followed by an `INSERT ... SELECT` of the redelivery row, and calls `conn.commit()` only on the success path. There is no `conn.rollback()` on any failure path. The shared connection is opened with Python's default `isolation_level` (`scripts/eventbus/db_conn.py`), so the `UPDATE` opens an implicit transaction that stays open if the `INSERT` raises, and a later request on the same connection can commit it.
- The `UPDATE`, `INSERT`, and `commit` already run inside `run_with_db_lock` (`_redeliver` in `scripts/eventbus/dlq_route.py`). What runs outside the lock is only the follow-up SQL in the route: the `new_seq` lookup and the 404/409 reclassification via `db.execute(...)` after `run_with_db_lock` returns. `redeliver_event()` returns `(False, None)` for both "not found" and "already redelivered", which is why the route re-queries to distinguish 404 from 409.
- `scripts/eventbus/dlq_route.py::dlq_list()` calls `run_with_db_lock` twice (once for `count_dlq`, once for `fetch_dlq`), so `total` and `items` are not one snapshot.
- The timestamp fragment `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` is interpolated through an f-string when `now is None`. The only production caller is `scripts/eventbus/dlq_route.py`, and no caller passes `now`, so the injection boundary is latent.
- `get_seq()` already exists in `scripts/eventbus/event_repo.py` and can return the new row's sequence inside the same transaction. `now_iso()` in `scripts/eventbus/json_utils.py` produces the default timestamp. `redeliver_event()` is imported only through the `scripts/eventbus/db.py` re-export facade by `scripts/eventbus/dlq_route.py`; no test calls it directly.
- Aggregated from three memo items: atomic requeue, the global DB lock boundary, and parameterized requeue timestamps.

## Problem
A failed insert can leave an uncommitted `dlq_requeue_count` update on the shared connection, which a later request may commit. The requeue count, lineage row, and returned sequence do not describe one atomic result. The route performs SQL outside the global lock and reclassifies 404/409 from a second, unlocked read. Separate count and page queries can return inconsistent pagination metadata. An optional timestamp is interpolated into SQL instead of bound as data (latent: no current caller passes one).

## Reason for Change
Partial success corrupts the operational audit trail (each committed `dlq_requeue_count` increment must correspond to exactly one redelivery row), and the shared-connection contract is violated on the route path.

## Implementation Intent
Keep the existing lineage model. Make the repository own the whole transition — update, insert, sequence lookup, commit/rollback, and 404/409 classification — and return a complete typed result; the route only maps the result to HTTP. Generate or accept the timestamp as data and bind it as a parameter. Read DLQ `total` and `items` under one lock acquisition. Preserve the HTTP contract and the single-shared-connection + global-DB-lock model.

## Requirements
- `REQ-001`: `redeliver_event()` returns a typed result carrying status, original-event existence, already-redelivered flag, new event ID, and new sequence instead of the `(bool, str | None)` tuple.
- `REQ-002`: The original-row update, redelivery insert, sequence lookup, and commit run in one explicit transaction; any update, insert, lookup, or commit failure rolls back and leaves no active transaction on the shared connection.
- `REQ-003`: `scripts/eventbus/dlq_route.py` performs no direct SQLite access; 404 and 409 are classified from the typed result inside the locked repository operation.
- `REQ-004`: DLQ `total` and `items` are fetched under one lock acquisition and describe one consistent snapshot.
- `REQ-005`: The requeue timestamp is bound as a SQL parameter; the default path uses `now_iso()` or the schema default; the optional explicit timestamp (if passed) is stored as data.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified` per `issue-to-plan` Step 8; see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Modify | Add `RequeueResult` typed result; refactor `redeliver_event()` to own update+insert+seq-lookup+commit/rollback in one transaction, classify 404/409, and bind the timestamp as a parameter. | REQ-001, REQ-002, REQ-005 | `redeliver_event()` UPDATE (line 50-53) then INSERT (line 56-61) with `commit()` only on success, no rollback; f-string timestamp at line 48; only caller is `dlq_route.py` (checked in Step 3) | `test_eventbus_dlq.py`, `test_eventbus_requeue_edge_cases.py`, `test_eventbus_concurrent.py`, `test_eventbus_dlq_promotion.py` | Verified |
| `scripts/eventbus/dlq_route.py` | Modify | Remove `db.execute(...)` calls in `dlq_requeue` (new_seq lookup and 404/409 classification); map the typed result to HTTP. Combine `dlq_list` count and fetch under one `run_with_db_lock` call. | REQ-003, REQ-004 | `db.execute` at lines 86-91 (new_seq) and 94-96 (404/409) run after `run_with_db_lock` returns (unlocked); `dlq_list` calls `run_with_db_lock` at lines 39 and 40 (checked in Step 3) | `test_eventbus_dlq.py`, `test_eventbus_dlq_pagination.py` | Verified |
| `tests/eventbus/test_eventbus_dlq.py` | Add/modify | Cover successful requeue returning the typed result and `new_seq` from the same atomic result. | REQ-001, REQ-003 | Existing requeue endpoint tests exercise the current `(bool, str)` contract (checked in Step 3) | `scripts/eventbus/dlq_route.py` | Verified |
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Add/modify | Failure-injection tests: insert failure after the original-row update, commit failure with rollback verification, constraint failure, connection remains usable after every failed path. | REQ-002 | Current `redeliver_event()` has no rollback path (checked in Step 3) | `scripts/eventbus/dlq_repo.py` | Verified |
| `tests/eventbus/test_eventbus_concurrent.py` | Add/modify | Concurrent requeue requests; target the failed-transaction carry-over on the shared connection rather than the lock-serialized update/insert. | REQ-002 | Update/insert is serialized by `run_with_db_lock`; unlocked follow-up SQL exists in the route (checked in Step 3) | `scripts/eventbus/dlq_route.py`, `scripts/eventbus/dlq_repo.py` | Verified |
| `tests/eventbus/test_eventbus_dlq_promotion.py` | Add/modify | Promotion while listing the DLQ; verify `total` and `items` stay one snapshot. | REQ-004 | `dlq_list` acquires the lock twice (checked in Step 3) | `scripts/eventbus/dlq_route.py` | Verified |
| `tests/eventbus/test_eventbus_dlq_pagination.py` | Add/modify | Pagination snapshot consistency; default and explicit timestamp paths. | REQ-004, REQ-005 | `dlq_list` count/fetch split; timestamp interpolated via f-string (checked in Step 3) | `scripts/eventbus/dlq_route.py`, `scripts/eventbus/dlq_repo.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/db.py` | Re-export facade; confirm `redeliver_event` stays consistent and decide whether the typed result is re-exported (warning: no new functions added here). | `scripts/eventbus/dlq_repo.py`, REQ-001 |
| `scripts/eventbus/event_repo.py` | `get_seq()`, `count_dlq()`, `fetch_dlq()` reuse for in-transaction sequence lookup and the combined DLQ snapshot. | `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/dlq_route.py`, REQ-002, REQ-004 |
| `scripts/eventbus/route_helpers.py` | `run_with_db_lock()` semantics for the single-lock snapshot. | `scripts/eventbus/dlq_route.py`, REQ-004 |
| `scripts/eventbus/json_utils.py` | `now_iso()` default-timestamp generation. | `scripts/eventbus/dlq_repo.py`, REQ-005 |
| `scripts/eventbus/db_conn.py` | Shared connection lifecycle and default isolation_level model. | `scripts/eventbus/dlq_repo.py`, REQ-002 |
| `scripts/eventbus/ack_route.py` | `now_iso()` usage pattern reference. | `scripts/eventbus/dlq_repo.py`, REQ-005 |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | DLQ operations design doc to update with the invariant and transaction/lock boundary. | `scripts/eventbus/dlq_repo.py`, REQ-002 |
| `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | DLQ endpoint design doc to update with the no-direct-SQL route contract. | `scripts/eventbus/dlq_route.py`, REQ-003 |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | ADR to update with the requeue atomicity invariant. | `scripts/eventbus/dlq_repo.py`, REQ-002 |

## Acceptance Criteria
- The original-row update and the redelivery insert commit together or both roll back (REQ-002; AC ties to `test_eventbus_requeue_edge_cases.py`).
- A failed requeue leaves no active transaction on the shared connection and a later request cannot commit state left by it (REQ-002; `test_eventbus_concurrent.py`, `test_eventbus_requeue_edge_cases.py`).
- `scripts/eventbus/dlq_route.py` contains no direct SQLite calls (REQ-003; static `rg "db.execute" scripts/eventbus/dlq_route.py` yields nothing).
- `new_event_id` and `new_seq` come from the same atomic result (REQ-001, REQ-003; `test_eventbus_dlq.py`).
- DLQ `total` and `items` describe one snapshot (REQ-004; `test_eventbus_dlq_promotion.py`, `test_eventbus_dlq_pagination.py`).
- An explicit timestamp is parameterized and stored correctly; the default path uses `now_iso()` or the schema default (REQ-005; `test_eventbus_dlq_pagination.py`).

## Tests
- Regression test that a successful requeue returns the typed result with matching `new_event_id` and `new_seq` (REQ-001, REQ-003).
- Failure-injection test: insert failure after the original-row update rolls back the update and leaves the connection usable (REQ-002).
- Failure-injection test: commit failure rolls back and leaves no active transaction; a subsequent request on the same connection succeeds (REQ-002).
- Constraint-failure test: requeue that violates a constraint rolls back without partial state (REQ-002).
- Concurrent requeue requests against the shared connection do not carry a failed transaction across requests (REQ-002).
- Promotion while listing the DLQ keeps `total` and `items` consistent (REQ-004).
- Pagination snapshot consistency plus default and explicit timestamp paths (REQ-004, REQ-005).
- Then ruff, mypy, and the EventBus test directory.

## Documentation Impact
Yes. The EventBus DLQ design documents must record: the invariant that each committed requeue-count increment corresponds to exactly one redelivery row, the transaction and global-lock boundary, the route performing no direct SQLite access, and the failure/rollback behavior. Driven by REQ-002 and REQ-003. Target docs resolved via `docs/00_index.md` "Document References by Task" → the `eventbus` domain (currently `docs/24_eventbus/eventbus_03_dlq_operations.md`, `eventbus_04_dlq_endpoint.md`, and `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`).

## Assumptions
- The optional `now` argument of `redeliver_event()` is retained and bound as data (no caller passes it; keeping it avoids a breaking API change to the re-exported symbol). Resolves UNK-01.
- The typed result is defined in `scripts/eventbus/dlq_repo.py` and imported by the route directly from `eventbus.dlq_repo`; `scripts/eventbus/db.py` is not extended with a new function (its "do not add new functions" warning holds), so `redeliver_event` stays re-exported unchanged.
- The 404/409 distinction maps to `status="not_found"` (no row) → 404 and `status="not_in_dlq"` / `already_redelivered` (row exists, `dlq_at` NULL or `redelivered_from` present) → 409.
- The shared connection's default `isolation_level` is preserved; explicit `conn.rollback()` on failure paths is what prevents transaction carry-over.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the explicit-timestamp parameter of `redeliver_event()` stays part of the repository API or may be removed (no caller passes it). | No caller passes `now`; either choice satisfies REQ-005. | Keep the parameter bound as data; document the retention decision in the Plan/implementation procedure. | False |
| UNK-02 | Whether the typed result replaces the `(bool, str | None)` return or wraps it. | Re-exports in `scripts/eventbus/db.py` must stay consistent; only `dlq_route.py` calls the function. | Replace the return with the typed result; keep `redeliver_event` re-exported in `db.py`. Document in Design. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Modify | Medium — `redeliver_event()` return type changes; only `dlq_route.py` calls it, but the result flows through the `db.py` re-export facade. | 5 commits (30d) | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `scripts/eventbus/dlq_route.py` | Modify | Low — affects only `/dlq/requeue` and `/dlq` endpoints. | Low (not in top-churn list) | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_dlq.py` | Modify | Low — test-only. | N/A (Path B historical analysis limited) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Modify | Low — test-only. | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_concurrent.py` | Modify | Low — test-only. | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_dlq_promotion.py` | Modify | Low — test-only. | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_dlq_pagination.py` | Modify | Low — test-only. | N/A | N/A | not applicable (rsynced) |

## Design
Path B (affects more than 3 files and changes the runtime return contract of `redeliver_event()`; reclassified from the provisional Path A assessment in Step 3 because the typed-result return is a public/runtime-facing interface change even though the sole production caller is `dlq_route.py`). Full four-dimension analysis performed: architecture (imports confirmed; `lint-imports` boundary unchanged — no new layer), dependency graphing (`redeliver_event()` reached only via `eventbus.db.redeliver_event` → `dlq_route.py`; no other callers, tests, or external services), historical (30-day churn measured above; `dlq_repo.py` moderate, `dlq_route.py` low), operational (single shared connection, default isolation_level; no process holds DB locks at planning time — `fuser`/`ss` not run, no listener involved).

Key decisions:
- **Typed result shape.** Define a `RequeueResult` dataclass in `scripts/eventbus/dlq_repo.py` with fields `status` (`success` | `not_found` | `not_in_dlq` | `already_redelivered`), `original_event_exists: bool`, `already_redelivered: bool`, `new_event_id: str | None`, `new_seq: int | None`. The route maps `success` → 200 with `new_event_id`/`new_seq`, `not_found` → 404, `not_in_dlq`/`already_redelivered` → 409. This preserves the HTTP contract while removing the route's need to re-query.
- **Transaction ownership.** Within the existing `run_with_db_lock` closure, execute: concurrency guard (`redelivered_from` existence check) → conditional `UPDATE` → if `rowcount == 0`, classify via a single existence read and `rollback()` the no-match `UPDATE` → else `INSERT ... SELECT` + `SELECT seq` → `commit()`. Wrap in try/except `sqlite3.Error` → `rollback()` → re-raise, guaranteeing no dangling implicit transaction on the shared connection.
- **Sequence from the same result.** `new_seq` is read inside the same transaction (via `get_seq()` or an inline `SELECT`) so `new_event_id` and `new_seq` describe one atomic result (REQ-003).
- **Timestamp binding.** Compute `ts = now if now is not None else now_iso()` in Python and bind it as a `?` parameter in the `INSERT`; remove the `strftime(...)` f-string interpolation. The optional `now` argument is retained (UNK-01) and never interpolated into SQL.
- **Single-lock DLQ snapshot.** `dlq_list()` runs one `run_with_db_lock` closure that calls both `count_dlq()` and `fetch_dlq()` under one lock acquisition, returning `total` and `items` from one snapshot (REQ-004).
- **Re-export discipline.** `scripts/eventbus/db.py` keeps re-exporting `redeliver_event`; the typed result is imported by the route from `eventbus.dlq_repo`. No new function is added to the facade (resolves UNK-02).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Typed result and repository refactor** (`scripts/eventbus/dlq_repo.py`)
   - [ ] Add `RequeueResult` dataclass with `status`, `original_event_exists`, `already_redelivered`, `new_event_id`, `new_seq` (REQ-001).
   - [ ] Refactor `redeliver_event()` to run update+insert+seq-lookup+commit/rollback in one transaction; classify 404/409; bind the timestamp as a parameter via `now_iso()` or the optional `now` (REQ-002, REQ-005).
2. **Phase 2: Route cleanup** (`scripts/eventbus/dlq_route.py`)
   - [ ] Remove `db.execute(...)` calls in `dlq_requeue`; map `RequeueResult` to HTTP (200/404/409); keep the privileged-action audit on success (REQ-003).
   - [ ] Combine `dlq_list` count and fetch into one `run_with_db_lock` closure for one snapshot (REQ-004).
3. **Phase 3: Tests** (`tests/eventbus/test_eventbus_dlq.py`, `test_eventbus_requeue_edge_cases.py`, `test_eventbus_concurrent.py`, `test_eventbus_dlq_promotion.py`, `test_eventbus_dlq_pagination.py`)
   - [ ] Add regression and failure-injection tests covering every acceptance criterion (all REQs).
4. **Phase 4: Documentation** (`docs/24_eventbus/eventbus_03_dlq_operations.md`, `eventbus_04_dlq_endpoint.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
   - [ ] Document the requeue invariant, transaction/lock boundary, and failure behavior (REQ-002, REQ-003).
5. **Phase 5: Deployment & Verification**
   - [ ] Run ruff, mypy, bandit, `lint-imports`, the EventBus test directory, and diff-cover; confirm no direct SQLite remains in `dlq_route.py` and the shared connection stays usable after every failed path (all REQs). Deployment is a hand-off to `skills/deploy/SKILL.md`: commit and push first; deploying is the user's decision.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Unit: failure injection (insert/commit/constraint), rollback leaves no active transaction, connection reusable | `uv run pytest tests/eventbus/` | All pass; no uncommitted state carried across requests |
| `scripts/eventbus/dlq_route.py` | Integration: requeue HTTP mapping, no-direct-SQL, DLQ snapshot consistency | `uv run pytest tests/eventbus/` | 200/404/409 correct; `total`/`items` one snapshot |
| `scripts/eventbus/dlq_route.py` | Static: no `db.execute` remaining | `rg "db.execute" scripts/eventbus/dlq_route.py` | Zero matches |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean |

## Risks
- **Risk**: Changing `redeliver_event()`'s return type breaks an undiscovered caller. → **Mitigation**: `rg` confirms the only caller is `dlq_route.py` (via `db.py`); search covers `scripts/` and `tests/`; the re-export in `db.py` is the single entry point.
- **Risk**: An explicit `conn.rollback()` on a shared connection could interfere with concurrent requests sharing it. → **Mitigation**: rollback only aborts the current request's own implicit transaction; the shared connection itself is unaffected, and `run_with_db_lock` serializes access.
- **Risk**: The 404/409 classification inside the repo diverges from the current route behavior. → **Mitigation**: preserve the exact mapping (no row → 404; row with `dlq_at` NULL or `redelivered_from` present → 409) and cover it with tests.
- **Risk**: Transaction wrapping changes timing under the global lock and increases lock hold time. → **Mitigation**: the work was already inside `run_with_db_lock`; no additional locking is introduced; measure under the concurrency tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Typed result and repository refactor (`scripts/eventbus/dlq_repo.py`) | In Progress | — | — | Path B |
| 2 | Route cleanup: no-direct-SQL + single-lock snapshot (`scripts/eventbus/dlq_route.py`) | In Progress | — | — | Path B |
| 3 | Regression and failure-injection tests | In Progress | — | — | Path B |
| 4 | Documentation of invariant, transaction/lock boundary, failure behavior | Pending | — | — | Path B |
| 5 | Deployment & verification (ruff/mypy/bandit/lint-imports/pytest/diff-cover) | Pending | — | — | Path B |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |
| `implementations/20261025-131314_01_scripts_eventbus_dlq_repo.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261025-131314_02_scripts_eventbus_dlq_route.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261025-131314_03_tests_eventbus_test_eventbus_dlq.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261025-131314_04_tests_eventbus_test_eventbus_requeue_edge_cases.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261025-131314_05_tests_eventbus_test_eventbus_concurrent.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261025-131314_06_tests_eventbus_test_eventbus_dlq_promotion.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261025-131314_07_tests_eventbus_test_eventbus_dlq_pagination.py.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261023-154325_eventbus001_dlq-requeue-transactional.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-095644
- **Related target files**: `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/dlq_route.py`, `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/test_eventbus_concurrent.py`, `tests/eventbus/test_eventbus_dlq_promotion.py`, `tests/eventbus/test_eventbus_dlq_pagination.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; Summary | `scripts/eventbus/dlq_repo.py` | Step 1 | AC 1 | requeue returns typed result | Confirmed by repository evidence |
| REQ-002 | Required Changes; Problem; Reason for Change | `scripts/eventbus/dlq_repo.py` | Step 1 | AC 1, AC 2 | rollback + connection reuse | Confirmed by repository evidence |
| REQ-003 | Required Changes; Constraints | `scripts/eventbus/dlq_route.py` | Step 2 | AC 3, AC 4 | no-direct-SQL, same atomic result | Confirmed by repository evidence |
| REQ-004 | Required Changes | `scripts/eventbus/dlq_route.py` | Step 2 | AC 5 | DLQ snapshot consistency | Confirmed by repository evidence |
| REQ-005 | Required Changes; Unresolved Questions | `scripts/eventbus/dlq_repo.py` | Step 1 | AC 6 | parameterized timestamp | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261025-131314 -->