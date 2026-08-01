# Replace docs/00_governance_04 Area Values list with a reference to docs/00_governance_01 In Scope

## Priority
Low

## Summary
`docs/00_governance_04_known-issues-template.md`'s "Area Values" (8-area enumeration) duplicates `docs/00_governance_01`'s "In scope" list verbatim.

## Reason for Change
Maintaining the same 8-item list in two places risks drift if scope areas change in the future.

## Implementation Intent
Make `docs/00_governance_01`'s "In scope" section canonical; have 04 reference it instead of re-listing the areas.

## Target Files or Areas
`docs/00_governance_04_known-issues-template.md`, `docs/00_governance_01_documentation-governance.md`

## Required Changes
- Verify the two lists are identical (compare content item by item).
- Replace 04's Area Values enumeration with a reference sentence, e.g. "対象領域は `docs/00_governance_01_documentation-governance.md` のIn scopeで定義される8領域と同一。"
- Keep 01's In scope list unchanged.

## Acceptance Criteria
04 no longer independently enumerates the 8 areas; a single reference sentence points to 01.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_04` updated to reference `docs/00_governance_01`.

## Out of Scope
Do not alter the actual set of areas/scope. Do not touch other governance files.

## AI Implementation Instruction
Verify list identity before replacing; if the lists differ in even one item, stop and report the discrepancy instead of silently reconciling.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §1 (重複している情報の傾向), §3 要約候補 item 3
- Generated at: 2026-08-02
