# Fix crawl_file responsibility misattribution and remove duplicate JSON/logging content in docs/03_rag_02_02-part2

## Priority
High

## Summary
`docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`'s "鮮度判定(自動)" (automatic freshness check) section attributes skip/re-ingestion decision logic to `WebCrawler`, but confirmed source reading shows `crawl_file()` only computes mtime/SHA-256 and stores them in the payload, always emitting JSON unconditionally — the actual skip/re-ingestion decision is made by `DocumentManager` (in `scripts/rag/ingestion/document_manager.py`, the ingester stage) via `_is_file_unchanged`/`_handle_existing_file`. Separately, this file duplicates its JSON-output-format example (already canonical in `docs/03_rag_04_01_dto-models_data.md`) and its logging section (already canonical in `docs/03_rag_05_3-logging.md`).

## Reason for Change
This is a confirmed factual error attributing a responsibility to the wrong module — the module-boundary distinction between WebCrawler and DocumentManager is one of this domain's most important design points per this review, and getting it backwards risks an implementer adding duplicate or conflicting skip-logic to WebCrawler. The JSON/logging duplication adds maintenance burden with no unique value.

## Implementation Intent
Rewrite the freshness-check section to correctly attribute responsibility to `DocumentManager`, describing `crawl_file()`'s actual (narrower) role. Remove the duplicated JSON-output example and logging section, replacing them with references to their canonical homes.

## Target Files or Areas
`docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`

## Required Changes
- Replace the "鮮度判定(自動)" section with: "`WebCrawler.crawl_file()` computes mtime/SHA-256 and stores them in the payload, always emitting JSON unconditionally — no skip/re-ingestion decision is made here. The actual skip/re-ingestion decision is made by `DocumentManager` (`scripts/rag/ingestion/document_manager.py`, the ingester stage) via `_is_file_unchanged`/`_handle_existing_file`."
- Remove the JSON-output-format example, replacing it with a reference to `docs/03_rag_04_01_dto-models_data.md`.
- Remove the logging section content, replacing it with a reference to `docs/03_rag_05_3-logging.md`.

## Acceptance Criteria
The freshness-check section correctly attributes skip/re-ingestion logic to `DocumentManager`, not `WebCrawler`; no duplicated JSON-format example or logging section remains — both are references to their canonical files.

## Testing Expectations
Not required (documentation-only). Manually re-verify `crawl_file()`'s actual behavior and `DocumentManager`'s `_is_file_unchanged`/`_handle_existing_file` methods against current source before finalizing.

## Documentation Impact
`docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` corrected and shortened.

## Out of Scope
Do not change `WebCrawler` or `DocumentManager`'s actual implementation in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error — apply the responsibility-attribution fix directly. Verify the exact method names (`_is_file_unchanged`/`_handle_existing_file`) against current source before finalizing, in case they've been renamed since this review.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (横断的な確定済み誤り item 4), §2 削除候補 item 3, §4 強化候補 (02_02-part2), §5 例4, §6A (crawl_fileの鮮度判定責務の誤帰属)
- Generated at: 2026-08-02
