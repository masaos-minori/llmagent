# Require Plan target rows in implementation order

## Priority
Medium

## Summary
State and check that the order of the `Implementation Target Files` rows is the implementation order, so the dependency of a row precedes it and no procedure is generated in a breaking order.

## Background
Evidence (`Explicit in code`): `skills/plan-to-implementation-procedure/workflow.md` "Workflow position" defines `seq` as the row's position in the table and the order of `code-implementation` as `seq` order. In the 2026-11-27 session the Plans for wfeff008 and wfeff009 both listed a dependent row before the row it depends on (a gate runner before the renderer it calls; a workflow file before the edge file that must receive its text first); the order was corrected only during procedure generation (Step 3a).

## Problem
Nothing in `templates/plan.md`, `skills/issue-to-plan/workflow.md` Step 8, or a checker states that the row order is the implementation order, so a wrong order is found late.

## Reason for Change
A wrong order breaks the targeted tests between procedures (no allowed red states in a plan batch) or loses text between a move and its destination.

## Implementation Intent
State the rule where the Plan is written and verified; evaluate whether a mechanical check is possible.

## Target Files or Areas
- `templates/plan.md`
- `skills/issue-to-plan/workflow.md`

## Required Changes
- Add to `templates/plan.md` (Implementation Target Files rules) that the row order is the implementation order and a row another row depends on comes first.
- Add to `skills/issue-to-plan/workflow.md` Step 8a one verification: each row's dependency (a created file before its user, a moved text's destination before its source, a callee before its caller) precedes it.
- Record in the issue's follow-up whether a mechanical check can be derived from Plan data (the table has no dependency column).

## Constraints
- `templates/plan.md` and `skills/issue-to-plan/workflow.md` are size-gated: `tools/check_skill_size_baseline.txt` ceilings apply (`skills/issue-to-plan/workflow.md` had about 430 B of headroom on 2026-11-27).
- The Plan template's heading set is unchanged.

## Acceptance Criteria
- [ ] The template and Step 8a state the rule.
- [ ] Both files stay at or below their ceilings.
- [ ] `tools/check_workitem_structure.py` and the skill checks pass.

## Testing Expectations
`tools/check_skill_size.py`, `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, `tools/check_workitem_structure.py`; one past Plan rechecked against the rule.

## Documentation Impact
Yes. The two files only.

## Out of Scope
- A new Plan field or table column.
- Reordering existing archived Plans.

## Dependencies
- Related: issues/20261127-120059_flowopt001_skill-size-fallout-check.md (the size headroom of `skills/issue-to-plan/workflow.md`); either order of the two issues works.

## Unresolved Questions
- `不明`: whether the order can be checked mechanically; this issue only states and verifies the rule by reading.

## AI Implementation Instruction
Edit text only; measure `wc -c` before and after each file. Do not add a checker in this issue.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120100
- **Related target files**: `templates/plan.md`, `skills/issue-to-plan/workflow.md`
