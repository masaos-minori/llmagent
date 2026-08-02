# Fix delete_existing_document() method-name typo and simplify docs/03_rag_02_04 (parts 1+2) tables

## Priority
Medium

## Summary
`docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md` references a method `delete_existing_document()` that does not exist in `scripts/mcp_servers/rag_pipeline/document_manager.py` — the actual method is `delete_document(url: str)`. Separately, `02_04-part1` contains verbatim "Dataclass" and "public methods" tables, and `02_04-part2` contains verbatim "updated DB tables" and structured logging-field-column tables — all mechanical transcriptions of code.

## Reason for Change
The method-name error is a confirmed factual error that would send a developer searching for a nonexistent method. The verbatim tables are code-derived detail that drifts whenever a field/method changes, providing no design-intent value beyond what reading the source directly would show.

## Implementation Intent
Fix the method name directly. Remove the mechanical tables, keeping only the design-relevant content already identified as important: the deletion-order invariant (once corrected per the related delete_document()-order issue) and `embedding_dims` validation logic.

## Target Files or Areas
`docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md`, `docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md`

## Required Changes
- Replace `delete_existing_document()` with the correct method name, `delete_document(url: str)`.
- Remove the "Dataclass" and "public methods" tables in `part1`; remove the "updated DB tables" and structured-logging-field-column tables in `part2`.
- Keep the deletion-order invariant description and `embedding_dims` validation design notes intact.
- Replace removed tables with a pointer to the implementation tree / Reference API for exact signatures and fields.

## Acceptance Criteria
No file references the nonexistent `delete_existing_document()`; no verbatim dataclass/method/DB-table/logging-field table remains; the deletion-order and `embedding_dims` design content is preserved.

## Testing Expectations
Not required (documentation-only). Manually verify the correct method name and signature against current `document_manager.py` before finalizing.

## Documentation Impact
Both parts of `docs/03_rag_02_04` corrected and shortened.

## Out of Scope
Do not change `document_manager.py`'s actual method names in this issue — documentation only. Do not duplicate the ETag doc_id=0 fix here — that is tracked in a separate issue covering `02_04-part1` alongside `02_05`/`02_06`.

## AI Implementation Instruction
This is a confirmed factual error (method name) — apply directly. Coordinate with the separate ETag doc_id=0 documentation issue if editing the same file in close succession, to avoid conflicting edits.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §2 削除候補 item 4, §6A (delete_existing_document()というメソッド名の誤記)
- Generated at: 2026-08-02
