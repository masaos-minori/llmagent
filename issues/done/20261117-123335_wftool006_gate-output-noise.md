# Hide runtime-argument gates from the default validation gate output

## Priority
Low

## Summary
`tools/run_validation_gates.py` prints several `Not available` rows on every run for commands that need a runtime argument, which buries the rows that matter. Show them only on request.

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. Claims below were verified in this investigation by reading tool source, running `--help`, and `rg`, unless marked `Needs confirmation`.

## Problem
Commands with a runtime placeholder are reported `Not available` on every run (`Explicit in code`, module docstring). In the latest sync validation, four of fifteen rows were such placeholder rows (`Operationally observed`). `skills/git-commit-and-sync/workflow.md` Phase 4 already tells the reader that only `Fail` and `Blocked` rows matter.

## Reason for Change
- The reader must scan past rows that can never run, and a genuinely unavailable local tool (a skipped check) looks the same as a placeholder row.
- The git workflow compensates with prose instead of the tool distinguishing the two cases.
- The gate runs on every commit and sync, so the noise is paid repeatedly. Severity is low.

## Implementation Intent
- The default output separates runtime-argument rows from rows skipped because a local tool is missing; only the latter stay visible, because they signal a skipped check.
- A flag shows every row.
- Mapping entries, the `drift` subcommand, and the Pass/Fail vocabulary stay unchanged.
- `run_validation_gates.py` is close to the size gate, so the output logic goes into a new module if it needs more than a few lines.

## Target Files or Areas
- `tools/run_validation_gates.py`
- `tests/tools/test_run_validation_gates.py`
- skills/git-commit-and-sync/workflow.md (Phase 4 note)
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Classify `Not available` rows into runtime-argument and missing-tool in the result model.
- Hide runtime-argument rows by default, print one summary line with their count, and add a flag that shows them.
- Update the Phase 4 note in `skills/git-commit-and-sync/workflow.md` and the tool description.

## Constraints
- A missing-tool `Not available` row MUST remain visible, and MUST NOT be reported as `Pass` (`rules/ai-execution.md` item 12).
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- The default output has no runtime-argument rows and prints their count (test).
- The flag prints them, a missing-tool row is still shown by default (tests).
- `uv run python tools/run_validation_gates.py drift` and the module-size gate pass.

## Testing Expectations
Unit tests under `tests/tools/test_run_validation_gates.py`; smoke run on a real diff; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The Phase 4 note in the git workflow and the tool description.

## Out of Scope
- Changing which gates are selected.
- Changing the exit code rules.

## Dependencies
- `issues/20261117-123330_wftool001_gate-workitem-structure.md` should land first, because it removes the structure check from the placeholder rows and also edits the gate.
- `issues/20261117-123333_wftool004_orphan-tool-routing.md` adds routing rows that add placeholder rows.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- Verify the size of `run_validation_gates.py` before editing; extract rather than grow it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123335
- **Related target files**: `tools/run_validation_gates.py`; `tests/tools/test_run_validation_gates.py`; skills/git-commit-and-sync/workflow.md (Phase 4 note); `tools/TOOL_DESCRIPTIONS.md`
