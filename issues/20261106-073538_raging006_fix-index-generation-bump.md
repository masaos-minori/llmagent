# Bump index_generation only when a run actually wrote content

## Priority
Low

## Summary
`RagIngester.ingest_all` bumps `rag_corpus_meta.index_generation` when the run guard
`results and any(not r.skipped for r in results)` is true, but groups that failed every
chunk (embed-failed, storage-failed, group-validation-failed) have `skipped=False`. A run
whose URL groups all failed, writing nothing, still advances the generation, signaling
consumers that the corpus changed when it did not.

## Problem
- `scripts/rag/ingestion/ingester.py` `ingest_all` (post-`_process_url_groups`): the
  bump condition tests "at least one group was not skipped", not "at least one chunk was
  written". `IngestUrlResult.validation_failure(...)` and all-failed group results carry
  `skipped=False` with `n_success=0`.
- Therefore a run where every group failed (e.g. embedding service down, poisoned groups
  from the group-validation issue) bumps `index_generation` once and invalidates
  consumer caches for zero content change.
- The run-level comment states the intent: "advance the corpus index generation once this
  run has written new content" — the guard does not implement that intent.

## Background
`bump_index_generation` (`scripts/rag/corpus_identity.py`) is best-effort and never
raises (REQ-007); the call site in `ingest_all` already sits outside the per-URL
transaction and after the consistency check, so placement is correct — only the guard
condition is imprecise. `tests/rag/ingestion/test_ingester_index_generation.py` covers
the success-path bump and the skipped-only-run case but not the all-groups-failed run.

## Reason for Change
The generation counter is the cache-invalidation signal for the corpus; bumping it on a
run that wrote nothing creates spurious invalidation and weakens the "content changed"
meaning.

## Implementation Intent
Change the guard to a content-based condition, e.g. bump only when the summed
`n_success` across results is greater than zero, keeping the best-effort never-raises
contract and the call position after the transaction block.

## Target Files or Areas
- `scripts/rag/ingestion/ingester.py`
- `tests/rag/ingestion/test_ingester_index_generation.py`

## Required Changes
- Replace `any(not r.skipped for r in results)` with a check on actual successful writes
  (sum of `n_success` > 0).
- Add a regression test: a run where all groups fail (embed failure or group-validation
  failure) leaves `index_generation` unchanged.
- Keep the existing skipped-only-run and success-path tests passing.

## Constraints
- `bump_index_generation` must remain best-effort: a failed bump never fails ingestion.
- Keep exactly one bump per qualifying run (no per-group bump).
- Do not move the bump inside any transaction.

## Acceptance Criteria
- After a run whose groups all failed, `index_generation` equals its pre-run value
  (covered by test).
- After a run with at least one successful chunk insert, `index_generation` increments
  exactly once.
- `uv run pytest tests/rag/ingestion` passes.

## Testing Expectations
- New all-groups-failed regression test in `test_ingester_index_generation.py`.
- Existing bump tests unchanged.

## Documentation Impact
If docs describe when `index_generation` advances, align the wording with the
content-based guard.

## Out of Scope
- Cache consumers of `index_generation` in the query path.
- Bump granularity (per-group vs per-run) — stays per-run.

## Dependencies
- N/A: none

## Unresolved Questions
- None.

## AI Implementation Instruction
Single guard-condition change plus one test; do not touch TransactionManager or
corpus_identity.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_ingester_index_generation.py`
