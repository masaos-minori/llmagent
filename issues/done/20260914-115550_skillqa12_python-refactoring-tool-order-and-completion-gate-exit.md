# Fix validation.md's tool-order mismatch and add an exit condition to report-template.md's Completion Gate

## Priority
Low

## Summary
`skills/python-refactoring/validation.md` lists a validation order ("Run mypy. Cross-check with pyright. Run ruff. Run characterization tests.") that does not match `workflow.md` Step 6's actual order (ruff format/check --fix runs immediately after each transformation, with mypy/pyright/tests run per logical diff group afterward). `skills/python-refactoring/report-template.md`'s Completion Gate lists pass conditions but states no exit/Blocked condition for when they cannot all be satisfied.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session. Note: the same review's finding about negative-only instructions without positive alternatives in `python-refactoring/SKILL.md` and `test-audit/SKILL.md`/`workflow.md` is already tracked in `skillqa01` — not repeated here.

## Problem
Confirmed by direct reading:
- `validation.md` (lines 44-47) states the order "mypy → pyright → ruff → characterization tests," but `workflow.md` (line 236) states "Run `ruff format` and `ruff check --fix` after each transformation," and line 273 states "Run tests, `ruff`, and `mypy` once per logical group" — i.e., the actual, intended order is ruff (immediately post-transform) before mypy/tests, the reverse of what `validation.md` states in isolation.
- `report-template.md`'s Completion Gate (lines 90-104) lists 9 pass conditions ("Target behavior is locked...", "External behavior is unchanged...", etc.) with no statement of what happens when one cannot be satisfied — contrast with this same file's own `Blocked` status handling elsewhere (line 27, 71, 84, 101), which exists for other sections but is not connected to the Completion Gate's own pass/fail logic.

## Reason for Change
`validation.md`'s stated order, read on its own (e.g. by an agent that consults it without also having `workflow.md` Step 6 loaded), would lead to running mypy/pyright before the post-transform `ruff format`/`--fix` pass — producing mypy findings against not-yet-reformatted code, which is wasted or misleading work. The Completion Gate's missing exit condition leaves ambiguous whether one failed item blocks the whole refactoring or can be reported as a partial pass.

## Implementation Intent
Correct `validation.md`'s stated order to match `workflow.md` Step 6's actual sequence; add an exit condition to the Completion Gate stating that any unsatisfied required item routes to `Blocked` (using this file's own existing `Blocked` vocabulary) rather than being silently dropped or averaged into a partial pass.

## Target Files or Areas
- `skills/python-refactoring/validation.md`
- `skills/python-refactoring/report-template.md`

## Required Changes
- `validation.md`: reorder the four listed items to "Run `ruff format`/`ruff check --fix` (per `workflow.md` Step 6, immediately after each transformation). Run `mypy`. Cross-check with `pyright`. Run characterization tests." — matching the actual sequence in `workflow.md`.
- `report-template.md` Completion Gate: add "If any required item above cannot be satisfied: report `Blocked` (per this file's existing `Blocked` status vocabulary) rather than a partial pass — a Completion Gate item is not conditional/optional like the validation items covered by `Not run`/`Blocked` status elsewhere in this template."

## Constraints
Do not change `workflow.md` Step 6's actual behavior — this issue only corrects `validation.md`'s description of it, and adds an exit condition to `report-template.md` without changing its existing pass-condition list.

## Acceptance Criteria
- `validation.md`'s stated tool order matches `workflow.md` Step 6's actual sequence.
- `report-template.md`'s Completion Gate states an explicit exit condition (`Blocked`) for any unsatisfied required item.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only files. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/python-refactoring/validation.md` and `skills/python-refactoring/report-template.md`.

## Out of Scope
- The negative-instruction/positive-alternative gap in `python-refactoring/SKILL.md` and `test-audit` files — already tracked in `skillqa01`.
- Any other file or evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Reorder `validation.md`'s list to match `workflow.md` Step 6's actual sequence exactly — verify against Step 6's current text rather than assuming the order stated in this issue's Required Changes has not since changed. Add only the one exit-condition sentence to `report-template.md`'s Completion Gate; do not alter its 9 existing pass conditions.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115550
- **Related target files**: skills/python-refactoring/validation.md, skills/python-refactoring/report-template.md
