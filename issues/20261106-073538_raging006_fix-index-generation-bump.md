# Bump index_generation only after a successful ingestion transaction

## Priority
Medium

## Summary
`TransactionManager.commit` calls `bump_index_generation` inside the BEGIN IMMEDIATE
transaction, before the chunk inserts have succeeded and before the commit. A failed
ingestion therefore increments `rag_corpus_meta.index_generation` anyway, and a failed run
with zero completed groups still bumps the generation once per attempted URL.

## Problem
- `scripts/rag/ingestion/transaction_commit.py`: `bump_index_generation(self._db)` runs
  after `delete_document_chain` and before the `documents`/chunks inserts, inside the
  open transaction.
- `bump_index_generation` (`scripts/rag/corpus_identity.py`) swallows `sqlite3.Error` and
  never raises, so a failed bump leaves the transaction open; the later
  `_begin_transaction` re-issue then commits the partial state (deleted old document and
  its chunks) — the atomicity guarantee around the bump is implicit and fragile.
- `ingest_url_group` validates chunk data and performs embedding before `commit`, but the
  bump happens before any insert, so validation-free failure paths still move the counter.
- Corpus consumers that cache by `index_generation` can observe a "new" generation whose
  content was never actually ingested.

## Background
`bump_index_generation`'s contract is "Best-effort increment after a completed ingestion"
(docstring, REQ-007). The current call site violates the "after a completed ingestion"
part of its own contract. `tests/rag/ingestion/test_ingester_index_generation.py` asserts
the bump value propagates on the success path but does not pin when the bump must not
happen.

## Reason for Change
The generation counter is the cache-invalidation signal for the corpus; bumping it on
failed or partial ingestion weakens its meaning and can invalidate caches with no
corresponding content change.

## Implementation Intent
Call `bump_index_generation` after `helper.commit()` succeeds (in
`TransactionManager.commit` or at the `ingest_url_group` level on the committed path
only), keeping its best-effort never-raises contract. Failed groups must not change
`index_generation`.

## Target Files or Areas
- `scripts/rag/ingestion/transaction_commit.py`
- `scripts/rag/corpus_identity.py` (docstring alignment only if needed)
- `tests/rag/ingestion/test_ingester_index_generation.py`

## Required Changes
- Move the `bump_index_generation` call to after a successful commit.
- Add a regression test: a commit that fails (e.g., a failing chunk insert) leaves
  `index_generation` unchanged and the old document intact.
- Keep the existing success-path behavior (bump returns the new generation, propagates to
  `RagIngester.last_index_generation`).

## Constraints
- `bump_index_generation` must remain best-effort: a failed bump never fails ingestion.
- Do not move the bump inside the transaction again, even after the inserts.
- Preserve BEGIN IMMEDIATE placement of the delete/insert sequence.

## Acceptance Criteria
- After a failed ingestion of a group, `index_generation` equals its pre-run value.
- After a successful ingestion, `index_generation` increments exactly once per committed
  group (current behavior).
- All existing tests in `tests/rag/ingestion` pass.

## Testing Expectations
- New failure-path test asserting no generation change on rollback.
- Existing bump tests updated only if their fixture placement changes.
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
If docs describe when `index_generation` advances, align the wording with the
post-commit semantics.

## Out of Scope
- Cache consumers of `index_generation` in the query path.
- Batch-level (per-run) vs per-group bump granularity — keep per-group.

## Dependencies
- N/A: none

## Unresolved Questions
- None.

## AI Implementation Instruction
Keep the change minimal: relocate the call, keep the try/except contract, add the
failure-path test. Do not restructure TransactionManager.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/transaction_commit.py`, `scripts/rag/corpus_identity.py`, `tests/rag/ingestion/test_ingester_index_generation.py`
