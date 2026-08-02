# Fix or remove nonexistent [debug] output example in docs/03_rag_03_02-part2 and 03_04

## Priority
Medium

## Summary
Both `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md` and `docs/03_rag_03_04_query_pipeline-search-stages.md` show an example `/rag search --debug` output containing `[debug] http mode: ...` / `[debug] fusion: ...` lines, but a repository-wide search finds no occurrence of the string `[debug]` anywhere in the codebase.

## Reason for Change
This is a confirmed factual error — an operator trying to use `--debug` expecting this output format would be confused when it doesn't appear, wasting troubleshooting time.

## Implementation Intent
Determine whether this debug output was renamed/reimplemented differently, or was never actually implemented (documented aspirationally but not built). Update or remove the example in both files consistently based on the finding.

## Target Files or Areas
`docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`, `docs/03_rag_03_04_query_pipeline-search-stages.md`

## Required Changes
- Investigate the current debug-output mechanism for `/rag search` (if any) via source inspection — check for renamed prefixes, alternate flags, or structured-log-based debug output.
- If a current equivalent exists, replace the `[debug]` example with the actual current output format in both files.
- If no such feature currently exists, remove the example entirely from both files and note (if relevant) that this was likely a planned-but-unimplemented feature.

## Acceptance Criteria
Neither file shows a `[debug]`-prefixed output example unless it is confirmed to exist in current code; both files are updated consistently with the same finding.

## Testing Expectations
Not required (documentation-only). Manually verify via `grep -rn "\[debug\]" scripts/` (expect no results, or find the actual current mechanism) before finalizing.

## Documentation Impact
Both files corrected consistently.

## Out of Scope
Do not implement a `--debug` output feature in this issue if one doesn't currently exist — documentation only, reflecting current reality.

## AI Implementation Instruction
Investigate thoroughly before deciding whether to replace or simply remove the example — do not guess at a replacement format without confirming it exists in source.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (横断的な確定済み誤り item 6), §6A ([debug]出力例の非実在)
- Generated at: 2026-08-02
