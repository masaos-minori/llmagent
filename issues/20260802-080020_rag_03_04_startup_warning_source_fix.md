# Fix docs/03_rag_03_04 startup-warning source reference (pipeline.py, not config_validator.py)

## Priority
Medium

## Summary
`docs/03_rag_03_04_query_pipeline-search-stages.md`'s "検索品質のトレードオフ" (search-quality tradeoff) section, describing `use_rrf=False`, states the startup-time warning is emitted via `config_validator.py`, but confirmed source reading shows it is actually emitted directly in `pipeline.py` (around lines 152-155).

## Reason for Change
This is a confirmed factual error — an operator investigating why a warning appeared (or troubleshooting why it didn't) would look in the wrong file, delaying root-cause identification.

## Implementation Intent
Correct the reference to point to `pipeline.py`, while keeping the rest of this section's content intact, since this review confirms the trade-off explanation itself (alternative considered and rejected) is accurate and exemplary design-decision documentation.

## Target Files or Areas
`docs/03_rag_03_04_query_pipeline-search-stages.md`

## Required Changes
- Replace the `config_validator.py` reference with: "`use_rrf=False`設定時はpipeline.py内で起動時に警告ログが出力される(config_validator.py経由ではない)。"

## Acceptance Criteria
The section correctly attributes the startup warning to `pipeline.py`, not `config_validator.py`.

## Testing Expectations
Not required (documentation-only). Manually re-verify the warning's actual emission location in `pipeline.py` before finalizing, in case the line numbers/location have shifted.

## Documentation Impact
`docs/03_rag_03_04` corrected.

## Out of Scope
Do not change the actual warning-emission code in this issue — documentation only. Do not touch the `[debug]`-output issue in this file, tracked separately.

## AI Implementation Instruction
This is a confirmed factual error — apply directly after re-verifying the exact current location in `pipeline.py`.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §4 強化候補 (03_04 use_rrf=False), §6A (use_rrf=False時の起動時警告の出力元不一致)
- Generated at: 2026-08-02
