# Generate the Requirement Traceability skeleton of a Plan

## Priority
Low

## Summary
Add a tool that prints (or inserts with a flag) the Requirement Traceability rows derivable from a Plan, leaving Status and the evidence wording to the author.

## Background
Evidence (`Explicit in code`, by reading): `templates/requirement-traceability.md` requires one row per Requirement and target file with the implementation step, acceptance criterion, and test column; `tools/amend_plan.py` is the only tool that writes into this table (one row on amendment), and `tools/check_workitem_traceability.py` validates it. Each Plan of 2026-11-27 had 10 to 16 rows written by hand; the values come from the `Requirements`, the target rows' `Related Requirement / Acceptance Criterion` and `Related Tests` cells, and the Implementation steps that cite each file.

## Problem
The mechanical part of a large table is typed by hand in every Plan.

## Reason for Change
Output tokens and typing errors on every Plan; no correctness risk.

## Implementation Intent
A read-only generator like `tools/fill_affected_areas.py`: print rows, insert only with an explicit flag.

## Target Files or Areas
- `tools/generate_requirement_traceability.py` (new)
- `tests/tools/test_generate_requirement_traceability.py` (new)
- `tools/TOOL_DESCRIPTIONS.md`
- `skills/issue-to-plan/workflow.md`

## Required Changes
- Read the Plan's `Implementation Target Files` rows and `Implementation steps`; for each Requirement ID in a row's requirement cell and each file print a row with the file, the phase that cites it, the acceptance criteria and test from the row, and an empty `Status`.
- Define how a range such as `REQ-001`..`REQ-005` is expanded and print what could not be mapped.
- Insert only with a flag and only into `### Requirement Traceability`; `--dry-run` prints the diff.
- Reference the tool in `skills/issue-to-plan/workflow.md` Step 7 within its size ceiling.

## Constraints
- The tool never fills `Status` or the source evidence column.
- `skills/issue-to-plan/workflow.md` stays at or below its ceiling (`tools/check_skill_size_baseline.txt`).

## Acceptance Criteria
- [ ] Rows printed for a past Plan equal its hand-written rows in file, requirement, step, and criterion columns.
- [ ] An unmappable cell is reported, not guessed.
- [ ] The default run writes nothing.

## Testing Expectations
Unit tests on a synthetic Plan; a comparison on two existing Plans; ruff, mypy, bandit; `tools/check_tool_descriptions_sync.py`; `tools/check_skill_size.py`.

## Documentation Impact
Yes. The tool row and the Step 7 reference.

## Out of Scope
- Judging a Requirement's evidence status.

## Dependencies
- Related: issues/20261127-120059_flowopt001_skill-size-fallout-check.md (size headroom of `skills/issue-to-plan/workflow.md`).

## Unresolved Questions
- `不明`: the variants of the requirement cell across Plans (ranges, lists, acceptance-criterion ids); the first Required Change measures them.

## AI Implementation Instruction
Reuse the section parsing of `tools/amend_plan.py` as `tools/fill_affected_areas.py` does. Stop and report if the cells cannot be parsed deterministically.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120107
- **Related target files**: `tools/generate_requirement_traceability.py`, `tests/tools/test_generate_requirement_traceability.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/issue-to-plan/workflow.md`
