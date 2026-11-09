## Goal
Make the BM25 (FTS) leg independent of the embedding and the vector-search leg in `_search_all_queries` (`REQ-001`..`REQ-005`): an embedding outage or a vector error still yields lexical hits, each failed retrieval leg is counted once, and the stage reports `fallback` only when no leg returned hits.

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/rag/stages/search.py`. The tests are the previous procedure; the docs are the next.

## Assumptions
- Execution order: Plan Phase 2, after `tests/rag/test_rag_stages.py` (Phase 1).
- Overlap judgment (Plan Assumptions): `plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md` later wraps the embedding `gather` in `_search_all_queries` with a semaphore. This procedure leaves the `gather` call untouched, so that change applies cleanly afterward (sequencing dependency, this Plan first).
- `SearchStage.get_status` already reports `fallback` only when `ctx.search_results` is empty; it needs no change once FTS contributes (`REQ-004`).
- The caught exception tuple (`sqlite3.OperationalError`, `RuntimeError`, `ValueError`, `OverflowError`, `struct.error`) stays the same for both legs; the exact exception for a wrong-dimension embedding is Plan UNK-01 (non-blocking).

## Design decisions
- Two small private helpers (one per leg) return the hits and a failed flag, so `_search_all_queries` (complexity B, 9 at plan time) does not grow past B; re-run `radon cc` afterward.
- Keep the per-query append order vector first, FTS second: the RRF fusion treats each list as a ranking, so the order of lists must not change for queries where both legs succeed.

## Alternatives considered
- Add a separate vector-error counter field to `SearchDiagnostics`: rejected (Plan: field names stay stable; owner preference is UNK-02).
- Wrap the whole query in one `try`: rejected, it is the current defect.

## Implementation
### Target file
`scripts/rag/stages/search.py`

### Procedure
1. Add `_vector_leg` (new): takes the repository, the embedding, `top_k`, and the query; returns `(hits, failed)`; calls `repo.vector_search` inside its own `try` with the existing exception tuple and logs a warning on failure.
2. Add `_fts_leg` (new): takes the repository, the query, and `top_k`; returns `(hits, failed)`; calls `repo.fts_search` inside its own `try` with the same tuple.
3. In `_search_all_queries`, rewrite the per-query loop: classify the embedding result (exception or non-list increments `embed_failed` and logs as today, but no longer `continue`s past retrieval; a list increments `embed_ok`); when an embedding exists run `_vector_leg` (new) and append its hits if non-empty, adding one to `fts_errors` when it failed; then always run `_fts_leg` (new), append its hits if non-empty, and add one to `fts_errors` when it failed.
4. Update the `_search_all_queries` docstring: embeddings are fetched concurrently; per query the vector leg (when an embedding exists) and the FTS leg run sequentially and independently; `fts_errors` counts failed retrieval legs.
5. Keep the `degraded` computation, the returned `SearchDiagnostics` fields, `SearchStage.get_status`, and `SearchStage.run` unchanged.

### Method
- The embedding `asyncio.gather(..., return_exceptions=True)` and the single `RagRepository(db)` instance stay exactly as they are (`REQ-005`); DB access stays sequential on one connection.
- `fts_errors` increments once per failed leg per query, so a query whose vector and FTS legs both fail adds 2 and the pinned single-vector-failure case stays 1 (`REQ-003`).
- Failure messages: keep the existing "Embedding failed" and "Unexpected embedding type" warnings; the leg helpers log the leg name and query, e.g. `"Vector search failed for '%s': %s"` and `"FTS search failed for '%s': %s"`. No existing test asserts the old "Search failed for" text (checked with `rg` over `tests/`).

### Details
- Keep the `cast("list[RawHit]", ...)` pattern for the repository returns; the helpers' return annotation is `tuple[list[RawHit], bool]`.
- Keep the stage-level warning in `SearchStage.run` (`"search degraded: %d FTS/vec errors"`) unchanged; tests assert its text.
- Do not touch `rag/repository.py`, `get_embedding`, or the semaphore (ragrev007).

## Compatibility considerations
- Public names, `SearchDiagnostics` shape, and the `stat_search_*` / `get_diagnostics()` keys are unchanged. Observable change: when embeddings fail or a vector query errors, lexical hits are now returned, and `fts_errors` is counted per failed leg. FTS runs for every query (it already did for queries whose embedding succeeded), so the added load is bounded by the query count.

## Security considerations
N/A: no new input handling, no credentials; queries still reach `fts_search` through the existing query builder.

## Rollback considerations
N/A: revert the commit (the test procedure's new tests would fail after a revert of this document only, so revert the tests with it).

## Validation plan
- `uv run pytest tests/rag/test_rag_stages.py -q` (new tests pass; pinned `test_run_pack_failure_degrades` unmodified).
- `uv run pytest tests/rag/test_diagnostics.py tests/rag/test_stage_observability.py tests/rag/test_rag_quality_regression.py tests/rag/test_stage_lifecycle.py -q`, then `uv run pytest tests/rag -q`.
- `uv run ruff check scripts/rag/stages/search.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run radon cc scripts/rag/stages/search.py -s`, `uv run python tools/check_module_size.py`.

## Completion criteria
- With every embedding failing, the stage returns the FTS hits and `embed_failed` equals the number of queries; a vector error keeps the FTS hits of that query; an FTS error keeps the vector hits.
- A query with both legs failing adds 2 to `fts_errors`; an empty database still yields `fallback` / `no search results`.
- The `gather` call and the single repository use are unchanged; complexity grade of `_search_all_queries` is not worse than B.

## Out of Scope
- The embedding concurrency bound and MQE changes (ragrev007), FTS query construction (ragrev005), `SearchDiagnostics` redesign, ranking and fusion, and deployment (a user decision after commit and push).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_vector_leg` (new) and `_fts_leg` (new) and restructure the per-query loop of `_search_all_queries` | Pending | — | — | |
| 2 | Run the new tests and the unmodified diagnostics, observability, and regression suites | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and `radon cc` | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`..`REQ-005` (independent legs, per-leg counting, status, concurrency and sequential DB unchanged)
- **Source issue**: issues/20261108-131007_ragrev004_search-bm25-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164823_ragrev004_search-bm25-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121538
- **Related target files**: `scripts/rag/stages/search.py`
