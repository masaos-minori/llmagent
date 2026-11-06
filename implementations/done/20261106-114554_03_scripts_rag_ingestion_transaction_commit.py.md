## Goal

Resolve incoming-vs-stored freshness inside `TransactionManager.commit`'s replace branch, before delete+insert, so freshness lands atomically with the chunk replacement and a stale payload can never regress stored values (REQ-003: commit-boundary guarded insert).

## Scope
**Release unit**: etag-atomic-fix

## Assumptions

- `resolve_incoming` is created by sibling procedure 02 (`implementations/20261106-114554_02_scripts_rag_ingestion_etag_manager.py.md`) — implement 02 first.
- Crawl/chunk payloads always carry a non-empty `fetched_at`; an empty one raises `ValueError` inside the transaction → rollback → the URL fails the run with no partial freshness write (Plan Assumption, falsifiable by REQ-004 tests).

## Design decisions

- Resolve against the current stored row via `ETagManager(self._db, doc_id).resolve_incoming(...)` before `delete_existing_document` (transaction_commit.py:61), then pass the resolved tuple to `DocumentStore.insert` (transaction_commit.py:62-71, document_persistence.py:77-95).
- Only the replace branch (`replace and doc_id is not None`) resolves against a stored row; the new-document branch keeps payload freshness unchanged.

## Alternatives considered

- Move the pre-commit UPDATE inside the transaction: rejected — the replace insert already carries payload freshness and would overwrite it (Plan Design).

## Implementation
### Target file
`scripts/rag/ingestion/transaction_commit.py`
### Procedure

- In `commit` (transaction_commit.py:37), inside `with self._db.begin_immediate():` (transaction_commit.py:57), on the replace branch before `delete_existing_document`: call `ETagManager(self._db, doc_id).resolve_incoming(etag, last_modified, fetched_at)` and use the returned `etag`/`last_modified`/`fetched_at` values in the `self._doc_store.insert(...)` call.
- Add the `ETagManager` import to this module.

### Method

- `commit`'s public signature stays unchanged (`etag`, `last_modified`, `fetched_at` parameters already exist at transaction_commit.py:48-51); only the values handed to `insert` change on the replace branch.
- `DocumentStore.insert` signature stays unchanged (document_persistence.py:77-95 — reference only, not modified).

### Details

- The resolution must happen inside `begin_immediate()` so the stored-row read and the insert share one transaction snapshot; no freshness write may land outside a committed transaction.

## Compatibility considerations

- Behavior change on stale/`etag`-less payloads: today they null/regress freshness via the insert; after this change stored values are carried (Plan Design — the guard contract the issue requires; pinned by REQ-004(d) tests and described in the REQ-005 doc update).
- Mock-based ingestion tests stub parts of this path; real-schema coverage is added in sibling procedure 04.

## Security considerations

N/A: value selection within an existing transaction; no new SQL surface (the insert SQL already carries these columns).

## Rollback considerations

N/A: revert the single commit (revert together with sibling procedures 01/02/04).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Integration | `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -v` | Failed re-ingestion leaves stored freshness unchanged; success path writes freshness atomically with chunks |
| Ingestion suite | `uv run pytest tests/rag/ingestion` | All green |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |

## Completion criteria

- AC-2: new freshness lands in the same transaction as the new chunks; no freshness write occurs outside it.
- AC-3: a transaction abort leaves both `documents` and `chunks` at pre-run values.
- AC-4: a stale payload cannot regress stored freshness on the replace path.
- AC-6: `uv run pytest tests/rag/ingestion` passes; diff-cover ≥ 90%.

## Out of Scope

- `ETagManager` guard logic itself (sibling procedure 02).
- `http_fetcher.py` conditional-request logic; retry/re-queue design (issue `20261106-073538_raging005_retry-dir-no-consumer.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-06 | 2026-11-06 | Requires sibling procedure 02 (`resolve_incoming`) to exist |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-06 | 2026-11-06 | Tests live in sibling procedure `implementations/20261106-114554_04_tests_rag_ingestion_test_ingestion_freshness.py.md` Tests in sibling procedure 04: TestFreshnessAtomicity fresh/stale/abort cases |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-06 | 2026-11-06 | Includes diff-cover ≥ 90% End-of-unit gate: ingestion suite 200/200; ruff/mypy/lint-imports/bandit/mock-patch/docstrings/module-size clean; full suite 11772 passed 9 skipped (deterministic order); diff-cover 100% (etag_manager.py, transaction_commit.py) |

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
- **Requirement ID**: `REQ-003` (guarded freshness resolution inside the commit transaction)
- **Source issue**: `issues/20261106-073538_raging002_etag-updated-before-reingestion.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094942_raging002_etag-updated-before-reingestion.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-114554
- **Related target files**: `scripts/rag/ingestion/transaction_commit.py`