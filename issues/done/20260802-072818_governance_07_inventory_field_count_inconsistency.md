# Fix "eleven fields" claim in docs/00_governance_07 (actual count is 15) and remove duplicate Japanese priority text

## Priority
Medium

## Summary
The Inventory Entry Fields section of `docs/00_governance_07_needs-confirmation-inventory.md` states "the following eleven fields" but enumerates 15 items. Separately, the same Priority (High/Medium/Low) explanation is duplicated: once in English, again in a "プライオリティ値(日本語)" section.

## Reason for Change
The 11-vs-15 mismatch appears to be a stale count from an earlier revision. Only 4 of 17 NC-XXX entries (NC-003, NC-008, NC-010, NC-014) currently fill in the last 4 fields (Priority/Related NC/Resolution Target/Blocking) — suggesting these are effectively optional in practice, but the text does not say so. The Japanese Priority duplication is redundant.

## Implementation Intent
Correct the stated field count to match the actual enumeration, explicitly mark which fields are required vs. optional (matching actual usage), and merge the duplicate Japanese Priority explanation into the single canonical field description.

## Target Files or Areas
`docs/00_governance_07_needs-confirmation-inventory.md`

## Required Changes
- Change "eleven fields" to the correct count (15, or whatever count results after any field consolidation from the related 03/07 field-mismatch issue).
- Add required/optional marking to each field, based on actual current usage across NC-001–017.
- Remove the separate "プライオリティ値(日本語)" section; fold its content into the single Priority field description, e.g. "Priority: High / Medium / Low(高: ブロッキング, 中: 要対応, 低: 参考情報)".

## Acceptance Criteria
Stated field count matches actual enumerated fields; required/optional status is explicit per field; no duplicate Priority explanation remains.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_07` updated for internal consistency.

## Out of Scope
Do not change the field reconciliation with `docs/00_governance_03` in this issue (tracked separately). Do not rewrite existing NC-XXX entry content.

## AI Implementation Instruction
Base the required/optional determination on actual observed usage across existing entries, not assumption. Coordinate with the related 03/07 field-mismatch issue if both are worked in the same pass, since fixing one may change the field count in the other.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §6 Needs confirmation item ("eleven fields"記述と実際15項目の食い違い), §3 要約候補 item 5
- Generated at: 2026-08-02
