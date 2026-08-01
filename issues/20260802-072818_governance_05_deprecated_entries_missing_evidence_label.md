# Add Evidence Label (Deprecated) to each docs/00_governance_05 Deprecated Document Reference entry

## Priority
Low

## Summary
`docs/00_governance_05_deprecated-items.md`'s Deprecated Document References (e.g. `diagnostics.jsonl` and others) do not carry an explicit Evidence Label as defined by `docs/00_governance_03_evidence-labels.md`, even though the governance model expects every claim to carry one of the 7 evidence labels.

## Reason for Change
Omitting the label breaks consistency with the evidence-labeling system that the rest of the governance document set relies on, making it harder to gauge confidence in each deprecated-item entry at a glance.

## Implementation Intent
Add an explicit "Evidence: Deprecated" annotation (with successor file name where applicable) to each entry, without changing the underlying "keep for reference, don't delete" policy.

## Target Files or Areas
`docs/00_governance_05_deprecated-items.md`

## Required Changes
- For each Deprecated Document Reference entry, add a line such as: "Evidence: Deprecated(廃止確認済み、後継: <ファイル名>)".

## Acceptance Criteria
Every Deprecated Document Reference entry carries an explicit Evidence Label consistent with `docs/00_governance_03`'s labeling scheme.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_05` entries gain Evidence Label annotations.

## Out of Scope
Do not change the "do not delete, keep as reference" policy itself. Do not touch the separate 4 Needs-Confirmation-formatted items in this same file (tracked in a different issue).

## AI Implementation Instruction
Apply the label consistently to every entry in this section; do not skip entries that seem "obviously" deprecated without an explicit label.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §4 強化候補 (Deprecated Document References)
- Generated at: 2026-08-02
