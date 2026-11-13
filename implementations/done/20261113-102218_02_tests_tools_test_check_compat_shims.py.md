## Goal
- Mark `TestProductionCategoryZero::test_real_repo_manifest_passes` with `@pytest.mark.repo_scan` so iteration runs can deselect it, without changing any assertion (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: a method-level decorator above `def test_real_repo_manifest_passes` in `TestProductionCategoryZero`.
- Not in scope: assertions, other tests of the file, the checkers the tests run.

## Assumptions
- The test runs `tools/check_compat_shims.py --check-removed-names --check-doc-symbols` over the real repository in a subprocess (100 s in the 2026-11-13 profile, 52 s on 2026-11-12). Falsifier: the test no longer scans the repository.
- `pytest` is already imported in the file, so the decorator needs no new import. The marker is registered by the sibling procedure for `pyproject.toml` (filename order runs it first); without it the decorator only warns because strict markers are off.
- Overlap judged compatible (Plan Step 2): `plans/20261112-122408_rmcompat008_compat-checker-patterns.md` also targets this file, adding pattern, scope, and marker-set tests and moving three fixtures in other regions; this procedure adds one decorator. Implement either first; re-read the file before editing.

## Design decisions
- Apply the marker at the narrowest scope that covers only the scanning tests, so the short tests of the same class still run in iteration.
- Add one comment line saying the marker means a whole-repository scan, deselected from iteration runs.

## Alternatives considered
N/A: a file-level `pytestmark` would also mark short tests and is rejected.

## Implementation
### Target file
`tests/tools/test_check_compat_shims.py`

### Procedure
1. Add the decorator as described in Method.
2. Run `uv run pytest --collect-only -q -m repo_scan` and confirm the marked tests of this file appear and no others from it.
3. Run `uv run pytest tests/tools/test_check_compat_shims.py -o addopts=""` once (it takes minutes because the scans run) and confirm all pass.

### Method
A method-level decorator above `def test_real_repo_manifest_passes` in `testproductioncategoryzero`.

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
- `uv run pytest tests/tools/test_check_compat_shims.py -o addopts=""`.
- `uv run ruff check tests/tools/test_check_compat_shims.py` and `uv run mypy --no-namespace-packages tests/tools/test_check_compat_shims.py`.

## Completion criteria
- The listed tests carry the marker, `--collect-only -m repo_scan` selects them, `--collect-only` without `-m` still collects them, and no assertion changed (`AC-002`, `AC-006`).

## Out of Scope
- Speeding up the checkers; marking other tests; skill text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-124614 | 20261113-125513 | Changed tests/tools/test_check_compat_shims.py: @pytest.mark.repo_scan (with a one-line comment) above TestProductionCategoryZero::test_real_repo_manifest_passes only; no assertion, fixture, or import changed. The overlap with plan rmcompat008 on this file was judged compatible; that plan was not yet implemented. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-125513 | 20261113-125513 | Collection: -m repo_scan selects the test; the iteration expression deselects it; a run without -m still collects it. File run explicitly: 149 passed (the scan takes 31 s). ruff and mypy clean. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-125513 | 20261113-125513 | Full suite serial 12151 passed, 3 failed: the known mdq cases (unrelated, Plan testspeed004). diff-cover N/A: no source file changed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-125513 | 20261113-125513 | N/A: no docs/00_index.md task-scope mapping for tests/tools/test_check_compat_shims.py |

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
- **Related target files**: `tests/tools/test_check_compat_shims.py`
