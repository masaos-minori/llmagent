# Reconcile Needs-Confirmation required-field definitions between docs/00_governance_03 and docs/00_governance_07

## Priority
High

## Summary
`docs/00_governance_03_evidence-labels.md` defines 6 required fields for Needs Confirmation entries (Question/Evidence/Impact/Required Action/Target Document/Review Timing), but `docs/00_governance_07_needs-confirmation-inventory.md`'s actual inventory template uses a different field set (11-15 fields), with some similarly-named fields (e.g. "Source File"/"Last Reviewed") that don't clearly map to "Target Document"/"Review Timing".

## Reason for Change
Without a clear single source of truth, future Needs Confirmation entries risk being recorded in inconsistent formats, defeating 07's stated goal of centralized management.

## Implementation Intent
Designate one file's field definition as canonical (this review suggests 07, since it is the operational inventory in active use) and update the other to match, keeping an explicit mapping between any differently-named equivalent fields.

## Target Files or Areas
`docs/00_governance_03_evidence-labels.md`, `docs/00_governance_07_needs-confirmation-inventory.md`

## Required Changes
- Compare the 6 fields in 03 against 07's actual field list line by line.
- Decide and document which file is canonical for field definitions.
- Update the non-canonical file's field list to match, or add explicit mapping notes between differently-named equivalent fields.

## Acceptance Criteria
A single, unambiguous field definition applies to Needs Confirmation entries; 03 and 07 no longer conflict on required fields or field names.

## Testing Expectations
Not required (documentation-only). Manually re-verify a sample of existing NC-XXX entries in 07 against the reconciled definition.

## Documentation Impact
`docs/00_governance_03` and/or `docs/00_governance_07` updated to align field definitions.

## Out of Scope
Do not retroactively rewrite the content of existing NC-001 through NC-017 entries beyond field-name alignment. Do not change the Evidence Label spectrum itself (docs/00_governance_03 Evidence Labels — kept as-is per this review).

## AI Implementation Instruction
This requires a documentation-owner decision on which file is canonical — if the decision is not clear from context, register it as a Needs Confirmation item in 07 rather than guessing.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §1 (連結文書としての問題), §6 Needs confirmation item (03/07 フィールド不整合)
- Generated at: 2026-08-02
