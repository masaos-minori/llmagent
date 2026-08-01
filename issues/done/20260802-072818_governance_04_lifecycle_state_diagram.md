# Add a state-transition diagram or table to docs/00_governance_04 Known Issue Lifecycle section

## Priority
Low

## Summary
The Lifecycle section of `docs/00_governance_04_known-issues-template.md` describes the open → investigating → fixed/deferred/wontfix → deprecated transitions in prose only, which is more error-prone to follow correctly than a visual/tabular representation.

## Reason for Change
Prose-only state machine descriptions are more easily misread or misapplied than an explicit table or diagram, especially when applying the lifecycle rule mechanically.

## Implementation Intent
Add a state-transition table (current state / transition condition / next state) alongside the existing prose, without removing the prose explanation.

## Target Files or Areas
`docs/00_governance_04_known-issues-template.md`

## Required Changes
- Add a table with columns: 現在の状態 / 遷移条件 / 遷移先, covering all states and transitions currently described in prose.

## Acceptance Criteria
The Lifecycle section includes a table that fully covers the same transitions as the existing prose, with no discrepancy between the two.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_04` gains a lifecycle table.

## Out of Scope
Do not change the actual lifecycle states or transition conditions, only add a tabular representation.

## AI Implementation Instruction
Derive the table strictly from the existing prose; do not invent transitions or states not already described.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §4 強化候補 (Lifecycle)
- Generated at: 2026-08-02
