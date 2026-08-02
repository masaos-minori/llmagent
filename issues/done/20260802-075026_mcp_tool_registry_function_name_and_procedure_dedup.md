# Fix nonexistent check_routing_drift_vs_live(), consolidate "add new tool" procedure, and add missing _SIDE_EFFECT_TOOLS constants (docs/04_mcp_03_02 + 03_05)

## Priority
High

## Summary
Both `docs/04_mcp_03_02_tool-registry.md` and `docs/04_mcp_03_05_lifecycle-and-new-server.md` reference a function `check_routing_drift_vs_live()` that does not exist in source — the actual function is `validate_routing_against_live()` in `tool_routing_validation.py`. The same 7-step "add a new tool" procedure is duplicated (effectively triplicated) across both files. Separately, `03_02` lists side-effect tool constants but omits 3 that exist in code: `CICD_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `MDQ_WRITE_TOOLS`.

## Reason for Change
The nonexistent function name is a confirmed factual error appearing in 2 files — a developer following either file would get an import error. The procedure duplication doubles maintenance cost for identical content. The missing constants leave the side-effect-tools list incomplete, risking a gap in write-operation safety review.

## Implementation Intent
Correct the function name in both files. Consolidate the "add new tool" procedure into `03_05` (the lifecycle document) as canonical, reducing `03_02`'s copy to a 3-line summary plus a link. Add the 3 missing constants to `03_02`'s side-effect tools listing.

## Target Files or Areas
`docs/04_mcp_03_02_tool-registry.md`, `docs/04_mcp_03_05_lifecycle-and-new-server.md`

## Required Changes
- Replace `check_routing_drift_vs_live()` with `validate_routing_against_live()` (from `tool_routing_validation.py`) in both files.
- Reduce `03_02`'s "add new tool" procedure to a 3-line summary with a link to the full procedure in `03_05`; keep the full 7-step procedure only in `03_05`.
- Add `CICD_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `MDQ_WRITE_TOOLS` to `03_02`'s side-effect tools listing, confirming first whether their omission was intentional or an oversight.

## Acceptance Criteria
Neither file references `check_routing_drift_vs_live()`; the "add new tool" procedure exists in full only in `03_05`, with `03_02` reduced to a summary+link; `03_02`'s side-effect tools listing includes all confirmed constants.

## Testing Expectations
Not required (documentation-only). Manually verify `validate_routing_against_live()`'s existence and signature in `tool_routing_validation.py`, and the 3 constants' existence, before finalizing.

## Documentation Impact
Both files corrected and deduplicated.

## Out of Scope
Do not change the actual tool-routing validation implementation in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error (function name) — apply directly. Verify the 3 side-effect-tool constants' existence in source before adding them.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 items 7-8, 連結文書としての問題), §3 要約候補 item 1, §5 例5, §6A (check_routing_drift_vs_live, _SIDE_EFFECT_TOOLS)
- Generated at: 2026-08-02
