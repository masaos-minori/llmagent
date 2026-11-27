# Reference append_plan_work_items.py in the procedure-generation workflow

## Priority
Medium

## Summary
Make `skills/plan-to-implementation-procedure/workflow.md` Step 4 use the existing `tools/append_plan_work_items.py`, which verifies a procedure pass and writes the `Work Items Created` rows, instead of a hand edit.

## Background
Evidence (`Explicit in code`): `tools/TOOL_DESCRIPTIONS.md` documents `tools/append_plan_work_items.py` (it verifies row coverage, companion eligibility, one target file per document, `Pending` Execution Status, and phase mapping, then writes the rows). A search of `skills/`, `rules/`, `routing.md`, and `prompts/` finds no reference to it, and Step 4 says "Adding these rows is a direct edit". In the 2026-11-27 session the rows were written with a one-off Python script at least six times.

## Problem
An existing, verifying tool is unused, and the workflow instructs an unverified hand edit.

## Reason for Change
Each Plan repeats a hand-written edit and skips the verification the tool performs.

## Implementation Intent
Reference the tool in Step 4 as the preferred path with the hand edit as the fallback, after checking that the tool's checks match Step 4's.

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Read `tools/append_plan_work_items.py` and compare its checks with Step 4's pre-move checklist; record any difference.
- Change Step 4 "Record the generated documents in the Plan" to name the tool as preferred and the direct edit as the fallback when it is unavailable or refuses.
- Add the routing point to the tool row if the table lacks one.

## Constraints
- `skills/plan-to-implementation-procedure/workflow.md` ceiling 34876 B (34635 B on 2026-11-27).
- The tool is not changed in this issue.

## Acceptance Criteria
- [ ] Step 4 names `tools/append_plan_work_items.py` as the preferred way to write the rows.
- [ ] A difference between the tool's checks and Step 4's checklist, if any, is stated.
- [ ] The skill checks pass and the file is within its ceiling.

## Testing Expectations
Run the tool on a scratch copy of one Plan with its procedures and compare with the manual result; `tools/check_skill_size.py`, `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`.

## Documentation Impact
Yes. The workflow step and the tool row.

## Out of Scope
- Changing the tool or Step 4's checklist semantics.

## Dependencies
N/A: none

## Unresolved Questions
- `不明`: whether `tools/append_plan_work_items.py` covers the companion and phase cases exactly as Step 4 requires; the first Required Change answers it.

## AI Implementation Instruction
Do not edit the tool. If its checks differ from Step 4, report the difference instead of choosing one.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120101
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`, `tools/TOOL_DESCRIPTIONS.md`
