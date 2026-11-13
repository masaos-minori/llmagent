## Goal
- Make parallel execution (`-n auto`) the documented standard for local full-suite runs without weakening the `/opt/llm` isolation or the coverage gate: first clear the three known failing tests, then make the isolation root per worker, then show with three random-order parallel runs that the suite is green, then document the default, the opt-out, and the serial exceptions identically in `rules/toolchain.md`, `skills/python-test-and-fix/workflow.md`, and `skills/code-implementation/workflow.md`.

## Priority
Medium

## Scope
- **In-Scope**: fix the three mdq tests by giving their subprocess the test isolation environment; give each xdist worker its own isolation root in `tests/conftest.py` and prove it with a test; record the serial baseline and the parallel results; run three consecutive random-order parallel runs and report any failure with its cause and owner; document the default, the opt-out, and the serial exceptions in the three files above.
- **Out-of-Scope**: changing `.github/workflows/ci.yml` (see `issues/20261112-183953_testspeed005_run-ci-suite-once.md`, whose Plan keeps CI serial); reducing individual test durations; changing which tests are selected by markers; `pytest-testmon` state maintenance; adding a parallel-mode coverage setup; changing production databases; fixing other subprocess tests that build a minimal environment (reported, not fixed).
- **Dependencies**: related, not blocking, and sequencing only: `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md` (its Plan `plans/20261113-093307_testspeed001_mark-repo-scan-tests.md` edits one command line in `skills/python-test-and-fix/workflow.md` Step 10 and `skills/code-implementation/workflow.md` Step 4, the same sections this Plan edits; implement it first and re-read those sections before Phase 4) and `issues/20261112-183849_testspeed003_cut-timeout-test-waits.md` (its Plan `plans/20261113-092136_testspeed003_cut-timeout-test-waits.md` removes the longest single tests, which raises the benefit of parallel execution).

## Background
Measured on 2026-11-12 with `uv run pytest -n auto -q -p no:randomly -m "not integration and not production_paths_allowed" --durations=25 -o addopts=""` on 8 cores: 3 failed, 12129 passed, 7 skipped, 226.87 s wall time and 9m25s of CPU time; the serial wall time was not measured. `pyproject.toml` has `addopts = "-v --tb=short"` with no `-n`, and `pytest-xdist`, `pytest-randomly`, `pytest-timeout`, and `pytest-testmon` are dev dependencies. `skills/python-test-and-fix/workflow.md` says `pytest-xdist` is only to be used after confirming the isolation guard is safe under multiple workers. Verified on 2026-11-13:
- The three failures (`tests/mcp_servers/test_config_isolation_import.py` two mdq cases and `tests/mcp_servers/test_require_auth_token.py` one mdq case) fail serially too. Their subprocess helpers build a minimal environment (`PATH`, `HOME`, token variables, `PYTHONPATH`, `LLMAGENT_LOG_DIR`) with no `LLMAGENT_CONFIG_DIR`, so the child reads the repository `config/mdq_mcp_server.toml`, whose `db_path` is the production `/opt/llm/db/mdq.sqlite` of this host. That file holds a table `chunk_summaries` the canonical schema does not define, and `shared/schema_fingerprint.py` raises before the expected auth message. CI is unlikely to show it (its `/opt/llm/db` is absent).
- `tests/conftest.py::_setup_isolation` builds the temporary isolation root "once per process tree" and reuses `LLMAGENT_TEST_ROOT` when it is set. A probe with `-n 2` showed both workers (`gw0`, `gw1`) using the same root, so the isolated `session`, `rag`, `workflow`, and `eventbus` SQLite files, the logs, and the storage directory are shared between concurrently running tests.
- `coverage run -m pytest -n 2` reports 0% for a module executed only in the workers (90% in the serial run), with exit status 0, so coverage runs must stay serial.

## Problem
Full-suite runs use one core on an 8-core machine, and the suite has a known-red baseline of three tests, so a developer cannot tell a new regression from an existing failure. The decision on parallel execution is blocked on two unverified claims that turn out to hold only in part: the three failures come from a test-isolation gap (a subprocess reaching a production database path), and the isolation root is shared across workers.

## Reason for Change
Test wall time dominates the implementation loop, and parallel execution is the cheapest lever that does not change what a test asserts. A clean baseline and a safe isolation model are the preconditions.

## Implementation Intent
Work in this order: (1) fix the three failures through the existing `isolated_subprocess_env` fixture and take the serial baseline; (2) make the isolation root per worker without changing serial behavior, and prove it; (3) run the parallel suite three times with random ordering and report; (4) document the default (a documented command, not an `addopts` entry), the opt-out, and the serial exceptions. Keep serial execution as the recommended mode for flaky investigation, mutation runs, and coverage runs.

## Requirements
- `REQ-001`: Record the serial baseline and the parallel result for the same selection expression (`-m "not integration and not production_paths_allowed"`, `-p no:randomly`) on the same machine, with the speedup factor.
- `REQ-002`: Make the three mdq tests pass by building their subprocess environment from the isolation variables (the shared `isolated_subprocess_env` fixture), not by skipping or weakening them, and state the cause in the change record, naming the production database path; the production database is not modified.
- `REQ-003`: Give each xdist worker its own isolation root, so concurrently running tests never share the isolated databases, logs, or storage; processes spawned by a worker keep reusing that worker's root; serial runs behave as today; the per-test guard and the session fingerprint fixture stay as they are; `tools/check_conftest_integrity.py` passes; a test proves the per-worker rule.
- `REQ-004`: Run the full non-integration suite in parallel with random ordering three consecutive times and compare; the result is zero failures, or each remaining failure is listed with its cause and an owner; an order-dependent test is reported, not rewritten silently.
- `REQ-005`: Document the default and its opt-out identically in `rules/toolchain.md`, `skills/python-test-and-fix/workflow.md`, and `skills/code-implementation/workflow.md`: full-suite runs use `-n auto`; serial (`-n 0` or no `-n`) stays the mode for flaky investigation, mutation runs, and coverage runs, with the reason for the coverage exception; `pytest-xdist` guidance in the tool table of `skills/python-test-and-fix/workflow.md` states that the isolation guard was confirmed safe under workers.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/mcp_servers/test_config_isolation_import.py | Fresh-interpreter import checks of the MCP servers | `_run` builds the child environment by hand without `LLMAGENT_CONFIG_DIR`; build it from the isolation variables (REQ-002) | REQ-002 / AC-002 | `_run` copies only `PATH` and `HOME`, adds token variables, `PYTHONPATH`, and `LLMAGENT_LOG_DIR`; the two mdq cases fail with a schema-fingerprint error about `/opt/llm/db/mdq.sqlite` (checked in Step 2 and Step 3) | tests/mcp_servers/test_config_isolation_import.py | Verified |
| tests/mcp_servers/test_require_auth_token.py | Empty-token import checks of every MCP server | `_import_in_fresh_interpreter` builds the child environment the same way; build it from the isolation variables (REQ-002) | REQ-002 / AC-002 | The helper copies only `PATH` and `HOME`; `test_empty_token_prevents_every_server_from_importing[...mdq...]` fails because stderr holds the fingerprint error instead of `auth_token is empty` (checked in Step 2 and Step 3) | tests/mcp_servers/test_require_auth_token.py | Verified |
| tests/conftest.py | Test isolation: root, guard fixtures, session fingerprint | `_setup_isolation` reuses an inherited `LLMAGENT_TEST_ROOT`, so every xdist worker shares one root; create a root per worker (REQ-003) | REQ-003 / AC-003 | `_setup_isolation` reuses `LLMAGENT_TEST_ROOT` when it exists; the `-n 2` probe printed one root for `gw0` and `gw1`; the required autouse fixtures are listed in `tools/check_conftest_integrity.py` (checked in Step 2 and Step 3) | tests/test_production_isolation.py | Verified |
| tests/test_production_isolation.py | Tests of the isolation mechanism | Add a test that a process running as an xdist worker builds its own root while a descendant of the same worker reuses it, using the fresh-interpreter pattern the file already has (REQ-003) | REQ-003 / AC-003 | The file already imports `tests/conftest.py` in a subprocess (`test_conftest_imports_on_host_without_production_db_dir`) and tests `_cleanup_isolated_root` (checked in Step 3) | tests/test_production_isolation.py | Verified |
| rules/toolchain.md | Shared validation sequence | State the parallel default, the opt-out, and the serial exceptions in sections 6 and 7 (REQ-005) | REQ-005 / AC-005 | Section 6 lists `uv run pytest -v` for the full suite and section 7 lists `coverage run -m pytest tests/`; neither mentions `-n` (checked in Step 3) | N/A: rule text; validated by `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` | Verified |
| skills/python-test-and-fix/workflow.md | Test-and-fix procedure | Update the `pytest-xdist` tool-table row and the Step 10 full-run command, and keep serial for flaky, mutation, and coverage runs (REQ-005) | REQ-005 / AC-005 | The `pytest-xdist` row says it is not part of the default run and only after confirming the isolation guard under workers; Step 10 gives the full run without `-n`; Step 11 gives the coverage run (checked in Step 3) | N/A: skill text; validated by the two skill checkers | Verified |
| skills/code-implementation/workflow.md | Code-implementation procedure | Update the Step 4 full-suite wording and keep the coverage run serial (REQ-005) | REQ-005 / AC-005 | Step 4 runs the "repository-defined full test suite" once and feeds the coverage gate through `coverage run -m pytest tests/` (checked in Step 3) | N/A: skill text; validated by the two skill checkers | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| pyproject.toml | `addopts` has no `-n` and stays so; `[tool.coverage.run]` has no `parallel` setting, which is why coverage stays serial | skills/python-test-and-fix/workflow.md / REQ-005 |
| tools/check_conftest_integrity.py | Lists the required autouse fixtures that must survive the conftest change | tests/conftest.py / REQ-003 |
| tests/mcp_servers/test_mcp_launcher.py | Builds its child environment the same way (`PATH` and `HOME` only); same gap, reported not fixed | tests/mcp_servers/test_require_auth_token.py / REQ-002 |
| config/mdq_mcp_server.toml | Holds the mdq `db_path` that points at the production database path | tests/mcp_servers/test_config_isolation_import.py / REQ-002 |
| .github/workflows/ci.yml | CI stays serial and unchanged here; its `Coverage report` step depends on serial coverage | rules/toolchain.md / REQ-005 |

## Acceptance Criteria
- `AC-001` (REQ-001): The change record lists the serial and the parallel wall time for the same selection, machine, and `-p no:randomly`, and the speedup factor.
- `AC-002` (REQ-002): The three mdq tests pass; the change record names `/opt/llm/db/mdq.sqlite` and the `chunk_summaries` table as the cause; no test is skipped or weakened; the production database files are unchanged (the session fingerprint check passes).
- `AC-003` (REQ-003): Under `-n 2` the workers use different roots, a descendant process of a worker reuses its worker's root, a serial run uses one root as today, the new test passes in a serial and a parallel run, `uv run python tools/check_conftest_integrity.py` passes, `tests/test_production_isolation.py` passes under `-n auto`, and no `llmagent-test-*` directory remains in the temporary directory after a run that exits normally.
- `AC-004` (REQ-004): Three consecutive `-n auto` runs with `pytest-randomly` enabled report zero failures, or every remaining failure is listed with cause and owner; the seeds are recorded.
- `AC-005` (REQ-005): The default, the opt-out, and the serial exceptions read the same in `rules/toolchain.md`, `skills/python-test-and-fix/workflow.md`, and `skills/code-implementation/workflow.md`; `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` pass.

## Tests
- The three mdq tests, serially and in parallel (REQ-002).
- A new test in `tests/test_production_isolation.py` for the per-worker root and descendant reuse (REQ-003).
- The existing isolation tests of `tests/test_production_isolation.py` under `-n auto` (REQ-003).
- The full non-integration suite: serial with `-p no:randomly` (baseline), parallel with `-p no:randomly`, and three parallel runs with random ordering (REQ-001, REQ-004).

## Documentation Impact
N/A: no `docs/` change. The operational commands and the xdist usage rule are in `rules/toolchain.md`, `skills/python-test-and-fix/workflow.md`, and `skills/code-implementation/workflow.md` (REQ-005); they state intent and the isolation and coverage constraints, and no configuration value beyond the command lines.

## Assumptions
- Giving the three mdq tests the isolation environment makes their child read the isolated root config, whose rewritten `db_path` is inside the root; falsifier: a child still opens `/opt/llm/db/mdq.sqlite` (the session fingerprint check would then report a change or the schema error persists).
- A per-worker root is the lower-risk choice over proving that no test writes to shared state: the suite has 558 test files and 43 of those that spawn subprocesses are not individually audited. Falsifier: a test depends on all workers sharing one root; the three parallel runs would show it.
- Serial behavior of `tests/conftest.py` stays identical when `PYTEST_XDIST_WORKER` is not set.
- `addopts` is left without `-n` because a bare `uv run pytest <one test>` would pay worker start-up and the coverage runs would silently report 0% for worker-executed code; falsifier: a parallel-mode coverage setup is adopted later (a separate Issue).
- The three known failures belong to this Plan's scope (the Issue includes them); other tests that spawn subprocesses with a minimal environment are reported only.
- Overlap judgment (Step 8b), compatible and sequencing: this Plan and `plans/20261113-093307_testspeed001_mark-repo-scan-tests.md` edit different lines of `skills/python-test-and-fix/workflow.md` Step 10 and `skills/code-implementation/workflow.md` Step 4 (a `--testmon-forceselect` command there, full-run wording here); implement that Plan first and re-read both sections before Phase 4.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Serial full-suite wall time | Not measured | Measure in Phase 1 with the same selection and `-p no:randomly` | False |
| UNK-02 | Whether any test is order-dependent or relies on a shared root under random ordering in parallel | Random-order parallel runs were not tried | Phase 3 runs; report each failure with cause and owner instead of rewriting a test | False |
| UNK-03 | Whether the three mdq failures also occur in CI or on other machines | CI results are unavailable (`gh` is not authenticated) | Expected not to occur where `/opt/llm/db/mdq.sqlite` is absent; the owner may check the CI log after the change | False |
| UNK-04 | Which other tests that spawn subprocesses can reach repository config paths (for example `tests/mcp_servers/test_mcp_launcher.py`) | 43 test files spawn subprocesses and only 2 use `isolated_subprocess_env`; they were not audited | List them in the change record for a follow-up Issue; do not fix them here | False |
| UNK-05 | Open dependencies named by the Issue: `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md` (Plan `plans/20261113-093307_testspeed001_mark-repo-scan-tests.md`, rows not `Completed`) and `issues/20261112-183849_testspeed003_cut-timeout-test-waits.md` (Plan `plans/20261113-092136_testspeed003_cut-timeout-test-waits.md`, rows not `Completed`) | Both Plans are `Pending` | Not needed first: implement them before this Plan only to avoid text conflicts (001) and to raise the benefit (003) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/mcp_servers/test_config_isolation_import.py | Modify | Low | 3 | N/A | not applicable (rsynced) |
| tests/mcp_servers/test_require_auth_token.py | Modify | Low | 4 | N/A | not applicable (rsynced) |
| tests/conftest.py | Modify | High (loaded by every one of the 558 test files; import-time isolation) | 7 | N/A | not applicable (rsynced) |
| tests/test_production_isolation.py | Modify | Low | N/A | N/A | not applicable (rsynced) |
| rules/toolchain.md | Modify | Medium (read by every workflow) | 15 | N/A | not applicable (rsynced) |
| skills/python-test-and-fix/workflow.md | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| skills/code-implementation/workflow.md | Modify | Medium | 15 | N/A | not applicable (rsynced) |

## Design
- Path B because seven files are targets. Architecture analysis: tests, rules, and skill text only; no import or layer change, so `lint-imports` is unaffected. Dependency graphing: `tests/conftest.py` is loaded by every test module; `tools/check_conftest_integrity.py` guards its required fixtures. Historical analysis: the 30-day commit counts are in `Affected areas`; `rules/toolchain.md` and `skills/code-implementation/workflow.md` are the busiest, so edit only the lines named above. Operational inspection: the change does not touch an MCP server or a database; the mdq cause concerns the production database path `/opt/llm/db/mdq.sqlite`, which is read by the failing tests' subprocess and must not be modified; the session fingerprint fixture stays as the detector.
- Validation quality baseline: `N/A: no Python target` under `scripts/` or `tools/`.
- Blast radius (`rules/toolchain.md` Impact-radius check): the conftest change reaches all 558 test files at import time, so the full suite runs serially and in parallel after it, and `tools/check_conftest_integrity.py` runs. The `-n` default changes how every full run executes.
- Decision D1, parallelism default. Chosen: a documented command (`-n auto` in the full-suite commands) with serial as the opt-out and as the mode for flaky, mutation, and coverage runs; `addopts` stays without `-n`. Alternatives: an `addopts` entry `-n auto` (rejected: every single-test run pays worker start-up, `-n 0` would be needed everywhere, and coverage runs silently report 0% for code run in workers, measured, which breaks the 90% diff-cover gate); `-n logical` or a fixed count (rejected: no evidence for a better value). Compatibility impact: none for existing commands; CI is unchanged.
- Decision D2, isolation root under workers. Chosen: each worker builds its own root when `PYTEST_XDIST_WORKER` is set and the inherited root is not its own; descendants of a worker, which inherit both the worker id and the root, reuse it; a serial run is unchanged. Alternatives: keep the shared root and audit every test that writes to it (rejected: 558 test files, no cheap way to prove absence); a per-test root (rejected: provisioning the databases per test is too costly). Compatibility impact: subprocess-based tests keep inheriting the worker's root through the environment, which `isolated_subprocess_env` already forwards; root creation costs one provisioning per worker.
- Decision D3, the mdq tests. Chosen: build the child environment from the isolation variables, through the `isolated_subprocess_env` fixture the repository already provides (`extra` carries the token variables, `PYTHONPATH`, and the per-test log directory). Alternatives: skip the mdq cases on a host that has a production database (rejected: the Issue forbids skipping, and the gap would remain); fix the production database (rejected: out of scope and the production state is not touched). Compatibility impact: the tests read the isolated config, so they no longer depend on the host's production database.
- Per-test guard and fingerprint fixture: unchanged; they run in every worker process, and each worker fingerprints `/opt/llm/db` itself.
- Sequencing: Phase 1 gives a clean baseline; Phase 2 must land before Phase 3 (the runs verify it); Phase 4 documents what Phase 3 verified.

## Implementation steps
Each step cites the rows of `Implementation Target Files` above.

1. **Phase 1: Clean baseline**
   - [ ] Build the child environment of the three mdq tests from the isolation variables (REQ-002; tests/mcp_servers/test_config_isolation_import.py, tests/mcp_servers/test_require_auth_token.py)
   - [ ] Run the three tests serially and in parallel; take the serial baseline and the parallel result for the same selection and record the times (REQ-001, REQ-002; the two test files)
2. **Phase 2: Per-worker isolation root**
   - [ ] Make `_setup_isolation` create a root per worker and keep descendant reuse and serial behavior (REQ-003; tests/conftest.py)
   - [ ] Add the test for the per-worker rule using the fresh-interpreter pattern (REQ-003; tests/test_production_isolation.py)
   - [ ] Run `tools/check_conftest_integrity.py`, the isolation tests serially and under `-n auto`, then the full suite serially once (REQ-003; tests/conftest.py, tests/test_production_isolation.py)
3. **Phase 3: Parallel verification**
   - [ ] Run the full non-integration suite in parallel with random ordering three times, record the seeds, and compare; report each failure with cause and owner (REQ-004; tests/conftest.py)
   - [ ] Check that no `llmagent-test-*` directory remains afterwards and the session fingerprint check passed (REQ-003, REQ-004; tests/conftest.py)
4. **Phase 4: Documentation of the default**
   - [ ] State the default, the opt-out, and the serial exceptions in `rules/toolchain.md` sections 6 and 7 (REQ-005; rules/toolchain.md)
   - [ ] Update the `pytest-xdist` row and the Step 10 full-run command, keeping serial for flaky, mutation, and coverage runs (REQ-005; skills/python-test-and-fix/workflow.md)
   - [ ] Update the Step 4 full-suite wording and keep the coverage run serial (REQ-005; skills/code-implementation/workflow.md)
   - [ ] Run the two skill checkers (REQ-005; the three documentation files)
   - [ ] No deploy step: only files under `tests/`, `rules/`, and `skills/` change

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/mcp_servers/test_config_isolation_import.py, tests/mcp_servers/test_require_auth_token.py | Unit with fresh interpreters | `uv run pytest tests/mcp_servers/test_config_isolation_import.py tests/mcp_servers/test_require_auth_token.py -p no:randomly` | All pass, including the three mdq cases |
| tests/conftest.py, tests/test_production_isolation.py | Isolation tests | `uv run pytest tests/test_production_isolation.py` and `uv run pytest tests/test_production_isolation.py -n auto` | All pass in both modes |
| tests/conftest.py | Integrity gate | `uv run python tools/check_conftest_integrity.py` | Exit 0 |
| Suite | Baseline | `uv run pytest -q -p no:randomly -m "not integration and not production_paths_allowed" --durations=25 -o addopts=""` serially, then with `-n auto` | Times recorded; zero failures after Phase 1 |
| Suite | Random-order parallel | `uv run pytest -n auto -q -m "not integration and not production_paths_allowed" -o addopts=""` three times with `pytest-randomly` active | Zero failures, or each failure listed with cause and owner |
| Temporary directory | Cleanup | list `llmagent-test-*` under the temporary directory before and after a run | No directory left by a normally exiting run |
| Production database | Fingerprint | the session fingerprint fixture of `tests/conftest.py` | No change reported |
| rules/toolchain.md, skills/python-test-and-fix/workflow.md, skills/code-implementation/workflow.md | Static | `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py` | Exit 0 |
| Touched Python files | Static | `uv run ruff format <files>`, `uv run ruff check <files>`, `uv run mypy --no-namespace-packages <files>` | Clean |
| Diff | Gate discovery | `uv run python tools/run_validation_gates.py` | Summary without `Fail` |

## Risks
- **Risk**: The conftest change breaks isolation for tests that rely on process-tree reuse (fresh-interpreter and subprocess tests) → **Mitigation**: descendants of a worker still reuse its root; the new test covers it; the full suite runs serially and in parallel after the change; `check_conftest_integrity.py` runs.
- **Risk**: Per-worker roots leak temporary directories → **Mitigation**: each worker registers its own cleanup (`atexit` and `pytest_sessionfinish` already do this for a created root); AC-003 checks the temporary directory.
- **Risk**: Random ordering in parallel exposes order-dependent tests and the suite is not green → **Mitigation**: report each with cause and owner (AC-004), do not rewrite it silently, and keep the documented default conditional on Phase 3's result; if a failure is unresolved, Phase 4 documents the serial recommendation and the open failure instead.
- **Risk**: A `-n` default hides a coverage gap (0% for worker code) → **Mitigation**: `addopts` stays without `-n` (D1); the documents name coverage runs as serial.
- **Risk**: The production isolation is weakened to make parallel runs pass → **Mitigation**: the per-test guard and the fingerprint fixture are not edited; only the root choice changes; the fingerprint check must pass in every run.
- **Risk**: The mdq tests start to pass for the wrong reason (the child no longer reaches the schema check) → **Mitigation**: the tests keep asserting `auth_token is empty` for the empty-token case and the config-isolation assertions; read the failing assertion's expected text after the change.
- **Risk**: Text conflict with the Plan for `testspeed001` in the same skill sections → **Mitigation**: implement that Plan first and re-read both sections before Phase 4; the overlap checker lists the shared files.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: clean baseline (tests/mcp_servers/test_config_isolation_import.py, tests/mcp_servers/test_require_auth_token.py) | In Progress | — | — |  |
| 2 | Phase 2: per-worker isolation root (tests/conftest.py, tests/test_production_isolation.py) | In Progress | — | — |  |
| 3 | Phase 3: parallel verification with random ordering (tests/conftest.py) | Pending | — | — |  |
| 4 | Phase 4: document the default (rules/toolchain.md, skills/python-test-and-fix/workflow.md, skills/code-implementation/workflow.md) | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261113-102519_01_tests_mcp_servers_test_config_isolation_import.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261113-102519_02_tests_mcp_servers_test_require_auth_token.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261113-102519_03_tests_conftest.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261113-102519_04_tests_test_production_isolation.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261113-102519_05_rules_toolchain.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261113-102519_06_skills_python-test-and-fix_workflow.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261113-102519_07_skills_code-implementation_workflow.md.md | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261113-093804
- **Related target files**: tests/mcp_servers/test_config_isolation_import.py, tests/mcp_servers/test_require_auth_token.py, tests/conftest.py, tests/test_production_isolation.py, rules/toolchain.md, skills/python-test-and-fix/workflow.md, skills/code-implementation/workflow.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (record serial baseline and parallel result) | tests/mcp_servers/test_config_isolation_import.py | Phase 1 | AC-001 | Validation plan: baseline row | Explicit in issue |
| REQ-002 | Issue Required Changes (fix the three failing tests); cause measured (checked in Step 2) | tests/mcp_servers/test_config_isolation_import.py | Phase 1 | AC-002 | Validation plan: first row | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (fix the three failing tests); cause measured (checked in Step 2) | tests/mcp_servers/test_require_auth_token.py | Phase 1 | AC-002 | Validation plan: first row | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (show the isolation guard is safe with workers, or fix it); `-n 2` probe (checked in Step 2) | tests/conftest.py | Phase 2 | AC-003 | Validation plan: isolation, integrity, and cleanup rows | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (show the isolation guard is safe with workers, or fix it); `-n 2` probe (checked in Step 2) | tests/test_production_isolation.py | Phase 2 | AC-003 | Validation plan: isolation row | Confirmed by repository evidence |
| REQ-004 | Issue Acceptance Criteria (three random-order parallel runs) | tests/conftest.py | Phase 3 | AC-004 | Validation plan: random-order parallel row | Explicit in issue |
| REQ-005 | Issue Required Changes (decide and implement the default; describe coverage); coverage measurement (checked in Step 2) | rules/toolchain.md | Phase 4 | AC-005 | Validation plan: static row | Derived from confirmed evidence |
| REQ-005 | Issue Required Changes (decide and implement the default; describe coverage); coverage measurement (checked in Step 2) | skills/python-test-and-fix/workflow.md | Phase 4 | AC-005 | Validation plan: static row | Derived from confirmed evidence |
| REQ-005 | Issue Required Changes (decide and implement the default; describe coverage); coverage measurement (checked in Step 2) | skills/code-implementation/workflow.md | Phase 4 | AC-005 | Validation plan: static row | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261113-102519 -->
