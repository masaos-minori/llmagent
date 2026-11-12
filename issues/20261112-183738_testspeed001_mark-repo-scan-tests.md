# Separate repository-scanning tests from the inner test loop

## Priority
Medium

## Summary
Mark the tests that scan the whole repository (and re-run checkers that already run as pre-commit hooks) with a dedicated pytest marker, and exclude that marker from the inner development loop. The tests keep running in the full suite and in CI. The goal is a shorter edit-test cycle without removing any verification.

## Background
Measured on 2026-11-12 with `uv run pytest -n auto -q -p no:randomly -m "not integration and not production_paths_allowed" --durations=25` (8 cores, 12129 passed, 3m47s wall time). Five tests spend about 158 s of call time in total on whole-repository scans:

- `tests/tools/test_check_compat_shims.py::TestProductionCategoryZero::test_real_repo_manifest_passes` (52.3 s): runs `tools/check_compat_shims.py --check-removed-names --check-doc-symbols` in a subprocess.
- `tests/tools/test_no_compatibility_policy_gate.py::TestNoLiveReferences::test_zero_findings_across_live_tree` (46.2 s) and `TestCheckerBlocking::test_repo_root_run_passes` (31.2 s).
- `tests/tools/test_check_docs_quality.py::TestRegressionFullDocsTree` (15.6 s and 13.6 s).

`.pre-commit-config.yaml` already defines hooks named `check-compat-shims` and `check-docs-quality` for the same checkers, so a developer pays for the same scan in the test loop and again at commit time. The existing inner-loop selection expression used by `skills/code-implementation/workflow.md` Step 4 is `-m "not integration and not production_paths_allowed"`; it has no marker for this kind of test. The earlier issue `issues/done/20261024-203550_perf004_bound-verification-sequence-cost.md` bounded the workflow-side cost of verification but did not address test-side cost.

## Problem
Every inner-loop run of the full non-integration suite pays about 158 s of call time for scans whose result depends on the whole repository, not on the code under change. They dominate the tail of the run and slow every implementation cycle.

## Reason for Change
The development loop is now dominated by test wall time (3m47s even with 8-way parallelism). These five tests are the largest identifiable block that is independent of the change being made. The change is cheap, keeps the checks enforced in CI, and is a prerequisite for measuring other speedups cleanly. Nothing makes it time-critical beyond developer throughput.

## Implementation Intent
Add one marker (working name `repo_scan`) registered next to the existing markers, apply it to the five tests, and extend the documented inner-loop selection expression to exclude it. The full suite, CI, and any run without a `-m` filter keep executing these tests unchanged. Preserve every assertion; do not change the checkers themselves.

## Target Files or Areas
- `pyproject.toml` or `tests/conftest.py` (marker registration; `integration` is registered in `pyproject.toml`, `production_paths_allowed` in `tests/conftest.py::pytest_configure`)
- `tests/tools/test_check_compat_shims.py`
- `tests/tools/test_no_compatibility_policy_gate.py`
- `tests/tools/test_check_docs_quality.py`
- `skills/code-implementation/workflow.md` (Step 4 inner-loop `-m` expression)
- `skills/python-test-and-fix/SKILL.md` (Step 10 impact-based execution, which cites the `-m` expression)

## Required Changes
- Register the new marker with a description stating it covers tests that scan the whole repository.
- Apply the marker to the five tests listed in Background; confirm by `--collect-only` that no other test in `tests/tools/` performs a comparable whole-tree scan, and mark any that do.
- Update the inner-loop `-m` expression in the skill files that cite it.
- Record the before and after inner-loop call time in the issue's Plan or the commit message.

## Constraints
- No test may be deleted, skipped unconditionally, or weakened; only selection changes.
- CI and the full suite must still execute the marked tests (the CI command in `.github/workflows/ci.yml` has no `-m` filter and must keep none).
- `--strict` marker handling, if enabled, must not break (the marker must be registered).

## Acceptance Criteria
- The marker is registered and `uv run pytest --collect-only -q -m repo_scan` lists exactly the intended tests (at least the five above).
- `uv run pytest --collect-only -q -m "not integration and not production_paths_allowed and not repo_scan"` deselects those tests.
- `uv run pytest --collect-only -q` (no `-m`) still collects them.
- The documented inner-loop expression in `skills/code-implementation/workflow.md` and `skills/python-test-and-fix/SKILL.md` includes the exclusion.
- A re-run of the inner-loop command reports call time lower by roughly the 158 s measured above (an estimate: compare against a fresh baseline taken the same way).

## Testing Expectations
- Collection checks listed in Acceptance Criteria.
- `uv run pytest tests/tools/test_check_compat_shims.py tests/tools/test_no_compatibility_policy_gate.py tests/tools/test_check_docs_quality.py` still passes when run explicitly.
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` after the skill edits.
- `uv run mypy` and `uv run ruff check` on the touched test files.

## Documentation Impact
Skill files only (`skills/code-implementation/workflow.md`, `skills/python-test-and-fix/SKILL.md`): the inner-loop selection expression. No `docs/` change is expected; state the operational rule (what the marker means and where it still runs) and nothing about implementation detail.

## Out of Scope
- Speeding up the checkers themselves.
- Changing which checkers run as pre-commit hooks or in CI.
- Parallel execution defaults (separate issue).
- The slow `test_large_string_terminates` test and the subprocess and timeout tests (separate issues).

## Dependencies
N/A: none

## Unresolved Questions
- Whether the pre-commit hooks `check-compat-shims` and `check-docs-quality` pass the same arguments as these tests (`--check-removed-names --check-doc-symbols`): 不明. Not compared. It decides whether the tests are fully redundant with the hooks or only partly.
- Final marker name: assumed `repo_scan`; confirm at planning time.
- Whether other tests in `tests/tools/` belong under the marker: 不明. Only the five above were observed in the top 25 durations.

## AI Implementation Instruction
Change test selection only. Do not edit the checker tools or weaken any assertion. Keep the CI command unchanged. If another whole-repository test is found, list it and mark it only if it is clearly a repo-wide scan; otherwise report it as an open question. Stop and report if the marker would need `--strict-markers` changes.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261112-183738
- **Related target files**: `pyproject.toml`, `tests/conftest.py`, `tests/tools/test_check_compat_shims.py`, `tests/tools/test_no_compatibility_policy_gate.py`, `tests/tools/test_check_docs_quality.py`, `skills/code-implementation/workflow.md`, `skills/python-test-and-fix/SKILL.md`
