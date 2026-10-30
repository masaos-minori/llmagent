# Amend a Frozen Plan with one tool and a defined approval rule

## Priority
Medium

## Summary
Add a tool that appends a target file to a Frozen Plan consistently (table row, freeze note, traceability row, related-files line, step text, work-item row) and re-runs the Plan checks, and define in `rules/workflow-lifecycle.md` which amendments the executor may make and report afterwards and which need approval first.

## Background
- `Operationally observed` (2026-10-30): the three Plans were amended six times after freeze (a path correction and a table-ownership inventory row for `dbmig001`; the workflow registry row and a deploy-test row for `wftaskapi001`; the registry row and an orchestrator integration-test row for `wfrecovery001`). Each amendment was a hand-written script that edited about seven places in the Plan.
- `Operationally observed`: one of those scripts replaced a path at the first occurrence in the file; that occurrence was in an unrelated table row, and the error was found by reading the diff, not by a check.
- `Explicit in code`: `rules/workflow-lifecycle.md` (Implementation Target Files Validation) requires that after an additional target file discovery the Plan is amended with the new row appended after the last row, with evidence and a requirement link, and re-validated; `skills/plan-to-implementation-procedure/workflow.md` Step 3c and `skills/code-implementation/workflow.md` end the cycle `Blocked` until then. No tool performs the amendment: `tools/check_workitem_structure.py` checks structure and `tools/audit_plan_target_paths.py` checks that target paths exist.
- `Operationally observed`: four of the six amendments (the two registry rows, the inventory row, and the deploy-test row) were approved by the user before they were made, each costing a question and a wait; the other two (the path correction under `skills/plan-to-implementation-procedure/workflow.md` Step 3a and the integration-test row) were made and reported afterward. None changed the Plan's behavior or scope; they only listed files that had to change to keep existing checks and tests green.
- Related closed work: `issues/done/20261024-203645_perf005_cut-blocking-question-waits.md` (reduced question waits in `code-implementation`; amendments were not in its scope).

## Problem
An amendment touches many places by hand, with no check that it was applied consistently and no rule for which amendments need a decision. The result is slow, error-prone, and either asks a question each time or leaves the executor to guess whether one is needed.

## Reason for Change
Additional target discoveries are a known recurring event (see `issues/20261030-191006_flowimp001_consumer-impact-scan.md` for the prevention side). Until prevention is complete, the remedy should be cheap, uniform, and checkable.

## Implementation Intent
Separate the mechanical part from the decision part. The tool does the mechanics: given the Plan, the new file, its responsibility and reason, the linked requirement, the evidence, and the related tests, it appends the row after the last existing row, extends the freeze note with the date and the reason, adds the traceability row and the related-files entry, appends or extends the step text, adds the work-item row for the new procedure, and then runs the structure, path-audit, and overlap checks, printing their results. A dry run prints the edits first. The decision part is a rule: an amendment that only adds a file needed to keep existing behavior, tests, inventories, or checkers working (fallout) may be made by the executor and reported afterward; an amendment that changes scope or behavior, adds a requirement, or removes a row needs approval before it is made.

## Target Files or Areas
- `tools/amend_plan.py` (new) and `tests/tools/test_amend_plan.py` (new)
- `rules/workflow-lifecycle.md` (the amendment procedure and the approval classes)
- `skills/plan-to-implementation-procedure/workflow.md` (Step 3c additional discovery) and `skills/code-implementation/workflow.md` (the stop rule)
- `tools/TOOL_DESCRIPTIONS.md` and `routing.md`

## Required Changes
- Implement the tool with a dry run, an append-only guarantee for the table (never insert before the last row), and a refusal when the file is already a target or a reference file.
- Record each amendment as a dated line in the Plan so the history is visible.
- Write the approval classes into `rules/workflow-lifecycle.md` with a short definition of "fallout" and the report the executor owes afterward.
- Update the two skills to call the tool and to follow the classes.

## Constraints
- The owner decides the policy; the tool must work under either answer (it does not decide the class itself, the caller states it).
- Plan Freeze validation rules stay as written: the new row must pass the same four checks before the section is `Frozen` again.
- The tool edits only the named Plan and never a source file or another Plan.

## Acceptance Criteria
- On a fixture Plan, a dry run prints all intended edits and changes nothing; a real run applies them, and the structure, path-audit, and overlap checks run and their results are printed.
- Adding a file that is already a target, or a reference file, is refused with the reason.
- A fixture Plan with a similar path appearing earlier in the file is edited in the intended row only.
- `rules/workflow-lifecycle.md` states the two approval classes and the report owed for the first class.
- `check_skills_references.py`, `check_skills_heading_cycles.py`, and `check_tool_descriptions_sync.py` pass.

## Testing Expectations
- Unit tests for each edit location, the append-only rule, the refusals, and the repeated-path case.
- A dry run against copies of the three amended Plans (reconstructing the amendment from their before state) compared with the hand-made result.
- `ruff`, `mypy <tool path>`, and `bandit` per "Adding a new tool".

## Documentation Impact
Yes. `rules/workflow-lifecycle.md` and the two skills state the amendment procedure and the approval classes. Intent and failure behavior only.

## Out of Scope
- Preventing the discoveries (`issues/20261030-191006_flowimp001_consumer-impact-scan.md`).
- Removing or reordering rows, or changing requirements through the tool.
- Generating the new row's procedure document.

## Dependencies
Sequencing only, in either order, with `issues/20261030-191057_flowimp002_plan-release-units.md`, `issues/20261030-191144_flowimp003_plan-dependency-gate.md`, and `issues/20261030-191615_flowimp009_test-row-grouping.md`: they share `skills/plan-to-implementation-procedure/workflow.md` and `skills/code-implementation/workflow.md`; whichever lands later rebases. No other open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30).

## Unresolved Questions
- `不明`: whether the owner accepts executor-made "fallout" amendments with an after-the-fact report; the tool does not depend on the answer.
- `不明`: whether the amendment log belongs in the freeze note or in a dedicated Plan section (which would touch `templates/plan.md` and `check_workitem_structure.py`).
- Assumption: the six amendments of 2026-10-30 are representative of the common case.

## AI Implementation Instruction
Implement the tool and the rule text only. Keep the owner's approval decision open: write both classes as proposed text and mark the policy as pending the owner's decision. Never edit a Plan outside tests. Stop and report if a Plan's structure prevents an unambiguous append.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191737
- **Related target files**: `tools/amend_plan.py`, `tests/tools/test_amend_plan.py`, `rules/workflow-lifecycle.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `tools/TOOL_DESCRIPTIONS.md`, `routing.md`
