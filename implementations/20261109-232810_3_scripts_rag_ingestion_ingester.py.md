## Goal

- Quarantine a URL group whose commit fails with a deterministic `sqlite3.IntegrityError` by routing the whole group to `failed/` with reason `STORAGE_FAILED`, while every other `sqlite3.Error` keeps today's retryable behavior (`REQ-003`: IntegrityError quarantine; `REQ-004`: transient errors unchanged; `REQ-005`: atomicity unchanged).

## Scope
**Release unit**: N/A: not part of a release unit

- The `TransactionManager.commit` call site in `RagIngester.ingest_url_group` in `scripts/rag/ingestion/ingester.py`.

## Assumptions

- Overlap judgment (vs `plans/20261108-170725_ragrev016_stale-recrawl-replaces-content.md`): `scripts/rag/ingestion/ingester.py` and `tests/rag/ingestion/test_ingester.py` are targets of both plans; judged a sequencing dependency, not a conflict — ragrev016's Scope states it must land after this plan's Phase 3 because both edit the same `commit` block. Keep the `commit(...)` call shape and its ignored return value `(doc_id, skip, replace)` unchanged here so the ragrev016 skip-handling adds on top cleanly.
- `TransactionManager.commit` runs inside `begin_immediate()` and the context manager rolls back on error (Plan Background; `scripts/rag/ingestion/transaction_commit.py` unchanged), so no manual rollback is added here.

## Design decisions

- Catch exactly `sqlite3.IntegrityError` and nothing else: only `IntegrityError` is a deterministic signal at commit time; the reproduction showed a dimension mismatch raises `OperationalError`, the same class as lock/IO errors (Plan Design Alternatives).
- Extract the commit-and-route block into a small private helper (`commit_url_group` (new)) returning the outcome, so `ingest_url_group` (already `radon` C (18)) does not grow (Plan Design).

## Alternatives considered

- Classify `OperationalError` by message text: rejected (sqlite-vec message text is not a contract, Plan Design Alternatives).
- Quarantine on any `sqlite3.Error`: rejected (a transient lock would quarantine good groups).

## Implementation
### Target file
- `scripts/rag/ingestion/ingester.py`

### Procedure
- Wrap the `tx_mgr.commit(...)` call (current L331-344) and the success routing at L345 in the new private helper; on `IntegrityError`, route the group to `failed/` with `STORAGE_FAILED` and return a failure result; re-raise every other `sqlite3.Error` unchanged.

### Method
- Add `RagIngester` method `commit_url_group` (new): builds `TransactionManager(db, doc_mgr, doc_store)`, calls `commit(...)` with the same arguments as today, and on success performs `self._file_router.route(prepared_paths, [])`.
- Inside it, `except sqlite3.IntegrityError:` → `self._route_group_failed([(p, IngestionFailureReason.STORAGE_FAILED) for p in prepared_paths])`, log the exception, return `False`; success returns `True`; any other `sqlite3.Error` propagates.
- `ingest_url_group` replaces its inline commit block with a call to the helper; on `False`, return `IngestUrlResult(url=url, n_success=0, n_failed=len(chunk_files), skipped=False, failure_reason=IngestionFailureReason.STORAGE_FAILED)` — the same result shape as the existing `GROUP_VALIDATION_FAILED` branch (L276-282).

### Details
- `_process_url_groups` (L401-422) stays untouched: `IntegrityError` no longer reaches it, and the `unexpected_failure` path for other errors (REQ-004/AC-4) is preserved exactly.
- `.error.json` metadata per file is written by `FileRouter.route` (existing `_route_group_failed` behavior); no new reason value (`STORAGE_FAILED` already exists in `scripts/rag/exceptions.py`).
- The group continues: `_process_url_groups` keeps iterating to the next group (AC-3).

## Compatibility considerations

- `tests/rag/ingestion/test_ingester.py::test_integrity_error_routes_to_failed_via_ingest_url_group` currently asserts propagation via `pytest.raises` and must be updated to assert the routing (plan AC-5 correction, seq-4 document); `TransactionManager`-level propagation tests stay valid.
- Ragrev016 phase 3 modifies this same block afterward; landing this document first keeps that edit additive.

## Security considerations
N/A: routing behavior on an existing DB error class; no new input surface.

## Rollback considerations
N/A: revert the single commit; quarantined `failed/` files are recoverable by moving them back (Plan Risks mitigation).

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingester.py -q` — the seq-4 integrity-error quarantine and transient-error tests fail on HEAD and pass after.
- `uv run pytest tests/rag/ingestion -q` regression (AC-5).
- `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- A forced `IntegrityError` routes every file of the group to `failed/` with `STORAGE_FAILED`, leaves no partial rows for the URL, and the run continues with the next group (AC-3); a forced `OperationalError` leaves files in place with the existing `unexpected_failure` result (AC-4).

## Out of Scope

- `TransactionManager.commit` internals, `FileRouter` internals, classifying `OperationalError` messages, consuming the `failed/` directory (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Confirm the tests added by the seq-4 document pass | Pending | — | — | Tests live in `tests/rag/ingestion/test_ingester.py` (own procedure document) |
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
- **Requirement ID**: `REQ-003` (quarantine IntegrityError groups), `REQ-004` (transient errors unchanged), `REQ-005` (atomicity unchanged)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `scripts/rag/ingestion/ingester.py`
