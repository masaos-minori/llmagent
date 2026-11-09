## Goal

Bound concurrent `get_embedding` calls in `_search_all_queries` with a per-call `asyncio.Semaphore` of a module-constant size, keeping the single `gather` and the sequential SQL searches (`REQ-003`: bounded embedding concurrency, unchanged results and diagnostics).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one module constant and the embedding fan-out inside `_search_all_queries` in `scripts/rag/stages/search.py`.
- Out of scope: a configuration key for the limit (Plan UNK-01), per-query retry, the vector/FTS leg split (ragrev004).

## Assumptions

- Re-verified at generation time: `_search_all_queries` runs one `asyncio.gather(*(get_embedding(...) for q in queries), return_exceptions=True)` with no bound, then searches each query sequentially; `get_embedding` is imported lazily inside the function, and tests patch it as `rag.llm_client.get_embedding`.
- UNK-02 resolved here: the limit is 8 (`_EMBED_CONCURRENCY` (new)). It is above the typical `mqe_n_queries + 1` of 4, so normal runs are not delayed; tune after measurement.
- Ordering: Plan ragrev004's procedure `implementations/20261109-121538_02_scripts_rag_stages_search.py.md` rewrites the per-query loop after the `gather` and adds `_vector_leg` / `_fts_leg`; this change touches only the `gather` expression and must be applied after it. Locate code by symbol, not line number.

## Design decisions

- Create the semaphore inside `_search_all_queries` (per call, inside the running event loop) rather than at module level, so it never binds to a stale loop.
- Wrap the fetch in a small nested coroutine `_embed_limited` (new) to keep `_search_all_queries` from rising to grade C.

## Alternatives considered

- A config key for the limit: rejected for now (Plan UNK-01); it would be a separate Plan (config, reference table, docs).
- Sequential embedding: rejected; it removes the existing concurrency for normal runs.

## Implementation
### Target file
`scripts/rag/stages/search.py`

### Procedure
1. Add a module constant `_EMBED_CONCURRENCY = 8` (new) with a one-line comment stating it bounds in-flight embedding requests per search run.
2. In `_search_all_queries`, create `sem = asyncio.Semaphore(_EMBED_CONCURRENCY)` and define `async def _embed_limited(q: str)` (new) that does `async with sem:` and returns `await get_embedding(q, cast(_httpx.AsyncClient, http), embed_url)`.
3. Replace the generator in `asyncio.gather(...)` with `(_embed_limited(q) for q in queries)`, keeping `return_exceptions=True`.
4. Extend the `_search_all_queries` docstring: embeddings are fetched concurrently up to the limit.

### Method
- Exceptions raised by `get_embedding` inside `_embed_limited` (new) propagate to `gather(return_exceptions=True)` exactly as before, so result classification and diagnostics are unchanged.
- The lazy `get_embedding` import stays where it is; the nested coroutine uses that local name.

### Details
- Do not change `SearchStage.run`, `SearchDiagnostics`, the `degraded` computation, or the repository usage.
- The module-size and complexity gates apply: run them after the edit.

## Compatibility considerations

- Results, ordering of `raw`, and diagnostics are identical for any query count; only the peak number of in-flight embedding calls changes, and a run of at most 8 queries is not delayed.
- Existing tests that patch `rag.llm_client.get_embedding` keep working because the patched name is still resolved at call time.

## Security considerations

N/A: bounds outbound request concurrency to the local embedding server; no new input or trust boundary.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_stages.py -q -k "embed or search"` (the concurrency-count test fails on HEAD, passes after), then `uv run pytest tests/rag -q`.
- `uv run ruff check scripts/rag/stages/search.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/rag/stages/search.py`.
- `uv run radon cc scripts/rag/stages/search.py -s -n C` and `uv run python tools/check_module_size.py`.

## Completion criteria

- With more queries than the limit, the maximum in-flight `get_embedding` count never exceeds `_EMBED_CONCURRENCY` (new) and every query is still embedded.
- All existing `SearchStage` and `SearchDiagnostics` tests pass unmodified; static gates are clean.

## Out of Scope

- The leg split and failure accounting (ragrev004), a config key, tests, and docs (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_EMBED_CONCURRENCY` (new) and the semaphore-bounded fetch in `_search_all_queries` | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) and `uv run pytest tests/rag -q` | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (bounded embedding concurrency)
- **Source issue**: issues/20261108-131120_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-133800
- **Related target files**: `scripts/rag/stages/search.py`
