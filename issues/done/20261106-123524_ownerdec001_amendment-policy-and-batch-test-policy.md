# Owner decisions: plan amendment approval and batch full-suite runs

## Priority
Medium

## Summary
Two workflow policies are unsettled and slowed or shaped the execution of four tools Plans: who may add a fallout target file to a Frozen Plan, and when the full suite runs for a batch of procedures that are not a declared release unit.

## Background
`rules/workflow-lifecycle.md` "Plan Amendment Approval Classes (proposed)" lets an executor add a fallout file without asking and requires approval for a scope change, but it is marked proposed and has no effect until the owner accepts it. During the `toolcommon001` and `toolreport001` work, `tests/tools/test_module_nodes.py` and `tests/tools/test_check_workitem_traceability.py` had to be added to Frozen Plans because the migration broke them; they were added on the strength of the live instruction to reflect verification results. `skills/code-implementation/workflow.md` requires the full suite once per cycle, with an exception only for a declared release unit; a batch of ten or more procedures confined to `tools/` was run with one full suite at the end of each Plan instead.

## Problem
The policy text and the practice differ, and the owner has not decided either.

## Reason for Change
Each Plan of this batch needed the question answered during execution; later batches will need it again.

## Implementation Intent
Record the owner's decision on both policies, then update the two workflow documents so they state the decision.

## Target Files or Areas
`rules/workflow-lifecycle.md`, `skills/code-implementation/workflow.md`, `tools/amend_plan.py` (class option text).

## Required Changes
- Decide whether to accept the fallout versus scope amendment classes, or require approval for every amendment.
- Decide whether a batch of procedures confined to one directory may share one full-suite run, and under which conditions (same Plan, no `scripts/` change, targeted tests per cycle).
- Update the documents to the decision; remove "proposed" if accepted.

## Constraints
Do not change `tools/amend_plan.py` behavior beyond what the accepted text needs.

## Acceptance Criteria
- Both policies are stated as decided in the workflow documents.
- `tools/amend_plan.py --help` and the workflow documents agree.

## Testing Expectations
Documentation checkers named in `routing.md` for the edited rules and skills (`check_skills_references.py`, `check_skills_heading_cycles.py`).

## Documentation Impact
Yes: `rules/workflow-lifecycle.md` and `skills/code-implementation/workflow.md` (intent: when an executor may amend a Frozen Plan, and when the full suite runs for a batch).

## Out of Scope
Changing the release-unit batch mode and the Plan Freeze criteria.

## Dependencies
N/A: none

## Unresolved Questions
- Whether the full-suite exception should depend on the changed paths (for example `tools/` and `tests/tools/` only) or on a declared list.

## AI Implementation Instruction
Write the decided text; do not decide the policy yourself.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-123524
- **Related target files**: `rules/workflow-lifecycle.md`, `skills/code-implementation/workflow.md`

## Adversarial Validation

Validated against current source on 2026-11-07.

- `rules/workflow-lifecycle.md` carries `### Plan Amendment Approval Classes (proposed)` with `Status: proposed, pending the owner's decision (Plan UNK-01); it has no effect until the owner accepts it`. — Evidence: `Explicit in code` — Confidence: High
- Both unsettled policies (amendment approval classes, full-suite batch runs) are correctly framed as owner decisions, and the AI Implementation Instruction ("do not decide the policy yourself") is appropriate.

Verdict: accepted as filed.

## Content Analysis

- Type: owner decision (policy), not a code change; does not go through code-implementation.
- Outcome: owner rules on (a) fallout versus scope amendment classes, and (b) the full-suite batch-run exception, then update `rules/workflow-lifecycle.md` and `skills/code-implementation/workflow.md`.
- Scope: policy documents only; `tools/amend_plan.py` stays unchanged beyond what the accepted text needs.
- Dependency: none. Independent of the other three batch issues.
