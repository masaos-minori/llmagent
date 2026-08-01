# [Implementation bug] Fix ETagManager doc_id=0 causing etag/last_modified updates to never apply

## Priority
High

## Summary
`scripts/rag/ingestion/document_manager.py`'s `_update_etag()` constructs `ETagManager(self._db, 0)`, hardcoding `doc_id` to `0` instead of passing the actual document's ID. Since SQLite `doc_id` values start at 1, the resulting `UPDATE ... WHERE doc_id = 0` never matches any real document row — meaning etag/last_modified are never actually updated via this path, even though the surrounding documentation and code structure imply they are.

## Reason for Change
This is a confirmed, real code defect (not a documentation error) — the etag/last-modified-based change-detection mechanism silently does nothing on the skip/no-reingestion path, which can cause either unnecessary re-ingestion (if some other check depends on etag freshness) or missed updates over time, undermining the intended optimization.

## Implementation Intent
Pass the actual document's ID into `ETagManager` instead of the hardcoded `0`, so the `UPDATE` statement targets the correct row.

## Target Files or Areas
`scripts/rag/ingestion/document_manager.py` (`_update_etag()`)

## Required Changes
- Change `ETagManager(self._db, 0)` to pass the actual `doc_id` for the document being processed.
- Add or update a test covering the etag/last_modified update path to assert the correct row is actually updated (not silently a no-op).
- Verify whether `scripts/mcp_servers/rag_pipeline/document_manager.py` has the same or a related issue, since this review compared both implementations for the deletion-order question and found them consistent — confirm the etag-update code path in that implementation too.

## Acceptance Criteria
`_update_etag()` passes the real document ID; a test confirms `UPDATE ... WHERE doc_id = <real id>` actually updates the target row; the equivalent code path in `mcp_servers/rag_pipeline/document_manager.py` (if it has similar logic) is checked and fixed if the same bug exists there.

## Testing Expectations
Add or update a unit test for `_update_etag()` verifying the etag/last_modified fields are actually persisted for the correct document row after the fix. Run the standard validation sequence (`rules/toolchain.md`) since this changes `scripts/`.

## Documentation Impact
Once fixed, `docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md`, `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`, and `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md` should be updated to describe the corrected, working behavior (tracked in a separate documentation-only issue, since this issue is implementation-only).

## Out of Scope
Do not update the documentation files describing this bug in this issue — that is tracked separately as a documentation-accuracy issue. Do not perform unrelated refactoring of `document_manager.py` beyond this fix.

## AI Implementation Instruction
This is a confirmed, verified bug — implement the fix following `skills/python-implementation` conventions, and ensure a regression test is added so this doesn't silently reappear. Follow `rules/toolchain.md`'s validation sequence before considering the fix complete.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (横断的な確定済み誤り item 3), §4 強化候補 (02_06 ETagManager), §5 例3, §6A (ETagManager doc_id=0固定値問題)
- Generated at: 2026-08-02
