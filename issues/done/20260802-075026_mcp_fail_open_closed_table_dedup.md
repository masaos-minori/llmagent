# Deduplicate Fail-Open/Closed summary table across docs/04_mcp_05_03 and 05_05

## Priority
Medium

## Summary
The same Fail-Open/Fail-Closed risk-tier summary table is duplicated (effectively in 3 places) across `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` and `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`.

## Reason for Change
Maintaining the same risk-tier classification table in 2 files doubles the update burden whenever risk-tier policy changes, and risks silent divergence between the two copies over time.

## Implementation Intent
Make `05_03` the canonical home for the general Fail-Open/Closed risk-tier summary table; reduce `05_05` to its MDQ-specific additional rules (e.g. deny-all lockdown behavior) plus a reference to `05_03` for the shared baseline.

## Target Files or Areas
`docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

## Required Changes
- Keep the full Fail-Open/Closed summary table only in `05_03`.
- In `05_05`, replace the duplicated table with: "Fail-open/fail-closed基本方針は `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` を参照。mdq-mcp固有のロックダウン規則(deny-all時の挙動)は本ファイル末尾に別途記載。" plus the actual mdq-specific rules retained below it.

## Acceptance Criteria
Only `05_03` contains the full risk-tier summary table; `05_05` contains a reference plus its own mdq-specific rules, with no duplicated table content.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`05_03` and `05_05` both updated for consistency.

## Out of Scope
Do not change the actual fail-open/fail-closed risk-tier classification or policy in this issue — documentation only.

## AI Implementation Instruction
Verify the two tables are actually identical (or identify any genuine mdq-specific differences) before deciding what to keep in `05_05` versus what to remove.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (連結文書としての問題), §3 要約候補 item 2
- Generated at: 2026-08-02
