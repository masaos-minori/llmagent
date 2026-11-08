# Search stage skips BM25 when the embedding or the vector search fails

## Priority
Medium

## Summary
`_search_all_queries` runs the full-text search only after the embedding succeeded and the vector search returned, so an embedding outage or a single vector-search error removes the BM25 results too, although FTS needs neither.

## Background
Review finding F-006. Evidence (Explicit in code): in `scripts/rag/stages/search.py`, a failed embedding takes the `continue` branch before `repo.fts_search`, and `repo.vector_search` and `repo.fts_search` share one `try` block, so an exception from the vector search (for example an embedding dimension mismatch reported by sqlite-vec as `sqlite3.OperationalError`) skips the FTS call for that query and increments `fts_errors`. The stage is described as hybrid search with a degraded mode (`SearchDiagnostics.degraded`).

## Problem
When the embedding service is down or returns vectors of the wrong dimension, retrieval returns nothing even though the lexical index could still answer, and the diagnostics blame FTS.

## Reason for Change
A degraded-but-useful result is better than an empty one for the failure that is most likely in a local deployment (the embedding server restarting).

## Implementation Intent
Run FTS independently of the embedding and of the vector search, keep each failure counted under its own diagnostic, and let the stage report `fallback` only when both retrieval paths are empty.

## Target Files or Areas
- `scripts/rag/stages/search.py` (`_search_all_queries`, `SearchStage`)
- `scripts/rag/models_result.py` (`SearchDiagnostics`)
- `tests/rag/test_rag_stages.py`

## Required Changes
- Move the FTS call out of the embedding-success and vector-success path with its own error handling.
- Count vector-search errors separately from FTS errors (or document the combined counter).
- Add tests for an embedding failure and a vector-search error that still return FTS hits.

## Constraints
- Keep the sequential DB access (one connection) and the concurrent embedding fetch.
- Keep `SearchDiagnostics` field names stable for consumers.

## Acceptance Criteria
- With every embedding failing, the stage returns the FTS hits and reports `embed_failed` equal to the number of queries.
- A vector-search `OperationalError` does not suppress the FTS hits for the same query.

## Testing Expectations
- Unit tests for the two failure shapes with a fake repository.
- `uv run pytest tests/rag/test_rag_stages.py -q`, ruff and mypy on touched files.

## Documentation Impact
Update the RAG query-pipeline search-stage description if it states that a failed embedding skips the whole query.

## Out of Scope
- Ranking or fusion changes.
- FTS query construction (separate issue `issues/20261108-131008_ragrev005_fts-query-and-semantics.md`).

## Dependencies
Related, no required order: `issues/20261108-131008_ragrev005_fts-query-and-semantics.md` (FTS query construction in the same retrieval leg).

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131007
- **Related target files**: `scripts/rag/stages/search.py`, `scripts/rag/models_result.py`, `tests/rag/test_rag_stages.py`
