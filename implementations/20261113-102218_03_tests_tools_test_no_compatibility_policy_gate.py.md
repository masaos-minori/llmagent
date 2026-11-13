## Goal
- Mark `TestNoLiveReferences` and `TestCheckerBlocking::test_repo_root_run_passes` with `@pytest.mark.repo_scan` so iteration runs can deselect it, without changing any assertion (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: a class-level decorator on `TestNoLiveReferences` (one test, an in-process scan of the live tree) and a method-level decorator above `def test_repo_root_run_passes` in `TestCheckerBlocking`; leave the other tests of `TestCheckerBlocking` unmarked.
- Not in scope: assertions, other tests of the file, the checkers the tests run.

## Assumptions
- `test_zero_findings_across_live_tree` calls `_scan_flags()` over the live tree (103 s in the 2026-11-13 profile) and `test_repo_root_run_passes` runs `python -m tools.check_compat_shims` at the repository root (90 s); `test_rotation_reject_then_recover` of the same class takes 0.6 s. Falsifier: one of them no longer scans the whole tree.
- `pytest` is already imported in the file, so the decorator needs no new import. The marker is registered by the sibling procedure for `pyproject.toml` (filename order runs it first); without it the decorator only warns because strict markers are off.

## Design decisions
- Apply the marker at the narrowest scope that covers only the scanning tests, so the short tests of the same class still run in iteration.
- Add one comment line saying the marker means a whole-repository scan, deselected from iteration runs.

## Alternatives considered
N/A: a file-level `pytestmark` would also mark short tests and is rejected.

## Implementation
### Target file
`tests/tools/test_no_compatibility_policy_gate.py`

### Procedure
1. Add the decorator as described in Method.
2. Run `uv run pytest --collect-only -q -m repo_scan` and confirm the marked tests of this file appear and no others from it.
3. Run `uv run pytest tests/tools/test_no_compatibility_policy_gate.py -o addopts=""` once (it takes minutes because the scans run) and confirm all pass.

### Method
A class-level decorator on `testnolivereferences` (one test, an in-process scan of the live tree) and a method-level decorator above `def test_repo_root_run_passes` in `testcheckerblocking`; leave the other tests of `testcheckerblocking` unmarked.

### Details
- Do not edit any assertion, fixture, or import.
- A test not listed here is not marked even if it reads the repository; the Plan names only the scans above the 10 s threshold.

## Compatibility considerations
N/A: selection metadata only; the test still runs without a `-m` filter, in the final full run, and in CI.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_no_compatibility_policy_gate.py -o addopts=""`.
- `uv run ruff check tests/tools/test_no_compatibility_policy_gate.py` and `uv run mypy --no-namespace-packages tests/tools/test_no_compatibility_policy_gate.py`.

## Completion criteria
- The listed tests carry the marker, `--collect-only -m repo_scan` selects them, `--collect-only` without `-m` still collects them, and no assertion changed (`AC-002`, `AC-006`).

## Out of Scope
- Speeding up the checkers; marking other tests; skill text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — | Collection checks of the Plan replace a new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A expected: no `docs/` change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002 (apply the marker to the five tests)
- **Source issue**: issues/20261112-183738_testspeed001_mark-repo-scan-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-093307_testspeed001_mark-repo-scan-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102218
- **Related target files**: `tests/tools/test_no_compatibility_policy_gate.py`
