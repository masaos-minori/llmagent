# Clarify relationship between docs/00_governance_02 Resolution Workflow (5 steps) and Conflict Resolution Rule (4 steps)

## Priority
Medium

## Summary
`docs/00_governance_02_canonical-source-rule.md` defines both a 5-step "Resolution Workflow" and a 4-step "Conflict Resolution Rule" with substantial content overlap, but does not state whether one is a specific instance of the other or how they relate.

## Reason for Change
Without an explicit relationship, readers cannot tell whether to follow one process, the other, or both, when resolving a conflict.

## Implementation Intent
Add a short statement at the start of Resolution Workflow clarifying that it is the overall process encompassing the individual rules (Conflict Resolution Rule, Code vs Document Conflict Rule, Known Issues Registration Rule) in execution order.

## Target Files or Areas
`docs/00_governance_02_canonical-source-rule.md`

## Required Changes
- Add an introductory sentence to the Resolution Workflow section stating it integrates the individual rules (Conflict Resolution Rule / Code vs Document Conflict Rule / Known Issues Registration Rule) into one ordered process.

## Acceptance Criteria
A reader can determine from the text alone whether Resolution Workflow supersedes, wraps, or duplicates Conflict Resolution Rule.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_02` gains one clarifying sentence; no other content changes.

## Out of Scope
Do not merge or restructure the two step lists themselves in this issue.

## AI Implementation Instruction
If the actual intended relationship is unclear from context, register it as a Needs Confirmation item in `docs/00_governance_07` instead of guessing.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §3 要約候補 item 2
- Generated at: 2026-08-02
