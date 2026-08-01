# Update docs/04_mcp_06_04 Major Default Values table: add missing half_open_cooldown_sec and evidence/source column

## Priority
Low

## Summary
`docs/04_mcp_06_04`'s Major Default Values table omits `half_open_cooldown_sec` (30 seconds), and does not distinguish which values are directly verified against code versus estimated/unmeasured.

## Reason for Change
A missing entry in a "major default values" table undermines its completeness, and the lack of a source/evidence indicator makes it impossible for a reader to know which numbers to trust without independently re-verifying every one.

## Implementation Intent
Keep the table structure, add the missing `half_open_cooldown_sec` row, and add a source/evidence column marking each value as either "measured (confirmed against code as of [reference])" or "estimated (unmeasured, Needs confirmation)."

## Target Files or Areas
`docs/04_mcp_06_04`

## Required Changes
- Add a row for `half_open_cooldown_sec` with value `30` and a "measured" source marking.
- Add a source/evidence column to the existing table, marking each existing row as measured (with a code-confirmation reference) or estimated (Needs confirmation) based on actual verification status.

## Acceptance Criteria
The table includes `half_open_cooldown_sec`; every row has an explicit source/evidence marking distinguishing measured values from estimates.

## Testing Expectations
Not required (documentation-only). Manually verify each value against source before marking it "measured."

## Documentation Impact
`docs/04_mcp_06_04` table extended with one new row and one new column.

## Out of Scope
Do not change the actual default values in code in this issue — documentation only.

## AI Implementation Instruction
Only mark a value "measured" if you have actually re-verified it against current source in this pass — do not carry forward a "measured" label from this review without re-confirming it yourself.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §3 要約候補 item 4
- Generated at: 2026-08-02
