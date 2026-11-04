# Define a CLI and exit-code convention for tools/

## Priority
Low

## Summary
Document one convention for tool command lines and exit codes, and bring the tools that lack `--help` or an entry point in line with it.

## Background
Confirmed by repository evidence on 2026-11-04:

- Exit codes in `tools/*.py` are mostly `0` (pass) and `1` (finding), with `2` used in 11 places (for example usage errors); no document states the contract.
- Five tools do not use `argparse`: `check_docs_japanese.py`, `check_dependency_graph_cycles.py`, `check_needs_confirmation_inventory.py`, `check_tool_descriptions_sync.py`, `audit_plan_target_paths.py`; they offer no `--help`.
- `generate_reference_table.py` (1060 lines) has no `main` function; its entry is a module-level `if __name__ == "__main__":` block. `pyproject.toml` console scripts point to `tools.check_docs_consistency:main_*` and similar entries.

## Problem
Callers (hooks, CI, `run_validation_gates.py`, skills) cannot rely on a stated meaning of each exit code, and several tools cannot be discovered or called programmatically in the same way as the rest.

## Reason for Change
Consistency and developer usability; no failure is known. Not time-sensitive.

## Implementation Intent
Write the contract once in `tools/TOOL_DESCRIPTIONS.md` (suggested: `0` = pass, `1` = findings, `2` = usage or environment error), confirm the existing tools already follow it, and fix only the deviations. Give the five tools an `argparse` entry and `generate_reference_table.py` a `main()`.

## Target Files or Areas
- `tools/TOOL_DESCRIPTIONS.md` (convention)
- The five tools above and `tools/generate_reference_table.py`
- Any tool found deviating from the convention during the audit (list: Unknown)

## Required Changes
- Audit every tool's exit codes and record deviations.
- Document the convention and the naming of options common to many tools (for example `--check`, `--json`) only where they already exist.
- Add `argparse` (`--help`) to the five tools and a `main()` to `generate_reference_table.py`, keeping current behavior and exit codes.

## Constraints
- Do not change what any tool checks or when it fails.
- Exit-code changes must be reviewed against every caller in pre-commit, CI, and `run_validation_gates.py` before being made.

## Acceptance Criteria
- The convention is documented and every tool is either compliant or listed with a reason.
- All tools support `--help`; `generate_reference_table.py` exposes `main()`.
- Existing hooks and CI steps behave unchanged.

## Testing Expectations
- Tests that call `--help` and the main exit paths for the changed tools; `uv run pytest tests/tools -q` and the validation gates.

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` with the convention.

## Out of Scope
- Splitting tools or changing tool logic.

## Dependencies
- Shares exit-code constants with `issues/20261104-152002_toolcommon001_shared-helper-for-tools.md`; the convention should be decided first.

## Unresolved Questions
- Whether any caller depends on a non-standard exit code: unknown (audit needed).

## AI Implementation Instruction
Audit first and report deviations before changing any tool; keep behavior identical.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-152002
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`, `tools/check_docs_japanese.py`, `tools/check_dependency_graph_cycles.py`, `tools/check_needs_confirmation_inventory.py`, `tools/check_tool_descriptions_sync.py`, `tools/audit_plan_target_paths.py`, `tools/generate_reference_table.py`
