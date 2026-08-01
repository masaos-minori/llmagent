# Resolve contradiction between "does not hardcode canonical sources" declaration and the fixed "Canonical Documents by Area" table in docs/00_governance_02

## Priority
High

## Summary
The "Canonical Documents by Area" section of `docs/00_governance_02_canonical-source-rule.md` explicitly states the document does not hardcode canonical sources, immediately followed by a table that hardcodes canonical entry points per area (e.g. `scripts/agent/`, `mcp_servers/`).

## Reason for Change
A document contradicting itself within the same section undermines trust in the governance document set and leaves unclear which table to update when an area's structure changes.

## Implementation Intent
Determine whether "document canonical source" and "code canonical entry point" are intentionally distinct concepts (in which case, state that distinction explicitly) or whether the declaration/table are simply inconsistent (in which case, reconcile them).

## Target Files or Areas
`docs/00_governance_02_canonical-source-rule.md`

## Required Changes
- Read both the declaration and the table in full context to determine intent.
- If the distinction is intentional, add a sentence clarifying: "文書としての正本と、コードとしての正典入口は別概念である" (or equivalent).
- If not intentional, reconcile the declaration and the table so they no longer contradict.

## Acceptance Criteria
The declaration and the table no longer read as directly contradictory; a reader can tell which one to update when project structure changes.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_02` clarified or reconciled.

## Out of Scope
Do not remove the per-area table's actual content unless resolving the contradiction requires it.

## AI Implementation Instruction
If the intended resolution is not determinable from context, register this as a Needs Confirmation entry in `docs/00_governance_07` rather than picking an interpretation unilaterally.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §6 Needs confirmation item ("正本を固定記述しない"宣言と直後の固定表の矛盾)
- Generated at: 2026-08-02
