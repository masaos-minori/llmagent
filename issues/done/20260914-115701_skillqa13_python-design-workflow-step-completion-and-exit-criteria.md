# Add completion/exit criteria to python-design workflow Steps 3, 5, 6, 7

## Priority
Low

## Summary
`skills/python-design/workflow.md` Step 3 (Define Architecture) has a "Completed when" line but no exit/Blocked condition; Steps 5 (Design Data and Persistence), 6 (Define Error Handling), and 7 (Define Test Strategy) have neither a completion nor an exit condition, unlike Steps 1, 2, 4, 8, 9 in the same file.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session. Note: re-verified during this issue's drafting that `python-design/SKILL.md` line 77 ("Use abstractions only when justified: no abstract factories, `Protocol`, or `abc.ABC` without a concrete requirement") already defines "justified" concretely in the same sentence — the review's initial "vague qualifier" concern for this term was not confirmed and is not included here.

## Problem
Confirmed by direct reading of `skills/python-design/workflow.md`:
- Step 3 (lines 41-73): has "Completed when: Components, Boundaries, Control flow, and Data flow are all defined and the component count is justified against Step 2's use cases" but no stated condition for what to do if that cannot be achieved (e.g. the component count cannot be justified against Step 2's use cases even after attempting to merge components).
- Step 5 (109-122), Step 6 (126-142), Step 7 (146-152): each lists concrete design items to produce (entity fields/validation/storage/serialization; failure-mode detection/response/logging/visibility; unit/integration/edge-case/failure-path test categories) but state no "Completed when" at all.

## Reason for Change
Steps 5-7 produce design artifacts (data model, error-handling design, test strategy) that later Steps (8, Implementation Plan) depend on — an agent with no stated completion condition for these Steps has no explicit checkpoint confirming each entity/failure-mode/module was actually covered before moving on.

## Implementation Intent
Add a "Completed when" line to Steps 5, 6, and 7 (mirroring Step 4's per-module completion style), and add an exit condition to Step 3 for the case where the component count cannot be justified even after the merge check already described in that Step.

## Target Files or Areas
- `skills/python-design/workflow.md`

## Required Changes
- Step 3: add "If the component count cannot be justified against Step 2's use cases even after attempting to merge components per the rule above: stop and report the specific components that could not be justified or merged, rather than proceeding with an unjustified count."
- Step 5: add "Completed when: every entity identified has Fields and types, Validation rules, Storage, and Serialization all specified."
- Step 6: add "Completed when: every failure mode identified has Detection, Response, Logging, and User visibility all specified, and every resource requiring a `with`/`async with` boundary has it stated."
- Step 7: add "Completed when: every module has at least one specified test category (unit, integration, edge case, or failure-path) matching its actual I/O/boundary characteristics from Step 4."

## Constraints
Do not add a numeric threshold (e.g. "at least N entities") — completion is about coverage of the items already in scope from earlier Steps, not an arbitrary count.

## Acceptance Criteria
- Step 3 has an explicit exit condition for the unjustifiable-component-count case.
- Steps 5, 6, and 7 each have an explicit "Completed when" line.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/python-design/workflow.md`.

## Out of Scope
- The "justified"/abstraction-qualifier concern — already adequately defined in `SKILL.md` line 77, confirmed during this issue's drafting; no change needed.
- Steps 1, 2, 4, 8, 9 — already have adequate completion/exit conditions.
- Any other evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Add only the four items described in Required Changes; do not modify the "justified"/abstraction wording in `SKILL.md` or elsewhere in `workflow.md` — it is already adequately defined.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115701
- **Related target files**: skills/python-design/workflow.md
