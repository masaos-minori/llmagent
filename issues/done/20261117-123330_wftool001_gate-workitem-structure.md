# Run the work item structure check at commit time and detect template leftovers

## Priority
Medium

## Summary
A new issue, plan, or implementation procedure is never structure-checked by the commit-time gates, and the structure checker cannot detect unfilled template instruction lines. Make the gate run the check on changed work item files and fold the leftover detection into the checker.

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. Claims below were verified in this investigation by reading tool source, running `--help`, and `rg`, unless marked `Needs confirmation`.

## Problem
`tools/run_validation_gates.py` maps `tools/check_workitem_structure.py --file <path>` but reports it `Not available` because the command has a runtime placeholder (`Explicit in code`). The only pre-commit hook for the checker is `--archived-status` on `implementations/done/` (`Explicit in code`, `.pre-commit-config.yaml`). `tools/check_workitem_structure.py` checks section presence only, and `skills/issue-creator/workflow.md` Step 10.4 substitutes a manual shell snippet (`mktemp`, `sed`, `rg`) for leftover detection (`Explicit in code`).

## Reason for Change
- A structurally incomplete or unfilled work item can be committed and pushed: both the gate run and the pre-commit run in the latest issue commit passed without any structure check.
- The skills rely on each author running the check by hand, and the leftover check lives only as prose plus a snippet that an author can skip or mistype.
- The gate already has a changed-file expansion mechanism (`__CHANGED_FILES__`, added for the local ruff gate), so the cost of closing the gap is low now. Nothing makes the change time-sensitive beyond the number of work items filed per week.

## Implementation Intent
- The gate selects the structure check whenever a file under `issues/`, `plans/`, or `implementations/` (excluding `done/`) changed, and runs it over exactly those files.
- The checker detects leftover template instruction lines and unfilled placeholders itself, deriving the instruction lines from the templates so there is one source.
- The skill snippet is replaced by one checker invocation.
- Do not grow `run_validation_gates.py` past the size gate; extract the changed-file expansion or selection logic into a new module if needed.

## Target Files or Areas
- `tools/run_validation_gates.py`
- `tools/check_workitem_structure.py`
- .pre-commit-config.yaml (only if a hook is chosen)
- routing.md (the When to run which tool row)
- skills/issue-creator/workflow.md (Step 10.4)
- `tools/TOOL_DESCRIPTIONS.md`
- `tests/tools/test_check_workitem_structure.py`
- `tests/tools/test_run_validation_gates.py`

## Required Changes
- Let the checker accept several files in one call (or a changed-file list), keeping `--file` behavior.
- Add leftover detection (template instruction lines and `{...}`/`<Issue Title>` placeholders) to the checker, sourced from `templates/issue.md`, `templates/plan.md`, and `templates/implementation-procedure.md`.
- Make the gate run the check on changed work item files, or add a pre-commit hook plus the gate mapping that `run_validation_gates.py drift` requires.
- Replace the Step 10.4 snippet in `skills/issue-creator/workflow.md` with the checker invocation, and update the `routing.md` row.
- Add fixtures: an issue missing a section, an unfilled scaffold, and a filled issue.

## Constraints
- Archived files under `done/` MUST stay excluded by default.
- `run_validation_gates.py` is close to the size gate; verify its size before and after.
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- A staged issue with a missing required section makes the gate report `Fail` (test).
- An unfilled scaffold (template instruction lines present) makes the checker exit `1`, and a filled issue exits `0` (tests).
- `uv run python tools/run_validation_gates.py drift` and `tools/check_module_size.py` (both scopes) pass.
- `skills/issue-creator/workflow.md` Step 10.4 no longer contains the `mktemp` snippet.

## Testing Expectations
Unit tests under `tests/tools/` for the checker and the gate selection; smoke run on the live `issues/` and `plans/` content; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. `routing.md` row, `skills/issue-creator/workflow.md` Step 10.4, and the `tools/TOOL_DESCRIPTIONS.md` entry.

## Out of Scope
- Changing the template content.
- Checking archived work items.
- Content-quality judgment (the checker stays structural).

## Dependencies
- `issues/20261117-123335_wftool006_gate-output-noise.md` follows this issue: it removes the remaining runtime-placeholder noise from the gate output.
- `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling issues of this batch; fix the order with the owner.

## Unresolved Questions
- Hook versus gate-only selection is undecided.
- Whether plan and procedure templates can use the same instruction-line extraction rule as the issue template is `Needs confirmation`.

## AI Implementation Instruction
- Verify `run_validation_gates.py` size first; extract rather than grow it.
- Do not change the templates in this issue.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123330
- **Related target files**: `tools/run_validation_gates.py`; `tools/check_workitem_structure.py`; .pre-commit-config.yaml (only if a hook is chosen); routing.md (the When to run which tool row); skills/issue-creator/workflow.md (Step 10.4); `tools/TOOL_DESCRIPTIONS.md`; `tests/tools/test_check_workitem_structure.py`; `tests/tools/test_run_validation_gates.py`
