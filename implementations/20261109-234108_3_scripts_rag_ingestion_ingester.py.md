## Goal

- Make `RagIngester.ingest_url_group` read `TransactionManager.commit`'s outcome and treat a stale skip as a skip: distinct warning log, existing registered-skip routing, and a skip result (`REQ-003`: stale-skip handling in the ingester).

## Scope
**Release unit**: ragrev016-core

- The commit-outcome handling in `ingest_url_group` in `scripts/rag/ingestion/ingester.py`, plus its companion test file.

## Assumptions

- Sequencing (Plan Scope dependency + gated state): this document is implemented after `plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md` phase 3 — its seq-3 document creates the `commit_url_group` helper around the same call site; the skip-outcome read is added inside that settled helper. Overlap judgment for `ingester.py` and `tests/rag/ingestion/test_ingester.py`: sequencing dependency, not a conflict (recorded in both plans' Assumptions).
- Today `commit`'s return value is ignored (L331-345 verified); a stale skip would otherwise be counted as success and routed as processed (Plan Background fact 3).
- The "already registered" skip shape to mirror: log + `self._file_router.route(chunk_files, [])` + `IngestUrlResult.skip(url)` (L317-320).

## Design decisions

- The skip read lives in the same private commit helper (Plan Design: small private method so neither function grows past its band); `ingest_url_group` only branches on the helper's outcome.
- The stale-skip log is a distinct warning (not the L318 info) so occurrences become visible in production (Plan UNK-01 resolution path).

## Alternatives considered

- Treating the skip as `unexpected_failure`: rejected — files were routed for a valid decision; a skip result matches the existing registered-skip contract (AC-3).

## Implementation
### Target file
- `scripts/rag/ingestion/ingester.py`

### Procedure
- Capture the `(doc_id, skip, replace)` return of `tx_mgr.commit(...)` in the commit helper; on `skip`, perform the registered-style routing and return a skip outcome to `ingest_url_group`, which then returns `IngestUrlResult.skip(url)`.

### Method
- In the commit helper: `result_doc_id, skipped, _ = tx_mgr.commit(...)`; if `skipped:` log a distinct warning (message states a stale generation was skipped, `extra={"url": url, "stage_name": "ingester"}`), call `self._file_router.route(prepared_paths, [])`, return the skip outcome; success path unchanged.
- In `ingest_url_group`: on the skip outcome return `IngestUrlResult.skip(url)` before the `log_ingestion_result` success bookkeeping (skip is not counted as success).

### Details
- No change to the earlier already-registered skip (L317-320), the failure routing (L347-350), or `_process_url_groups`.
- `n_embed_failed` accounting is untouched (stale-skip happens after embedding; embedding cost already paid).

### Companion test files
- `tests/rag/ingestion/test_ingester.py`
  - Procedure: add a stale-skip routing test (new test method, e.g. `test_stale_skip_routes_registered_and_returns_skip` (new)) in `TestIngestUrlGroup`: seed a `documents` row with a newer `fetched_at`, commit a group with an older HTTP payload and `force=False`; assert files land in the registered directory (same destination as the already-registered skip), `failed/` stays empty, and the result is a skip with `n_success = 0` (AC-3).
  - Validation: `uv run pytest tests/rag/ingestion/test_ingester.py -q` — the new test fails on HEAD (stale payload is counted as success), passes after.

## Compatibility considerations

- Existing ingester tests seed documents with matching freshness or `force=True`, so their `commit` calls stay on the fresh/forced path (verified against `TestIngestUrlGroup` / `TestGenerationDrain` usage in this cycle); the only outcome change is for stale non-forced payloads.
- Depends on the seq-2 document's skip outcome; without it there is nothing to read (release unit ragrev016-core covers phases 2-3).

## Security considerations
N/A: result-handling change.

## Rollback considerations
N/A: revert the single commit; skipped files are in the registered directory, not deleted.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingester.py -q` — companion test asserts routing (AC-3).
- `uv run pytest tests/rag/ingestion -q` regression.
- `uv run ruff check`, `uv run mypy`.

## Completion criteria

- A stale-skip run routes the chunk files to the registered directory, logs the distinct stale warning, and returns a skip result not counted as success (AC-3); all existing ingester tests stay green.

## Out of Scope

- The staleness rule itself (seq-2 document), staleness comparison redesign, the HTTP skip decision in `DocumentManager` (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md phase 3 - both plans edit the `tx_mgr.commit(...)` block chain; land the commit-error handling first so the skip handling is added to the settled block |
| 2 | Add companion tests per Companion test files | Pending | — | — | Gated: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md phase 3 - both plans edit the `tx_mgr.commit(...)` block chain; land the commit-error handling first so the skip handling is added to the settled block |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md phase 3 - both plans edit the `tx_mgr.commit(...)` block chain; land the commit-error handling first so the skip handling is added to the settled block |

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
- **Requirement ID**: `REQ-003` (ingester treats the stale skip as a skip)
- **Source issue**: issues/20261108-131235_ragrev016_stale-recrawl-replaces-content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170725_ragrev016_stale-recrawl-replaces-content.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-234108
- **Related target files**: `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_ingester.py`
