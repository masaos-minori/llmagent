# Run the CI test suite once instead of twice

## Priority
Medium

## Summary
The CI workflow runs the whole pytest suite twice on every push to master and every pull request to master: once as `uv run pytest -v` and again as `uv run coverage run -m pytest tests/`. Fold the two into a single coverage-collecting run, so CI test time is roughly halved while the coverage gate and failure reporting stay intact.

## Background
- `.github/workflows/ci.yml` (triggered on `push` and `pull_request`) has the step "Run tests" with `run: uv run pytest -v`, followed by the step "Coverage report" with `uv run coverage run -m pytest tests/`, `uv run coverage xml`, and `uv run diff-cover coverage.xml --compare-branch=origin/master --fail-under=90`. Both pytest invocations select the whole `tests/` tree.
- The same suite was measured on 2026-11-12 at 12129 passed in 3m47s wall time with 8-way parallelism (9m25s CPU time). The serial time and the CI runner's time were not measured, so the saving in CI minutes is not quantified here.
- `pytest-randomly` is a dev dependency, so the two runs use different random orders unless a seed is passed; whether that was intended is not recorded anywhere that was checked.
- `[tool.coverage.run]` in `pyproject.toml` sets `source` and `omit` and has no `parallel` or `concurrency` setting. The local Step 4 of `skills/code-implementation/workflow.md` already feeds the coverage gate from one `coverage run -m pytest tests/` run so that the suite runs once.
- The CI run results themselves were not checked (the `gh` tool is not authenticated on this machine, according to `rules/toolchain.md`).

## Problem
Each CI run pays the full test cost twice for no additional verification: the second run executes the same tests and only adds coverage data, and a failure in either one fails the job.

## Reason for Change
Test time is the largest part of the development loop, and CI feedback is part of that loop. Removing the duplicate run is a small workflow-file change that does not alter what is checked. It also leaves one place to add `-n auto` later.

## Implementation Intent
Keep one test step that runs the suite under `coverage run`, then the existing `coverage xml` and `diff-cover` steps unchanged. Keep failure output sufficient for diagnosis. Do not change the selection (no `-m` filter), the coverage gate threshold, or the compare branch.

## Target Files or Areas
- `.github/workflows/ci.yml` (test and coverage steps)
- `tox.ini` (`tests` environment runs `uv run pytest {posargs}`; check whether it needs the same treatment)

## Required Changes
- Replace the two steps with a single step that runs `uv run coverage run -m pytest tests/` (keeping whichever verbosity flags are needed for CI diagnosis), followed by `coverage xml` and `diff-cover` as today.
- Confirm that a failing test still fails the job and that the `diff-cover` gate still runs and enforces 90%.
- State in the change record what the second run was for, if anything.

## Constraints
- All tests that run today must still run in CI (no `-m` filter added).
- The 90% diff-cover gate and the `origin/master` compare branch stay as they are.
- Do not introduce parallel workers in this change (that belongs to the parallel-execution issue); if workers are added later, coverage needs a parallel-mode setting.

## Acceptance Criteria
- `.github/workflows/ci.yml` invokes pytest on the `tests/` tree exactly once per job run.
- A pull request with a deliberately failing test fails the job (verify once on a throwaway change or by reading the exit code of `coverage run` locally).
- `diff-cover` still runs after the test step and still uses `--fail-under=90`.
- CI duration for the test portion is recorded before and after the change.

## Testing Expectations
- Run the combined command locally: `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` and compare the pass/fail result with a plain `uv run pytest`.
- Validate the workflow file syntax (for example `actionlint` if available; otherwise review by reading and one CI run).
- `uv run python tools/check_tool_descriptions_sync.py` is not needed unless a tool is touched; none is expected.

## Documentation Impact
None expected. If `rules/toolchain.md` section 7 describes the CI steps, keep it consistent; it currently shows the same local command sequence.

## Out of Scope
- Adding `-n auto` or other parallel execution to CI.
- Changing the CI trigger set, runners, caching, or the lint job.
- Changing the `diff-cover` threshold.
- Test-level speedups (separate issues).

## Dependencies
- `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md`: related; if parallel workers are adopted there, a follow-up must add coverage parallel settings to CI. Not blocking this issue.

## Unresolved Questions
- Whether the first run (`pytest -v`) was kept intentionally, for example as a second random-order run or for the verbose log: 不明. No record was found in the files read.
- CI wall time for the test steps: 不明. Not available without CI access.
- Whether `-v` output is needed for diagnosis in CI: 不明; default is to keep a short failure summary (`--tb=short` is already in `addopts`).

## AI Implementation Instruction
Change only the test and coverage steps of the workflow. Do not touch other jobs or steps. Keep the gate commands identical. If you find a reason the duplicate run was intentional, stop and report it instead of removing it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261112-183953
- **Related target files**: `.github/workflows/ci.yml`, `tox.ini`
