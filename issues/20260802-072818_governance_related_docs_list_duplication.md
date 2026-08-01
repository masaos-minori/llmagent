# Consolidate duplicate "Related Governance Documents" list across governance docs 01-07

## Priority
Medium

## Summary
The same 6-item "Related Governance Documents" link list is duplicated verbatim across `docs/00_governance_01` through `docs/00_governance_07` (7 files). Replace the duplicates with a single reference to 01.

## Reason for Change
Template-level duplication across 7 files creates update-drift risk; adding, removing, or renaming a governance doc currently requires 7 separate edits to stay accurate.

## Implementation Intent
Treat `docs/00_governance_01_documentation-governance.md` as the canonical holder of the full list. Replace the list in the other files with a one-line reference pointing to 01.

## Target Files or Areas
`docs/00_governance_01_documentation-governance.md` through `docs/00_governance_07_needs-confirmation-inventory.md` — confirm by grep exactly which of 02-07 currently contain the full duplicated list before editing.

## Required Changes
- Grep for the duplicated "Related Governance Documents" block across `docs/00_governance_*.md` to confirm scope.
- Keep the full list only in `docs/00_governance_01_documentation-governance.md`.
- Replace the list in each other affected file with a single reference line, e.g. "関連文書一覧は `docs/00_governance_01_documentation-governance.md` を参照。"

## Acceptance Criteria
- Only `docs/00_governance_01` contains the full 6-item list.
- Each other affected file has exactly one reference line instead.
- No broken links are introduced.

## Testing Expectations
Not required (documentation-only, no behavior change). Manually re-grep for the list pattern across `docs/00_governance_*.md` after the change to confirm no duplicates remain.

## Documentation Impact
`docs/00_governance_01` through `07` updated. No other docs affected.

## Out of Scope
Do not change the content of the list itself (item names/order). Do not touch `docs/00_governance_08` or `docs/00_index.md` in this issue.

## AI Implementation Instruction
Grep for the exact duplicated block first to confirm scope before editing. Do not rewrite unrelated sections of these files. Keep the reference wording consistent across all files touched.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §2 (削除候補: なし, but see §3 要約候補 item 1) and §5 例1
- Generated at: 2026-08-02
