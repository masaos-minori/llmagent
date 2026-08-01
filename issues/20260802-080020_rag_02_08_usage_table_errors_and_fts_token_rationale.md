# Fix and compress docs/03_rag_02_08 usage-source table errors; confirm _MAX_FTS_TOKENS=20 rationale

## Priority
Medium

## Summary
`docs/03_rag_02_08_ingestion_pipeline-shared.md`'s "利用元" (usage source) table states `chunk_splitter.py` uses `normalize_unicode` (actual: only `chunk_japanese.py` does), and that `pipeline.py` uses `sanitize_document`/`floats_to_blob` (actual: the direct callers are `stages/augment.py` and `repository.py`, not `pipeline.py`). Separately, `_MAX_FTS_TOKENS = 20`'s rationale (measured vs. rule-of-thumb) is undocumented.

## Reason for Change
This is a confirmed factual error in a dependency-mapping table — a developer refactoring based on this table would misjudge which files are actually affected by a change to `normalize_unicode`/`sanitize_document`/`floats_to_blob`. The FTS-token-limit's undocumented rationale means future performance tuning has no basis for judging whether 20 is still appropriate.

## Implementation Intent
Correct the usage-source table entries to reflect actual current callers, and compress the table to list only the primary 1-2 usage sites per function rather than an exhaustive list. Investigate `_MAX_FTS_TOKENS=20`'s origin and document it, or mark as Needs Confirmation if undeterminable.

## Target Files or Areas
`docs/03_rag_02_08_ingestion_pipeline-shared.md`

## Required Changes
- Correct: `normalize_unicode` is used by `chunk_japanese.py` (not `chunk_splitter.py`).
- Correct: `sanitize_document`/`floats_to_blob` are directly called by `stages/augment.py` and `repository.py` (not `pipeline.py`).
- Compress the usage-source table to list only the primary 1-2 call sites per function.
- Investigate whether `_MAX_FTS_TOKENS=20` is based on measurement/load testing or a rule-of-thumb estimate; document the finding, or mark as Needs Confirmation if undeterminable.

## Acceptance Criteria
The usage-source table matches confirmed actual callers; it is compressed to primary usage sites; `_MAX_FTS_TOKENS=20`'s rationale is documented or explicitly tracked as Needs Confirmation.

## Testing Expectations
Not required (documentation-only). Manually re-verify actual callers via `grep -rn "normalize_unicode\|sanitize_document\|floats_to_blob" scripts/rag/` before finalizing.

## Documentation Impact
`docs/03_rag_02_08` corrected and shortened.

## Out of Scope
Do not change the actual call sites or the `_MAX_FTS_TOKENS` value in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error (usage sites) — apply directly after re-verifying against current source. Check commit history/design notes for the FTS-token-limit rationale before concluding it's unconfirmable.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §3 要約候補 item 5, §6A (「利用元」テーブルの誤り), §6B (FTS5クエリのトークン数上限20の根拠)
- Generated at: 2026-08-02
