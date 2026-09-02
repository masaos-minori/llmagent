# Replace SemanticCache tests and documentation with the no-cache RAG design

## Priority
Low

## Summary
Replace cache-centric tests and documentation with the current no-cache design: local RAG
performs retrieval for every query and reflects the currently visible committed local RAG
database state without a cache invalidation action or service restart.

## Background
`docs/03_rag_03_06_query_pipeline-helpers-and-cache.md` and
`docs/03_rag_05_1-configuration-reference.md` currently describe SemanticCache behavior and
configuration. No Known Issue entry for cache freshness was found in
`docs/03_rag_90_inconsistencies_and_known_issues.md` at investigation time; a separate,
already-tracked remote/local corpus-mismatch concern is distinct from this issue's scope and
must not be affected by it.

## Problem
Deleting the implementation and settings (`semcacherm`, `semcacheconfig`) is not sufficient if
active tests, API references, runbooks, ADRs, or Known Issues continue to describe
`SemanticCache`, FIFO eviction, similarity thresholds, generation counters, cache invalidation,
or the `/rag_invalidate_cache` endpoint. The current cache has no TTL, and its generation value
is not used as a corpus freshness check — retaining those descriptions would preserve incorrect
implementation claims and obsolete operational procedures.

## Reason for Change
Code and configuration alone do not prevent a reader or AI agent from relying on stale test
assertions or documentation that still describes SemanticCache as current behavior.

## Implementation Intent
Replace cache-centric verification and documentation with the current design: local RAG
performs retrieval for every query, does not reuse a prior RAG context block, and reflects the
currently visible committed local RAG database state without a cache invalidation action or
service restart. Keep remote/local corpus mismatch documented as a separate unresolved concern.

## Target Files or Areas
- RAG cache tests (`tests/rag/test_rag_cache.py`, `tests/rag/test_semantic_cache_invalidate.py`, `tests/rag/test_semantic_cache_eviction.py`, `tests/rag/test_semantic_cache_concurrency.py`)
- RAG pipeline tests (`tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/test_rag_quality_regression.py`, `tests/rag/test_rag_repository.py`)
- RAG MCP integration and endpoint tests (`tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`)
- `docs/03_rag_03_01_query_pipeline-overview.md`
- `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`
- `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md`
- `docs/03_rag_05_1-configuration-reference.md`
- `docs/03_rag_90_inconsistencies_and_known_issues.md`
- `docs/03_rag_00_document-guide.md`
- Any ADR that currently adopts SemanticCache

Verify every path and ownership boundary before editing; add only files confirmed by a
repository-wide reference search at implementation time.

## Required Changes
- Remove unit tests for SemanticCache lookup, semantic-similarity hits, FIFO eviction, capacity, dimension mismatch, invalidation, and generation.
- Remove tests for the `/rag_invalidate_cache` endpoint.
- Update document-deletion tests so they no longer expect cache invalidation.
- Replace removed cache tests with tests proving that local retrieval runs for every query.
- Add or retain tests proving that committed document additions, updates, and deletions are reflected without restart.
- Remove descriptions of `SemanticCache`, `CacheService`, `CacheEntry`, and `RagPipeline.invalidate_cache()` from active documentation.
- Remove descriptions of FIFO eviction, similarity threshold, maximum cache size, generation, and TTL.
- Remove the `/rag_invalidate_cache` endpoint from API references and runbooks.
- Remove configuration-reference entries for the three deleted cache keys.
- Remove instructions requiring cache invalidation or RAG service restart after CLI ingestion or document deletion.
- Remove cache-specific debug output, metrics, scripts, front-matter tags, keywords, and guide references when present.
- Update any accepted ADR that adopts SemanticCache so the current decision records its removal and rationale.
- Remove the cache-freshness Known Issue only after implementation and replacement regression tests are complete, if one is registered by the time this issue is implemented.
- Do not close or remove the separate remote/local corpus-mismatch Known Issue.
- Document the freshness guarantee precisely as retrieval from the currently visible committed local RAG database state.

## Constraints
- Limit the change to SemanticCache removal and its direct contracts.
- Do not redesign remote/local fallback behavior in this issue set.
- Do not remove `embed_url`; it remains required outside the deleted cache path.
- Do not preserve a no-op cache API or configuration switch that suggests the removed feature still exists.
- Preserve unrelated behavior and update only verified callers.
- Update documentation only after code and tests establish the final behavior — do not perform this issue's edits until `semcacherm` and `semcacheconfig` have landed.

## Acceptance Criteria
- Active tests contain no assertion for SemanticCache behavior or cache invalidation APIs.
- Removed cache tests are replaced by retrieval re-execution and committed-corpus-change tests.
- Active documentation does not describe SemanticCache, cache invalidation, FIFO, cache TTL, cache generation, or removed settings as current behavior.
- The `/rag_invalidate_cache` endpoint is absent from API references and operational procedures.
- No procedure requires cache invalidation or service restart to expose committed local corpus changes.
- The local freshness guarantee is stated as the currently visible committed local RAG database state.
- Remote/local corpus mismatch remains documented as a separate unresolved issue.
- Documentation links, metadata, keywords, ADR references, and the active Known Issues inventory are consistent.

## Testing Expectations
Run a repository-wide reference search before editing. Confirm each replacement regression
test fails before the implementation change and passes afterward. Run the complete affected
test suites, type checking, and linting. Verify that unrelated remote/local fallback behavior
is not changed by this issue. Record any missing file or unresolved design decision before
implementation rather than guessing.

## Documentation Impact
Yes — this issue's entire second half is the documentation alignment listed in Target Files,
to be done only after `semcacherm` and `semcacheconfig` establish the actual, current
behavior.

## Out of Scope
- Removing the `SemanticCache` implementation itself and its invalidation paths (`semcacherm`).
- Configuration-contract field removal (`semcacheconfig`).
- The separate, already-tracked remote/local corpus-mismatch concern — do not close or alter it.
- Redesigning remote/local RAG fallback behavior.

## Dependencies
Depends on `semcacherm` and `semcacheconfig` landing first, so tests and documentation describe
the actual, final behavior rather than an anticipated one.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Do not begin this issue until `semcacherm` and `semcacheconfig` have landed. Run a
repository-wide reference search for `SemanticCache`, `semantic_cache`, and
`rag_invalidate_cache` before editing, since test and documentation content may have changed
since this issue was filed. Do not touch the separate remote/local corpus-mismatch Known Issue.
