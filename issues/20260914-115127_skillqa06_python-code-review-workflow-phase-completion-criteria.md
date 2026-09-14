# Add "Completed when" criteria to python-code-review workflow Phases 2-9

## Priority
Medium

## Summary
`skills/python-code-review/workflow.md` Phase 1 and Phase 10 each state an explicit "Completed when," but Phases 2 through 9 — which contain this skill's entire review checklist (Correctness, Architecture, Async/Resource Lifecycle, Error Handling, Tests, Documentation, Evidence Assignment, Report Writing) — have no stated completion condition.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session. Companion issues from the same review cover other files.

## Problem
Confirmed by direct reading of `skills/python-code-review/workflow.md` lines 43-118: Phases 2 through 9 are each structured as a "Do:" checklist (e.g. Phase 2 lists 6 checks: edge cases, state transitions, import direction, responsibility boundaries, typing correctness, lint/type tool run), but none states when that checklist is considered satisfied — unlike Phase 1's "Completed when: the diff boundary and stated intent are both recorded" or Phase 10's "Completed when: every grouped finding from 10a has a drafted issue from 10b that has [passed Phase 9]."

## Reason for Change
A checklist Phase with no completion condition risks an agent treating "I read the list" as equivalent to "I checked every item against the actual diff" — the two are not the same, and only the latter is the intended completion state.

## Implementation Intent
Add one "Completed when" line to each of Phase 2 through 9, stating that every "Do:" item in that Phase has been checked against the actual diff (not merely read), following Phase 1/Phase 10's existing phrasing style.

## Target Files or Areas
- `skills/python-code-review/workflow.md`

## Required Changes
- Phase 2: add "Completed when: every check above has been applied to each changed function in the diff, and `ruff check`/`mypy`/`pyright` have been run on touched files."
- Phase 3: add "Completed when: dependency direction and abstraction-introduction checks have been applied to every changed import/interface in the diff."
- Phase 4: add "Completed when: every changed `async def`/resource-acquiring code path in the diff has been checked for blocking calls and cleanup on both normal and exception paths."
- Phase 5: add "Completed when: every changed error-handling/config/logging code path has been checked, and `bandit` has been run where available."
- Phase 6: add "Completed when: test coverage has been checked for every critical/edge/failure path touched by the diff, and `pytest` has been run to confirm the claimed pass/fail state."
- Phase 7: add "Completed when: every doc claim about the changed behavior has been checked against the current implementation, not against a prior-version recollection."
- Phase 8: add "Completed when: every finding carried forward from Phases 2-7 has concrete evidence, an evidence label/confidence level, and a severity assigned."
- Phase 9: add "Completed when: the report follows `SKILL.md`'s Output Format, findings are grouped by severity, and no style-only issue is over-reported."

## Constraints
Do not change any Phase's actual checklist content — only add the completion-condition line per Phase.

## Acceptance Criteria
- Each of Phase 2 through 9 in `skills/python-code-review/workflow.md` has an explicit "Completed when" line.
- Each new line ties completion to the actual diff/findings, not merely to having read the checklist.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/python-code-review/workflow.md`.

## Out of Scope
- Phase 1 and Phase 10 — already have adequate completion conditions.
- Any other evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Add only the completion-condition line per Phase; do not restructure the existing "Do:" checklists. Match Phase 1/Phase 10's existing "Completed when" phrasing style.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115127
- **Related target files**: skills/python-code-review/workflow.md
