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
2. In it, build a child code string (mirroring the neighbouring test's style) that: imports `os`, `runpy`, `subprocess`, `sys`; runs `runpy.run_path('tests/conftest.py', run_name='conftest_probe')` in the child; prints `os.environ['LLMAGENT_TEST_ROOT']`; then defines a grandchild code string that repeats the same two lines under `run_name='grandchild_probe'`, launches it with `subprocess.run([sys.executable, '-I', '-c', gc], env=os.environ, capture_output=True, text=True, timeout=120)` (the grandchild inherits the child's cwd, the repository, so no cwd is passed), and forwards the grandchild's captured stdout with `print(r.stdout.strip())` so the parent observes both printed roots.
3. Launch the child with `[sys.executable, '-I', '-c', code]`, `cwd=repo`, `timeout=120`, `check=False`, capturing output. Build the child environment as `{**os.environ, "PYTEST_XDIST_WORKER": "gw7", "LLMAGENT_TEST_ROOT": str(_root())}`. Crucially, do **not** set `LLMAGENT_TEST_ROOT_OWNER`: it stays at the parent's value (`""` in a serial run, `"gw0"` in a parallel run), which differs from the injected `gw7`. This reproduces REQ-003: the child sees an existing root whose recorded owner is not its own worker id, so `_setup_isolation` builds a fresh root instead of reusing the parent's. The child forwards the grandchild's captured stdout (`print(r.stdout.strip())`) so the parent observes both printed roots; the grandchild inherits the child's cwd (the repository) so no cwd is passed.
4. Assert `result.returncode == 0` (stderr tail as message); split stdout into the child's line and the grandchild's line; assert the child's path differs from the parent's `_root()`, the grandchild's path equals the child's path, both start with `llmagent-test-` (fresh mkdtemp isolation roots), and neither is under `/opt/llm`.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-185322 | 20261113-185322 | Implemented the descendant-reuse test. Three adversarial findings fixed during implementation: (1) child subprocess.run with capture_output swallowed the grandchild stdout so the parent saw one line only -> forward with print(r.stdout.strip()); (2) initial assertions used full-path startswith of llmagent-test- which fails since mkdtemp paths begin with /tmp/ -> use Path name startswith; (3) injected worker id gw7 collides with a real xdist worker on eight-or-more CPU hosts making the test flaky -> use synthetic gw999 xdist never assigns. Verified empirically. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-185322 | 20261113-185322 | Test test_xdist_worker_builds_its_own_root_and_children_reuse_it added after test_conftest_imports_on_host_without_production_db_dir. Passes serial three times and -n auto three times. Full file 21/21 serial and 21/21 parallel. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-185322 | 20261113-185322 | ruff check and ruff format --check pass. mypy success except pre-existing firejail-shim error at conftest.py:356 (untouched, out of scope). Falsifier: removing the owner==worker_id rule makes the child reuse the parent root and the test fails, proving it validates REQ-003 (AC-003). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-185322 | 20261113-185322 | N/A expected: no docs/ change. |

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
