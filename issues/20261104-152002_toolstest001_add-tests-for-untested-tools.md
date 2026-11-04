# Add tests for module_nodes, run_refactor_validation, and audit_plan_target_paths

## Priority
Medium

## Summary
Add unit tests for the three untested workflow tools whose mistakes cost the most: `module_nodes.py`, `run_refactor_validation.py`, and `audit_plan_target_paths.py`.

## Background
Confirmed by repository evidence on 2026-11-04: no file under `tests/` references `module_nodes`, `run_refactor_validation`, or `audit_plan_target_paths` (searched by module name and import). Other untested tools exist (`fix_docs_section_marks.py`, `fix_docstring_blank_line.py`, `fix_procedure_new_markers.py`, `generate_mcp_inventory.py`, `migrate_runtime_tool_calls.py`), and `check_skills_references.py` is covered only indirectly through `tests/tools/test_run_validation_gates.py`; they are not in this issue's scope.

- `module_nodes.py` moves exact source ranges between files for Path C module splits (`extract`, `measure`, and a verify subcommand): an error corrupts source.
- `run_refactor_validation.py` runs the per-file refactor gate described in `rules/toolchain.md`.
- `audit_plan_target_paths.py` is invoked by `amend_plan.py` (`tools/amend_plan.py` runs it by path) to audit target paths in plans.

## Problem
Tools that rewrite source or decide whether a refactor passes have no regression tests, so behavior changes (including the shared-helper and size-gate work filed alongside this issue) cannot be checked.

## Reason for Change
Test gap on tools that modify or gate source. This should land before the refactors in the dependent issues.

## Implementation Intent
Cover the main behavior and the failure paths of each tool with tests that use temporary directories and fixed inputs, without running the real toolchain or touching the repository.

## Target Files or Areas
- `tools/module_nodes.py`, `tools/run_refactor_validation.py`, `tools/audit_plan_target_paths.py`
- New files under `tests/tools/` (names follow `test_<module>.py`)

## Required Changes
- `module_nodes`: tests for `measure` (line span and byte size per top-level node), `extract` (exact range moved, source and destination consistent), and the verification step on a mismatch.
- `run_refactor_validation`: tests of the command construction and result aggregation with the subprocess calls faked; include a failing step and an all-pass case.
- `audit_plan_target_paths`: tests for a missing path, a cross-plan overlap, and a path referenced in a plan body but not covered by a target row, using temporary plan files.

## Constraints
- Do not change tool behavior; if a test exposes a defect, record it as a separate issue.
- Tests must not run ruff, mypy, or pytest of the real repository and must not write outside the temp directory.

## Acceptance Criteria
- Each of the three tools has a test file that fails when the tool's main behavior is broken.
- Each tool has at least one negative-path test.
- `uv run pytest tests/tools -q` passes.

## Testing Expectations
- New unit tests only; run `uv run pytest tests/tools -q`, ruff, and mypy per `rules/toolchain.md`.

## Documentation Impact
Not required.

## Out of Scope
- Tests for the other untested tools listed in Background.
- Refactoring the three tools.

## Dependencies
- This issue should land before `issues/20261104-152002_toolcommon001_shared-helper-for-tools.md` and `issues/20261104-152002_toolsizegate001_apply-size-gate-to-tools.md`, which may touch these files.

## Unresolved Questions
- Whether the byte-size calculation of `module_nodes measure` is specified anywhere other than its docstring: unknown.

## AI Implementation Instruction
Write tests against observable behavior and temporary fixtures; keep the production files unchanged.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-152002
- **Related target files**: `tools/module_nodes.py`, `tools/run_refactor_validation.py`, `tools/audit_plan_target_paths.py`
