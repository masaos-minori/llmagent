# Fix chunk_utils.py shared-function usage table to reflect actual non-sharing in docs/03_rag_02_07

## Priority
Medium

## Summary
`docs/03_rag_02_07_ingestion_pipeline-utils.md`'s "ミックスインでの使用箇所" (mixin usage) table implies `ChunkEnglishMixin` and `ChunkJapaneseMixin` both use `chunk_utils.py`'s shared functions, but confirmed source reading shows `ChunkEnglishMixin` uses only `start_next_buf` and otherwise implements its own logic, while `ChunkJapaneseMixin` imports nothing from `chunk_utils.py` and is entirely self-implemented. `merge_text_items` is actually only used by `ChunkSplitter._chunk_code`.

## Reason for Change
This is a confirmed factual error — the table's implication that `chunk_utils.py` is a genuinely shared helper layer is contradicted by actual usage. An implementer who modifies `chunk_utils.py` expecting the change to propagate to English/Japanese chunking would find their change silently has no effect on those paths, potentially introducing an inconsistency bug.

## Implementation Intent
Correct the usage table to reflect actual current usage, and note explicitly that the shared-helper extraction is incomplete (design intent not fully realized in implementation), rather than presenting it as if fully shared.

## Target Files or Areas
`docs/03_rag_02_07_ingestion_pipeline-utils.md`

## Required Changes
- Correct the mixin-usage table: `ChunkEnglishMixin` uses only `start_next_buf` (rest is self-implemented); `ChunkJapaneseMixin` uses none of `chunk_utils.py` (fully self-implemented); `merge_text_items` is used only by `ChunkSplitter._chunk_code`.
- Add a note that the shared-helper extraction is incomplete relative to the original design intent, and that a future consolidation may or may not be planned — mark the plan's existence as a Needs Confirmation item rather than asserting one exists.

## Acceptance Criteria
The usage table matches confirmed actual usage; a note explicitly flags the shared-helper extraction as incomplete, with the future-plan question tracked as Needs Confirmation rather than silently implied.

## Testing Expectations
Not required (documentation-only). Manually re-verify each mixin's imports and function usage against current source before finalizing.

## Documentation Impact
`docs/03_rag_02_07` corrected.

## Out of Scope
Do not refactor `ChunkEnglishMixin`/`ChunkJapaneseMixin` to actually share `chunk_utils.py` logic in this issue — documentation only, reflecting current reality. If a future consolidation is confirmed to be planned, that would be a separate implementation issue.

## AI Implementation Instruction
This is a confirmed factual error — apply directly. Do not assert a future consolidation plan exists without confirming it; mark as Needs Confirmation if uncertain.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (横断的な確定済み誤り item 7), §6A (chunk_utils.py共有関数の実質的な未共有)
- Generated at: 2026-08-02
