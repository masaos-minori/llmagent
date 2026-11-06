# Update document ETag only after re-ingestion commits

## Priority
High

## Summary
For changed HTTP documents, `DocumentManager.handle_existing_document` writes the new
`etag`/`last_modified`/`fetched_at` into the `documents` row before the chunks are
re-embedded and committed. If the later embedding or transaction step fails, the document
row claims freshness that the stored chunks do not have, and subsequent crawls receive
HTTP 304 and never re-ingest. Move the freshness update inside the commit boundary.

## Background
Evidence path, all in `scripts/rag/ingestion`:
- `document_manager.py` `handle_existing_document` calls `_update_etag` (via
  `ETagManager.update`) and then returns `replace=True` — the DB update happens at
  `get_or_create` time, before `ChunkFactory.prepare` and `TransactionManager.commit` run.
- `http_fetcher.py` `get_conditional_headers` reads `etag`/`last_modified` from the
  `documents` table and sends them as `If-None-Match`/`If-Modified-Since`;
  `fetch_html` returns `None` on 304, so no new crawl payload is written.
- `transaction_commit.py` re-inserts the `documents` row (with the payload's etag) only on
  the success path.
The file:// sibling path shows the intended ordering: it does not touch stored etag
before replace; the fresh values land only via the transaction insert.

### Verification (issue-to-plan cycle 20261106-094942)
- Confirmed line-by-line at HEAD `bdb9bed66`: pre-commit write at `document_manager.py:101`
  (`_update_etag` → `ETagManager.update`), unconditional payload-freshness insert at
  `transaction_commit.py:59-78` + `document_persistence.py:77-95`, 304 skip path at
  `http_fetcher.py:39-77`.
- Correction: the HTTP skip branch (`document_manager.py:98-99`, stored etag and
  last_modified equal) does **not** call `ETagManager.update` — the sole production call site
  is the replace branch. The "skip-path" wording in `ETagManager`'s log strings and in this
  issue's Implementation Intent names a code path that does not currently exist.
- New finding: on a successful replace, the transaction's delete+insert writes the payload's
  freshness values unconditionally, so the `ETagManager` stale guard never affects the final
  stored row on the replace path; it only prevented freshness advancement on runs whose
  commit never executed. The plan must apply the guard to the insert values, not inherit it
  (see Plan Design).
- No existing test pins the pre-commit `_update_etag` call (`rg '_update_etag'` matches only
  `document_manager.py`; mock-based ingestion tests stub `handle_existing_document`).

## Problem
A failed re-ingestion (embedding service down, transaction error) leaves old chunks in
place while the `documents` row carries the new etag. The next crawl gets 304, the URL is
skipped forever, and the RAG index serves stale content indefinitely with no retry path.

## Reason for Change
Data-integrity defect in the normal HTTP update workflow; the failure is self-perpetuating
(no future run can recover it without manual intervention).

## Implementation Intent
Make the freshness record atomic with the chunk replacement: the skip path may keep the
`ETagManager.update` guarded fast-forward, but the replace path must defer the
`etag`/`last_modified`/`fetched_at` write to the same `BEGIN IMMEDIATE` transaction that
deletes and re-inserts the document and chunks. Keep `ETagManager`'s stale-overwrite guard.

## Target Files or Areas
- `scripts/rag/ingestion/document_manager.py`
- `scripts/rag/ingestion/transaction_commit.py`
- `tests/rag/ingestion/test_ingestion_freshness.py` and `tests/rag/ingestion/test_ingester_etag_guard.py`

## Required Changes
- Remove the pre-commit `_update_etag` call from the replace branch of
  `handle_existing_document`.
- Ensure the replace-path `documents` insert carries the new etag/last_modified/fetched_at
  (it already passes them; verify against the ETagManager freshness-guard semantics so a
  stale incoming payload cannot overwrite fresher stored values).
- Add a regression test: existing document + changed etag + forced embedding/commit
  failure → stored etag unchanged and the URL is re-ingestable on the next run.

## Constraints
- Keep the skip-path etag fast-forward behavior (documents whose chunks were not replaced
  must still refresh freshness).
- Preserve the `ETagManager` stale-timestamp guard semantics after the move.
- Do not change the HTTP conditional-request logic in `http_fetcher.py`.

## Acceptance Criteria
- After a failed re-ingestion, the `documents` row still holds the previous etag and a
  subsequent run re-processes the URL.
- After a successful re-ingestion, the `documents` row holds the new etag in the same
  transaction as the new chunks.
- Existing freshness tests (`test_ingestion_freshness.py`, `test_ingester_etag_guard.py`)
  still pass, plus the new regression test.

## Testing Expectations
- Regression test simulating embedding failure after `get_or_create` returns
  `replace=True`, asserting stored etag is unchanged.
- Transaction-atomicity test: rollback leaves both chunks and etag at pre-run values.
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
If the RAG persistence docs describe when `documents.etag` is refreshed, update the
description of the update ordering (intent level only).

## Out of Scope
- Crawler conditional-request logic.
- The retry/ re-queue design (see `20261106-073538_raging005_retry-dir-no-consumer.md`).

## Dependencies
- N/A: none

## Unresolved Questions
- Whether `ETagManager.update` should remain on the replace path at all, or be removed
  entirely once the insert carries the values — decide during planning.
  Resolved in `plans/20261106-094942_raging002_etag-updated-before-reingestion.md`: `update`
  is no longer called on the replace path; the guard moves to `ETagManager.resolve_incoming`
  applied at the transaction insert; `update` itself is kept unchanged (characterization
  tests) with removal deferred to the `rules/coding.md` deprecation policy.

## AI Implementation Instruction
Keep the change inside the document-management/transaction boundary; do not touch the
crawler HTTP layer. Re-read `ETagManager`'s stale-guard contract before moving the write,
and cover both failure and success paths with tests.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/document_manager.py`, `scripts/rag/ingestion/transaction_commit.py`, `tests/rag/ingestion/test_ingestion_freshness.py`, `tests/rag/ingestion/test_ingester_etag_guard.py`
