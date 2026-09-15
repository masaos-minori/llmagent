# Add "Completed when" criteria to issue-creator workflow Phases 3-8

## Priority
Medium

## Summary
`skills/issue-creator/workflow.md` Phases 1, 2, 9, and 10 each state an explicit "Completed when" (and Phase 1 also a "Stop and ask" condition), but Phases 3 through 8 — which draft the bulk of an issue's actual content (Background/Problem/Reason for Change/Implementation Intent, Scope and Boundaries, Acceptance Criteria and Testing, Documentation Impact, Priority Assignment, AI Implementation Instruction) — have no stated completion condition at all.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session; this entry covers the most severe single finding from the "goal + exit condition" criterion. Companion issues from the same review (`skillqa01`, `skillqa02`, and others in the `skillqa`/`pyimplqa`/etc. series filed in the same batch) cover the other criteria and other files.

## Problem
Confirmed by direct reading of `skills/issue-creator/workflow.md`: Phase 3 (lines 61-79), Phase 4 (82-97), Phase 5 (100-108), Phase 6 (111-128), Phase 7 (131-149), and Phase 8 (152-158) each describe what to draft, but none states when that Phase is done — an AI agent following this workflow has no explicit signal for when it may move on, unlike Phase 1's "Completed when: source, scope, and completeness ... are all recorded" or Phase 2's "Completed when: every task from Phase 1's scope has been assigned to exactly one issue group."

## Reason for Change
Without a stated completion condition, an agent drafting an issue through Phases 3-8 has no explicit checkpoint to confirm each field is actually filled (or correctly marked `N/A`) before moving to the next Phase — this is exactly the kind of silent gap Phase 9's own Step 9c Final Checklist exists to catch retroactively, but catching it only at the end (rather than per-Phase) means a Phase 3-8 defect is found later and farther from its cause.

## Implementation Intent
Add one "Completed when" line to each of Phase 3 through 8, following the style already used in Phase 1/Phase 2, stating the minimum condition for that Phase's fields to be considered drafted (each field is filled, or explicitly marked `N/A: {reason}` per the template's own convention). Do not add a "Stop and ask" condition to every Phase — only where a genuine blocking ambiguity is possible (mirroring Phase 1's own selective use of it).

## Target Files or Areas
- `skills/issue-creator/workflow.md`

## Required Changes
- Phase 3: add "Completed when: Background, Problem, Reason for Change, and Implementation Intent are each filled or explicitly marked `N/A` with a stated reason."
- Phase 4: add "Completed when: Target Files or Areas, Required Changes, Constraints, Out of Scope, and Dependencies are each filled or explicitly marked `N/A`/`Unknown` per the template's convention."
- Phase 5: add "Completed when: every Acceptance Criteria item is independently testable by review, test execution, or documentation inspection, and Testing Expectations is filled or marked `Not required` only for a documentation-only/no-behavior-change task."
- Phase 6: add "Completed when: Documentation Impact states explicitly whether documentation must be updated, and if so, names the kind of information affected."
- Phase 7: add "Completed when: exactly one of High/Medium/Low is assigned, matching the criteria stated above for that tier."
- Phase 8: add "Completed when: the AI Implementation Instruction states concrete constraints (not a generic restatement of Phase 4's Out of Scope) an implementer must follow."

## Constraints
Do not restructure Phase 3-8's existing content — only add the completion-condition line to each, following Phase 1/Phase 2's existing phrasing style.

## Acceptance Criteria
- Each of Phase 3 through 8 in `skills/issue-creator/workflow.md` has an explicit "Completed when" line.
- The new lines are consistent in style with Phase 1/Phase 2's existing "Completed when" phrasing.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/issue-creator/workflow.md`.

## Out of Scope
- Adding a "Stop and ask"/Blocked condition to every Phase — only add one where a genuine blocking ambiguity is plausible, per Implementation Intent.
- Any other evaluation criterion from the same review — tracked in separate issues.
- Changes to `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, or `skills/code-implementation/workflow.md` — these already have adequate per-Step completion/exit conditions per the same review.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Add only the completion-condition line per Phase; do not restructure or expand the surrounding content beyond what's needed to state that condition. Match Phase 1/Phase 2's existing "Completed when" phrasing style rather than inventing a new format.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-114926
- **Related target files**: skills/issue-creator/workflow.md
