# Simplify docs/03_rag_02_01 file-lifecycle table

## Priority
Low

## Summary
`docs/03_rag_02_01_ingestion_pipeline-overview.md`'s "ファイルのライフサイクル" (file lifecycle) table lists output file paths for each stage, duplicating detail already present in the `02_02`/`02_03`/`02_04` detail files.

## Reason for Change
Maintaining the same file-path detail at both the overview and detail-document levels doubles maintenance effort and risks silent divergence.

## Implementation Intent
Reduce this table to the overview-appropriate level: the 3-stage flow (crawl → split → ingest) and the general output-directory structure, deferring filename-level detail to the respective detail documents.

## Target Files or Areas
`docs/03_rag_02_01_ingestion_pipeline-overview.md`

## Required Changes
- Reduce the file-lifecycle table to describe the crawl → split → ingest flow and general output-directory placement only.
- Remove filename-level detail, replacing it with references to `docs/03_rag_02_02`, `02_03`, `02_04` for stage-specific detail.

## Acceptance Criteria
The table conveys only the 3-stage flow and output-directory structure; filename-level detail is deferred via reference to the detail documents.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/03_rag_02_01` shortened.

## Out of Scope
Do not edit `docs/03_rag_02_02`/`02_03`/`02_04` in this issue (their own fixes are tracked separately).

## AI Implementation Instruction
Keep the summary to the stage-flow level; do not re-introduce filename-level detail that belongs in the detail documents.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §3 要約候補 item 2
- Generated at: 2026-08-02
