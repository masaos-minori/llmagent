## Goal

- Add a public staleness query to `ETagManager` built on `_incoming_decision` so `TransactionManager.commit` can decide about a stale payload before deleting, with no behavior change to `resolve_incoming` (`REQ-001`: staleness query; `REQ-004`: existing guard contract unchanged).

## Scope
**Release unit**: ragrev016-core

- One additive public method on `ETagManager` in `scripts/rag/ingestion/etag_manager.py`.

## Assumptions

- `_incoming_decision` (L83-98) already encodes the exact tri-state (True incoming wins / False stale / None both-`None`), verified against current source; the query only exposes it.
- The both-`None` case is not stale: the Plan keeps `resolve_incoming`'s both-`None` behavior out of scope (UNK-02).

## Design decisions

- The query returns `bool` (`True` only when the decision is stale): the both-`None` tri-state `None` maps to `False` because `commit` must not skip on a validator-less payload (REQ-004).
- Same validation contract as `resolve_incoming`: empty `new_fetched_at` raises `ValueError`, unparseable timestamps raise `InvalidIncomingTimestampError` / `InvalidStoredTimestampError` before any skip decision, so `commit`'s transaction aborts cleanly (mirrors L89-95).

## Alternatives considered

- Making `resolve_incoming` raise on stale: rejected by the Plan (it is the contract for metadata-only callers).

## Implementation
### Target file
- `scripts/rag/ingestion/etag_manager.py`

### Procedure
- Add `is_stale_incoming` (new) as a public method delegating to `_incoming_decision`.

### Method
- `def is_stale_incoming(self, etag: str | None, last_modified: str | None, new_fetched_at: str) -> bool:` returning `self._incoming_decision(etag, last_modified, new_fetched_at) is False`.
- No change to `update`, `resolve_incoming`, `_incoming_decision`, or `_is_stale_update`.

### Details
- Docstring states the tri-state mapping: incoming-wins and both-`None` both return `False`.
- `scripts/rag/ingestion/transaction_commit.py` is the only intended consumer (seq-2 document); `test_ingester_etag_guard.py` stays green (it tests `resolve_incoming`, untouched).

## Compatibility considerations

- Purely additive: no existing call site changes; `update()` and `resolve_incoming()` keep their contracts (AC-4).

## Security considerations
N/A: read-only freshness query.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py tests/rag/ingestion/test_ingester_etag_guard.py -q` (guard suite unmodified, AC-4).
- `uv run ruff check`, `uv run mypy`.

## Completion criteria

- `is_stale_incoming` returns `True` exactly when `resolve_incoming` would pick stored values due to staleness (not for both-`None`), and raises the same validation errors; both existing suites pass unmodified.

## Out of Scope

- The stale-skip decision itself (seq-2 document), the file/force exceptions, the both-`None` validator rule (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md phase 3 - both plans edit the `tx_mgr.commit(...)` block chain; land the commit-error handling first so the skip handling is added to the settled block |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Tests-first cases live in the seq-4 document |

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
- **Requirement ID**: `REQ-001` (public staleness query), `REQ-004` (guard contract unchanged)
- **Source issue**: issues/20261108-131235_ragrev016_stale-recrawl-replaces-content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170725_ragrev016_stale-recrawl-replaces-content.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-234108
- **Related target files**: `scripts/rag/ingestion/etag_manager.py`
