# A stale incoming chunk generation replaces newer content but keeps newer metadata

## Priority
Medium

## Summary
In the replace branch of `TransactionManager.commit`, `ETagManager.resolve_incoming` returns the stored etag and fetched_at when the incoming payload is older, yet the existing chunks are still deleted and the incoming chunks inserted, so the document row and its chunks come from different generations.

## Background
Review finding F-016 (the control flow is Explicit in code; the end-to-end scenarios were not reproduced). Evidence: `scripts/rag/ingestion/transaction_commit.py` `commit` calls `resolve_incoming(...)` and then `delete_existing_document(doc_id)` and inserts the new chunks unconditionally; `scripts/rag/ingestion/etag_manager.py` `resolve_incoming` documents that stale incoming values are replaced by the stored row values. For `file://` documents `fetched_at` is the file modification time, so a file restored with an older mtime counts as stale while the stored sha256 stays old, and later runs can re-ingest repeatedly. Related archived work: `issues/done/20261106-073538_raging002_etag-updated-before-reingestion.md` (freshness placement) and `issues/done/20261106-073538_raging003_recrawled-chunk-group-poisoning.md`.

## Problem
Older content can overwrite newer content while the row keeps the newer validators, so later crawls skip the page (HTTP) or re-ingest forever (file).

## Reason for Change
Content and its freshness metadata must describe the same generation; the guard currently protects only the metadata columns.

## Implementation Intent
When the incoming payload is stale, skip the replacement (keep chunks and row as stored) instead of replacing the chunks and keeping the stored metadata, and report the skip.

## Target Files or Areas
- `scripts/rag/ingestion/transaction_commit.py` (`TransactionManager.commit`)
- `scripts/rag/ingestion/etag_manager.py` (`resolve_incoming`)
- `tests/rag/ingestion/`

## Required Changes
- Make the staleness decision abort the replace branch (no delete, no insert) and route the chunk files accordingly.
- Decide how a legitimately restored older file is re-ingested (hash comparison).
- Add tests for the stale HTTP case and the older-mtime file case.

## Constraints
- Keep the single-transaction guarantee.
- Do not regress the raging002 freshness-in-transaction behavior.

## Acceptance Criteria
- A stale incoming generation leaves chunks and metadata unchanged.
- A file restored with an older mtime but different content is handled by the chosen rule without an endless re-ingest loop.

## Testing Expectations
- Unit tests around `commit` with stale and fresh payloads using an in-memory database.
- ruff and mypy.

## Documentation Impact
No documentation change expected beyond the freshness description if it states the replace rule.

## Out of Scope
- Redesigning freshness comparison.

## Dependencies
Related, no required order: `issues/20261108-131124_ragrev010_pages-without-validators-skipped.md` (same freshness rules).

## Unresolved Questions
Whether a stale payload can reach `commit` in practice (the group validation and the ingester skip checks may already prevent it) is `Needs confirmation`.

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131235
- **Related target files**: `scripts/rag/ingestion/transaction_commit.py`, `scripts/rag/ingestion/etag_manager.py`, `tests/rag/ingestion/`
