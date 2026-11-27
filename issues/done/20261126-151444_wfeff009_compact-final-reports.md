# Define compact final-report formats for the workflow skills

## Priority
Low

## Summary
The workflow skills require a full final report after every cycle, and most of its content repeats what the changed documents and checkers already record. Define a compact chat form that keeps every required fact but states only deviations in detail.

## Background
Evidence (`Explicit in code`, by reading): `skills/code-implementation/workflow.md` "Final Report" (traceability line, a seven-row Execution Status table, questions, next steps, blockers, work items), `skills/plan-to-implementation-procedure/workflow.md` "Final report", `skills/issue-to-plan/workflow.md` Step 9, and `skills/git-commit-and-sync/workflow.md` Phase 9 each list several items to report. The persisted facts already live in the procedure's Execution Status Notes, the Plan, and the commit. Whether any tool parses the chat report is `Needs confirmation`.

## Problem
Long reports add output tokens to every cycle without adding information when nothing deviated.

## Reason for Change
Token cost; no correctness risk. Not urgent.

## Implementation Intent
For each workflow, add a compact form used when no deviation occurred: one status line, one validation line, and a table or list of deviations, warnings, and decisions the user must make. The full form remains for any deviation.

## Target Files or Areas
- `skills/code-implementation/workflow.md`
- `skills/plan-to-implementation-procedure/workflow.md`
- `skills/issue-to-plan/workflow.md`
- `skills/git-commit-and-sync/workflow.md`

## Required Changes
- Define the compact form per workflow and the condition for using it.
- State that every fact still required (traceability values, validation results, unresolved items, pending moves) stays recorded in its persisted place and appears in the report when it is a deviation.
- Check that no tool or skill reads the chat report text (`rg` over `tools/` and `skills/`).

## Constraints
- No required information may be dropped from the persisted records.
- The skill size gate (`tools/check_skill_size.py`) must still pass.

## Acceptance Criteria
- [ ] Each of the four workflows defines the compact form and when it applies.
- [ ] A cycle with a deviation still reports in full.
- [ ] `tools/check_skill_size.py` and `tools/check_skills_references.py` pass.

## Testing Expectations
Run `tools/check_skill_size.py`, `tools/check_skills_references.py`, and `tools/check_skills_heading_cycles.py`; review one past report against the compact form.

## Documentation Impact
Yes. The four workflow files only.

## Out of Scope
- Changing what each workflow verifies or records.

## Dependencies
- N/A: none

## Unresolved Questions
- `不明`: whether any tool reads the final-report text.

## AI Implementation Instruction
Do not remove any item from a persisted record. Stop and report if a tool parses the report.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261126-151444
- **Related target files**: `skills/code-implementation/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/issue-to-plan/workflow.md`, `skills/git-commit-and-sync/workflow.md`
