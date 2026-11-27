# Add output filters to overlap and gate reports

## Priority
Low

## Summary
`tools/check_plan_target_overlaps.py` prints every overlap among all active Plans, and `tools/run_validation_gates.py` prints every passing gate. Add filters so a caller sees only what concerns the current Plan and only failures.

## Background
Evidence (`Explicit in code`): `tools/check_plan_target_overlaps.py` has only a `--format` option (`build_arg_parser`), and each run lists overlaps unrelated to the Plan being processed. `tools/run_validation_gates.py` has `--base`, `--full`, `--jobs`, and `--verbose` and prints one row per gate plus the changed-file list.

## Problem
Each run adds unrelated lines to the working context, and the useful result (a conflict or a failure) is a small part of it.

## Reason for Change
Token cost per run; no correctness risk. Not urgent.

## Implementation Intent
Add opt-in filters and leave the default output and exit codes unchanged.

## Target Files or Areas
- `tools/check_plan_target_overlaps.py`
- `tools/run_validation_gates.py`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Add a repeatable `--plan PATH` option to the overlap checker that keeps only findings naming that Plan.
- Add a failures-only option to the gate runner that prints the changed-file count, every `Fail`, `Blocked`, and `Not available` row, and the final status line.
- Document both options.

## Constraints
- Default output and exit codes are unchanged; the failures-only option must return the same exit code as the full output.

## Acceptance Criteria
- [ ] `--plan` output contains only findings that name the given Plan.
- [ ] The failures-only output omits passing rows and keeps the exit code.
- [ ] Existing tests of both tools still pass.

## Testing Expectations
Unit tests for both options; ruff, mypy, bandit; `tools/check_tool_descriptions_sync.py`.

## Documentation Impact
Yes. `tools/TOOL_DESCRIPTIONS.md`.

## Out of Scope
- Changing what the checkers detect.

## Dependencies
- N/A: none

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
Keep the change to argument handling and rendering. Do not alter detection logic.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261126-151443
- **Related target files**: `tools/check_plan_target_overlaps.py`, `tools/run_validation_gates.py`, `tools/TOOL_DESCRIPTIONS.md`
