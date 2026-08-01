# Simplify docs/03_rag_02_09 shared-utilities tables; confirm MIN_TEXT_LENGTH_FOR_DETECTION=100 rationale

## Priority
Medium

## Summary
`docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md` contains verbatim "function/signature/return-value/description," "constants" (`LOG_KEY_*`), and "usage source" tables — pure API listings. Separately, the `MIN_TEXT_LENGTH_FOR_DETECTION=100` language-detection threshold's rationale (measured vs. rule-of-thumb) is undocumented.

## Reason for Change
The API-listing tables are mechanical, code-derivable content with no design value. The threshold's undocumented rationale means a future misdetection incident would have no basis for judging whether the threshold should change.

## Implementation Intent
Remove the mechanical tables, keeping only design-relevant constants like `MIN_TEXT_LENGTH_FOR_DETECTION=100` documented individually with rationale where available.

## Target Files or Areas
`docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md`

## Required Changes
- Remove the function/signature/return-value/description table, the `LOG_KEY_*` constants table, and the usage-source table.
- Keep `MIN_TEXT_LENGTH_FOR_DETECTION=100` (and any similarly design-relevant constant) documented individually.
- Investigate whether `MIN_TEXT_LENGTH_FOR_DETECTION=100` is based on measurement or a rule-of-thumb; document the finding, or mark as Needs Confirmation if undeterminable.

## Acceptance Criteria
No verbatim API-listing table remains; `MIN_TEXT_LENGTH_FOR_DETECTION=100`'s rationale is documented or explicitly tracked as Needs Confirmation.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/03_rag_02_09` shortened and clarified.

## Out of Scope
Do not change the actual threshold value in code in this issue — documentation only.

## AI Implementation Instruction
Check commit history/design notes before concluding the rationale is unconfirmable — only fall back to a Needs Confirmation note after a reasonable investigation.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §2 削除候補 item 5, §6B (MIN_TEXT_LENGTH_FOR_DETECTION=100の根拠)
- Generated at: 2026-08-02
