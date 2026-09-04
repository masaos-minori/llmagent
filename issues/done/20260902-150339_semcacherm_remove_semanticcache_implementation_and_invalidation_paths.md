# Remove SemanticCache implementation and all RAG MCP invalidation paths

## Priority
High

## Summary
Remove query-result caching as a runtime capability from the RAG pipeline, along with every
call site, protocol method, and HTTP endpoint that exists only to invalidate it. Local RAG must
execute retrieval for every query against the currently visible committed RAG database state.

## Background
`scripts/rag/cache.py` currently implements `SemanticCache` and `CacheEntry`;
`scripts/rag/pipeline.py` imports, constructs, and calls `lookup()`/`put()`/`invalidate_cache()`
on it. `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` exposes
`invalidate_cache()` and calls it from document deletion; `rag_pipeline_server.py` exposes the
`/rag_invalidate_cache` HTTP endpoint. `scripts/rag/ingestion/cache_invalidation.py`'s
`CacheInvalidator` class is a confirmed active caller of that endpoint, invoked after ingestion
completes to invalidate stale entries.

## Problem
The in-process `SemanticCache` cannot observe corpus changes committed by other processes, has
no TTL, and does not use its generation value to validate entry freshness. Its behavior is
spread across the RAG pipeline, the RAG MCP service protocol, document deletion, the ingestion
pipeline's post-ingestion invalidation call, and a direct HTTP invalidation endpoint. Removing
only the cache lookup from the pipeline would leave invalid method contracts, stale call sites,
and a public endpoint for a feature that no longer exists.

## Reason for Change
A cache with no cross-process invalidation and no TTL can serve stale results after another
process commits document changes, contradicting the freshness guarantee RAG retrieval is
expected to provide.

## Implementation Intent
Remove query-result caching as a runtime capability and make local RAG execute retrieval for
every query against the currently visible committed RAG database state. Remove cache
invalidation as an API and an operational concept, including the ingestion pipeline's
post-ingestion invalidation call. Preserve `embed_url` because it remains required by local
vector retrieval and the Agent memory embedding path.

## Target Files or Areas
- `scripts/rag/pipeline.py`
- `scripts/rag/cache.py`
- `scripts/rag/models_data.py`
- `scripts/rag/ingestion/cache_invalidation.py` (`CacheInvalidator`, confirmed active caller of `/rag_invalidate_cache`)
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
- RAG pipeline tests (`tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/test_rag_cache.py`, `tests/rag/test_semantic_cache_invalidate.py`, `tests/rag/test_semantic_cache_eviction.py`, `tests/rag/test_semantic_cache_concurrency.py`)
- RAG MCP service/server tests (`tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`)
- RAG ingestion tests referencing cache invalidation (`tests/rag/ingestion/test_rag_ingester.py`)

Confirm every path and ownership boundary before editing; add only files confirmed by a
repository-wide reference search at implementation time.

## Required Changes
- Remove the `SemanticCache` import from `scripts/rag/pipeline.py`.
- Remove construction and storage of `RagPipeline.semantic_cache`.
- Remove the cache-lookup embedding request from `RagPipeline.augment()`.
- Remove all calls to `SemanticCache.lookup()` and `SemanticCache.put()`.
- Remove `RagPipeline.invalidate_cache()` and `invalidate_cache()` from the `RagPipelineLike` protocol.
- Remove `RagPipelineMCPService.invalidate_cache()`.
- Remove cache invalidation and its log message from `fmt_delete_document()`.
- Remove the `/rag_invalidate_cache` HTTP endpoint, handler, responses, logging, and endpoint tests.
- Remove `scripts/rag/ingestion/cache_invalidation.py`'s `CacheInvalidator` and its caller in the ingestion pipeline, since its sole purpose is calling the removed endpoint.
- Search for all references to `SemanticCache`, `CacheService`, `CacheEntry`, `invalidate_cache`, and `rag_invalidate_cache`.
- Delete `CacheEntry` if no non-cache use remains; delete `scripts/rag/cache.py` after verifying no active caller remains.
- Remove imports, mocks, fixtures, and helper methods made unused by the deletion.
- Keep `embed_url`; do not remove or rename it as part of this issue.
- Ensure local RAG executes `SearchStage` for every query, including repeated identical queries.
- Add regression coverage proving that committed document additions, updates, and deletions are visible without cache invalidation or service restart.

## Constraints
- Limit the change to SemanticCache removal and its direct contracts.
- Do not redesign remote/local fallback behavior in this issue set.
- Do not remove `embed_url`; it remains required outside the deleted cache path.
- Do not preserve a no-op cache API or configuration switch that suggests the removed feature still exists.
- Preserve unrelated behavior and update only verified callers.
- Update documentation only after code and tests establish the final behavior (see `semcachedocs`).

## Acceptance Criteria
- Production code contains no reference to `SemanticCache` or `CacheService`.
- `RagPipeline` does not create, read, write, or invalidate a query-result cache.
- The RAG MCP protocol and service do not expose `invalidate_cache()`.
- Successful document deletion does not invoke cache invalidation.
- The `/rag_invalidate_cache` endpoint no longer exists, and no active caller (including `CacheInvalidator`) expects it.
- `CacheEntry` and `scripts/rag/cache.py` are removed when the repository-wide reference check confirms they have no other purpose.
- Every local RAG query executes the retrieval pipeline.
- Committed document additions, updates, and deletions are reflected without restarting the RAG MCP service.
- Local RAG and Agent memory embedding behavior depending on `embed_url` continues to work.
- RAG pipeline, RAG MCP service, RAG MCP server, and ingestion tests pass.

## Testing Expectations
Run a repository-wide reference search before editing. Confirm each replacement regression
test fails before the implementation change and passes afterward. Run the complete affected
test suites, type checking, and linting. Verify that unrelated remote/local fallback behavior
is not changed by this issue. Record any missing file or unresolved design decision before
implementation rather than guessing.

## Documentation Impact
Yes — covered by `semcachedocs` (filed alongside this issue), not performed here; update
documentation only after this issue's code and tests establish the final behavior.

## Out of Scope
- Configuration-contract field removal (`use_semantic_cache`, `semantic_cache_threshold`, `semantic_cache_max_size`) — covered by `semcacheconfig`.
- Test and documentation replacement beyond what this issue's own Testing Expectations require — covered by `semcachedocs`.
- Redesigning remote/local RAG fallback behavior.

## Dependencies
`semcacheconfig` (configuration-contract removal) and `semcachedocs` (test/documentation
replacement) both depend on this issue landing first, since they remove settings and
descriptions for a feature this issue deletes.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Run a repository-wide reference search for `SemanticCache`, `CacheEntry`, `invalidate_cache`,
and `rag_invalidate_cache` before editing, since call sites may have changed since this issue
was filed. Delete `scripts/rag/cache.py` and `scripts/rag/ingestion/cache_invalidation.py`
only after confirming zero remaining callers. Do not remove `embed_url` or redesign
remote/local fallback behavior.
