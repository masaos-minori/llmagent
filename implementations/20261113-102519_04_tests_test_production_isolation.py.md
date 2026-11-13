## Goal
- Add a test proving that a process running as an xdist worker builds its own isolation root while a process it spawns reuses it (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new test at the end of the root-handling tests of the file.
- Not in scope: existing tests, the conftest change (sibling procedure, filename order runs it first).

## Assumptions
- The file already proves conftest behavior in a fresh interpreter (`test_conftest_imports_on_host_without_production_db_dir` runs `runpy.run_path('tests/conftest.py', ...)` under `-I`). The new test uses the same pattern.
- A root a child builds is removed by that child's `atexit` handler, so the child must start its grandchild before it exits; a sequence of two separate children would see the first root already deleted.
- The sibling procedure for `tests/conftest.py` introduces the owner variable `LLMAGENT_TEST_ROOT_OWNER`; the test sets only PYTEST_XDIST_WORKER and `LLMAGENT_TEST_ROOT`, as an inherited environment would.

## Design decisions
- One test, named `test_xdist_worker_builds_its_own_root_and_children_reuse_it` (new), parameter-free.
- Assert on directory paths printed by the children, not on file contents.

## Alternatives considered
N/A: a test that runs under real xdist would only be meaningful in parallel runs; a fresh-interpreter test works in both modes.

## Implementation
### Target file
`tests/test_production_isolation.py`

### Procedure
1. Add the test after `test_conftest_imports_on_host_without_production_db_dir`.
2. In it, run a child with `sys.executable -I -c` and `cwd` set to the repository, with an environment that sets PYTEST_XDIST_WORKER to `gw7` and `LLMAGENT_TEST_ROOT` to the current process's isolation root (the test already has the module `tests/conftest.py` available as `tests.conftest`).
3. The child runs `runpy.run_path('tests/conftest.py', run_name='conftest_probe')`, prints `os.environ['LLMAGENT_TEST_ROOT']`, then runs a grandchild with the same code and `env=os.environ` that prints it again, and exits after the grandchild finished.
4. Assert that the first printed path differs from the parent's root, that the second equals the first, and that both lie under the temporary directory, not under `/opt/llm`.
5. Run `uv run pytest tests/test_production_isolation.py -o addopts=""` serially and with `-n auto`.

### Method
Reuse the file's imports (`subprocess`, `sys`, `Path`); build the child code as a string like the neighbouring test. Keep the timeout and `check=False` style and assert `returncode == 0` with the stderr tail as the message.

### Details
- The test must pass in a serial and a parallel run.
- Do not edit existing tests.

## Compatibility considerations
N/A: test-only addition.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/test_production_isolation.py -o addopts=""` serially and with `-n auto`, repeated.
- `uv run ruff check tests/test_production_isolation.py` and `uv run mypy --no-namespace-packages tests/test_production_isolation.py`.

## Completion criteria
- The new test passes in a serial and a parallel run and fails if the owner rule is removed (`AC-003`).

## Out of Scope
- The conftest change itself and other isolation tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
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
- **Requirement ID**: REQ-003 (prove the per-worker rule)
- **Source issue**: issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-093804_testspeed004_adopt-parallel-test-execution.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102519
- **Related target files**: `tests/test_production_isolation.py`
