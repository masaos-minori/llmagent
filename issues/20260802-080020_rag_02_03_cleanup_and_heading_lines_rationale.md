# Simplify docs/03_rag_02_03 (parts 1+2): remove constant/method tables, compress --force description, confirm MIN_HEADING_LINES_FOR_MARKDOWN=2 rationale

## Priority
Medium

## Summary
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md` lists module-level constants and public methods verbatim, with threshold values but no selection rationale (including `MIN_HEADING_LINES_FOR_MARKDOWN=2`, whose determination basis — experimental tuning vs. convention — is undocumented). `docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md`'s CLI-argument table describes the `--force` option verbosely.

## Reason for Change
The constant/method tables are mechanical code transcription. The `--force` description is more verbose than needed for a simple flag. `MIN_HEADING_LINES_FOR_MARKDOWN=2`'s rationale, if determinable, would help future implementers judge whether changing the threshold is safe.

## Implementation Intent
Remove the mechanical tables, keeping only design-relevant threshold values with rationale where available. Compress the `--force` description to one line. Investigate `MIN_HEADING_LINES_FOR_MARKDOWN=2`'s origin (experimental vs. convention) and document it, or mark as Needs Confirmation if undeterminable.

## Target Files or Areas
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`, `docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md`

## Required Changes
- Remove the module-level constants table and public-methods table in `part1`; keep only `MIN_HEADING_LINES_FOR_MARKDOWN` (and similar design-relevant thresholds) with available rationale.
- Compress the `--force` CLI-argument description in `part2` to: "`--force`: センチネルチェックを無視し既存チャンクを再生成する。"
- Investigate whether `MIN_HEADING_LINES_FOR_MARKDOWN=2` is based on experimental tuning or convention; document the finding, or mark as an explicit Needs Confirmation item if the author's rationale can't be determined.

## Acceptance Criteria
No verbatim constant/method table remains beyond design-relevant thresholds; `--force` is described in one line; `MIN_HEADING_LINES_FOR_MARKDOWN=2`'s rationale is documented or explicitly tracked as Needs Confirmation.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
Both parts of `docs/03_rag_02_03` corrected and shortened.

## Out of Scope
Do not change the actual constant values in code in this issue — documentation only.

## AI Implementation Instruction
Check commit history/design notes for `MIN_HEADING_LINES_FOR_MARKDOWN`'s origin before concluding it's unconfirmable — only fall back to a Needs Confirmation note after a reasonable investigation.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §2 削除候補 item 2, §3 要約候補 item 4, §6B (MIN_HEADING_LINES_FOR_MARKDOWN=2の決定根拠)
- Generated at: 2026-08-02
