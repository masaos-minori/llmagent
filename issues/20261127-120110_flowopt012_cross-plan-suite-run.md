# Decide whether consecutive Plan batches may share one full-suite run

## Priority
Low

## Summary
Record the owner's decision on whether the full test suite may run once for consecutive plan batches of the same session, and update the batch text to match.

## Background
Evidence (`Explicit in code`): `skills/code-implementation/workflow-edge.md` "Batch mode (plan batch)" runs the full suite and the diff-cover gate once per plan batch of one Plan. The archived issue `issues/done/20261106-123524_ownerdec001_amendment-policy-and-batch-test-policy.md` settled that sharing for procedures of one Plan. On 2026-11-27 three consecutive Plan batches each ran the full suite (about 2.5 to 3 minutes each, once about 10 minutes).

## Problem
Whether the saving can extend across Plans (for example tools-only and skills-only Plans with no `scripts/` change) is not decided.

## Reason for Change
Waiting time per Plan; the risk is that a failure can no longer be tied to one Plan.

## Implementation Intent
Obtain a decision with explicit conditions, then write it down.

## Target Files or Areas
- `skills/code-implementation/workflow-edge.md`

## Required Changes
- Record the decision and its conditions (for example: no `scripts/` or `config/` change in any member Plan, per-Plan targeted tests still pass, each Plan's changed-file list recorded in its Notes so a failure can be attributed).
- Update "Batch mode (plan batch)" to the decision; keep the single-Plan text as the default if the decision is no.

## Constraints
- A failed shared run must be attributable per Plan; the text must say how.
- `skills/code-implementation/workflow-edge.md` stays under 20480 B (15160 B on 2026-11-27).

## Acceptance Criteria
- [ ] The decision and its conditions are written in the workflow text.
- [ ] The text states how a failure is attributed to a Plan.

## Testing Expectations
`tools/check_skill_size.py`, `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`.

## Documentation Impact
Yes. The batch mode section.

## Out of Scope
- Changing the release-unit batch mode or the diff-cover threshold.

## Dependencies
N/A: none

## Unresolved Questions
- `不明`: whether the owner accepts sharing across Plans, and under which conditions.

## AI Implementation Instruction
Write the decided text; do not decide the policy yourself.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120110
- **Related target files**: `skills/code-implementation/workflow-edge.md`
