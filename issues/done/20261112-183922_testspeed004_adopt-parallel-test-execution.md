# Adopt parallel test execution as the standard way to run the suite

## Priority
Medium

## Summary
`pytest-xdist` is installed but not used by default, so the full suite runs on one core. Establish, with measurements, that the suite can run in parallel safely, fix the three failures that currently block a green baseline, and make parallel execution the documented standard for local runs. The goal is a shorter full-suite run with the same verification.

## Background
- Measured on 2026-11-12 with `uv run pytest -n auto -q -p no:randomly -m "not integration and not production_paths_allowed" --durations=25 -o addopts=""` on 8 cores: 3 failed, 12129 passed, 7 skipped, 226.87 s (wall 3m52s), 9m25s of CPU time. The serial wall time was not measured, so the speedup factor is unknown.
- `pyproject.toml` `[tool.pytest.ini_options]` has `addopts = "-v --tb=short"`, no `-n`. `pytest-xdist`, `pytest-randomly`, `pytest-timeout`, and `pytest-testmon` are all dev dependencies.
- `skills/python-test-and-fix/workflow.md` (tool table) says xdist is not part of the default run and is to be used only after confirming the isolation guard is safe under multiple workers. `tests/conftest.py` contains the guard against tests opening databases or logs under `/opt/llm` and a session-scoped fingerprint fixture. That safety confirmation has not been done.
- The three failures are `tests/mcp_servers/test_config_isolation_import.py::test_restrict_first_import_loads_only_the_own_config[...mdq...]`, `...::test_a_server_module_executes_once_under_python_m[...mdq...]`, and `tests/mcp_servers/test_require_auth_token.py::test_empty_token_prevents_every_server_from_importing[...mdq...]`. They also fail when run serially (3 failed, 3 passed in 2.6 s), so they are not caused by parallelism. In the last one, the assertion `"auth_token is empty" in result.stderr` fails because stderr holds a traceback that ends with a message about archiving, removing or renaming an existing database. The cause (for example a database file present on this machine) was not determined.

Verified on 2026-11-13 (cause determined):
- The tests start a fresh interpreter with a hand-built minimal environment (`PATH`, `HOME`, token variables, `PYTHONPATH`, `LLMAGENT_LOG_DIR`) that omits `LLMAGENT_CONFIG_DIR`. The child therefore reads the repository `config/mdq_mcp_server.toml`, whose `db_path` is `/opt/llm/db/mdq.sqlite`, the production mdq database of this host. That file (dated 7 July) holds a table `chunk_summaries` that the canonical schema does not define, so `shared/schema_fingerprint.py` raises `RuntimeError: mdq.sqlite: unexpected table 'chunk_summaries' ...` before the expected auth-token message.
- So the failure is an environment dependency that comes from a test-isolation gap: these subprocess tests reach a production database path. The session fingerprint fixture only detects a change of the files, and a read-only schema check does not change them. A host with an empty or missing `/opt/llm/db` (the CI `test` job creates only `docs` and `logs` under `/opt/llm`) does not reproduce it, so CI is unlikely to show these failures (not checked: CI access is unavailable).
- `tests/conftest.py` already provides the `isolated_subprocess_env` fixture, which forwards the isolation variables (`LLMAGENT_CONFIG_DIR` among them) to a child; the failing tests do not use it.
- The production database must not be changed or removed as part of this issue.
- `tests/mcp_servers/test_mcp_launcher.py` builds its subprocess environment the same way (`PATH` and `HOME` only), so it has the same gap; it does not fail on this host, but it can reach the repository config paths. Of 43 test files that spawn subprocesses, 2 use `isolated_subprocess_env`.
- Coverage under workers (measured on a scratch test): `coverage run -m pytest -n 2` reports 0% for a module executed only in the workers, against 90% for the serial run, with exit status 0 in both. A `-n` entry in `addopts` would therefore silently empty the coverage report that feeds the 90% diff-cover gate (`rules/toolchain.md` section 7, `skills/code-implementation/workflow.md` Step 4, and the `Coverage report` step of `ci.yml`). Coverage runs must stay serial unless a parallel-mode coverage setup is added, which this issue does not do.
- The runs above used `-p no:randomly`; parallel runs with random ordering were not tried.

## Problem
Full-suite runs use one core while an 8-core machine is available, and the suite has a known-red baseline of three tests, so a developer cannot tell a new regression from an existing failure. The decision on parallel execution is blocked on an unverified isolation claim and on those failures.

## Reason for Change
Test wall time dominates the implementation loop, and parallel execution is the cheapest lever that does not touch any test. Doing it now needs a clean baseline, so the three failures are part of the same change. Nothing in the repository sets a deadline for it.

## Implementation Intent
Work in this order: (1) take a serial baseline with the same selection expression, (2) find the cause of the three mdq failures and fix or classify them, (3) verify that the production-path isolation guard and the shared-resource tests (ports, files, SQLite files, subprocesses) behave under multiple workers, including with random ordering, (4) choose how parallelism becomes the default (an `addopts` entry, or a documented command with an opt-out) and update the documented commands. Keep serial execution available for flaky-test investigation as the existing skill text requires.

## Target Files or Areas
- `pyproject.toml` (`addopts`, `[tool.coverage.run]` if coverage must support workers)
- `tests/conftest.py` (isolation guard under workers; read first)
- `tests/mcp_servers/test_config_isolation_import.py`, `tests/mcp_servers/test_require_auth_token.py` (the failures)
- `rules/toolchain.md` (sections 6 and 7 commands)
- `skills/python-test-and-fix/workflow.md` (tool table row for `pytest-xdist`)
- `skills/code-implementation/workflow.md` (Step 4 commands)

## Required Changes
- Record the serial baseline (same `-m` expression, `-p no:randomly`) and the parallel result.
- Determine and fix (or document as an environment dependency) the three failing tests; state which database or setting the traceback refers to.
- Show the isolation guard is safe with multiple workers, or fix it (the shared isolation root is the known gap: give each worker its own root, or show that no test writes to the shared state concurrently); run the parallel suite with random ordering at least three times and compare results.
- Decide and implement the default; update `rules/toolchain.md`, the python-test-and-fix tool table, and the Step 4 command lines consistently.
- Describe how coverage is collected when workers are used, or state that coverage runs stay serial.

## Constraints
- The `/opt/llm` isolation guarantee must hold; no test may open production databases or logs, whatever the worker count.
- Serial execution must stay available and must stay the recommended mode for flaky-test investigation and mutation runs, as in the current skill text.
- No test may be deleted or weakened to make parallel runs pass.
- CI workflow changes are a separate issue.

## Acceptance Criteria
- A recorded serial and parallel timing for the same selection, from the same machine.
- Zero failures in three consecutive parallel runs with random ordering enabled, or each remaining failure listed with a cause and an owner.
- The three mdq tests pass, or each has a documented, reviewed reason to be marked as an environment-dependent test.
- The default and the opt-out are documented identically in `rules/toolchain.md`, `skills/python-test-and-fix/workflow.md`, and `skills/code-implementation/workflow.md`.
- `uv run python tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` pass after the skill edits.

## Testing Expectations
- The full suite, serial and parallel, as above.
- The isolation tests (`tests/test_production_isolation.py` and the guard in `tests/conftest.py`) run under `-n auto`.
- `uv run python tools/check_conftest_integrity.py` if `tests/conftest.py` changes.
- `uv run ruff check`, `uv run mypy` on touched Python files.

## Documentation Impact
Yes: the operational commands and the xdist usage rule in `rules/toolchain.md`, `skills/python-test-and-fix/workflow.md`, and `skills/code-implementation/workflow.md`. State intent (when to use parallel, when not) and the isolation constraint; do not copy configuration values into prose beyond the command lines.

## Out of Scope
- Changing `.github/workflows/ci.yml`.
- Reducing individual test durations (separate issues).
- Changing which tests are selected by markers.
- `pytest-testmon` state maintenance.

## Dependencies
- `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md`: related; both may edit the `pyproject.toml` pytest settings and the Step 4 command line, so coordinate the order at planning time.
- `issues/20261112-183849_testspeed003_cut-timeout-test-waits.md`: related; the longest single tests set the floor of parallel wall time, so their fixes raise the benefit of this change.

## Unresolved Questions
- Serial full-suite wall time: 不明. Not measured.
- Resolved (2026-11-13): cause of the three mdq failures (see Background); fix direction is test-side (`isolated_subprocess_env`), not a production database change.
- Whether the failures also occur in CI and on other machines: 不明 (CI results unavailable); expected not to occur where `/opt/llm/db/mdq.sqlite` is absent.
- Whether the `/opt/llm` isolation guard and session fingerprint fixture are safe under multiple workers: partly answered on 2026-11-13. The per-test guard and the session fingerprint fixture run in every worker process, and each worker fingerprints `/opt/llm/db` itself. But the isolation root is shared: `tests/conftest.py::_setup_isolation` creates the temporary root "once per process tree" and reuses `LLMAGENT_TEST_ROOT` when it is already set, and an xdist worker inherits that variable. A probe with `-n 2` (two workers, `gw0` and `gw1`) showed both workers using the same root, so the isolated `session`, `rag`, `workflow` and `eventbus` SQLite files, the logs and the storage directory are shared between concurrently running tests. Which tests write to that shared state, and whether a per-worker root is needed, is not determined; the earlier parallel run passing does not show it is safe.
- Behavior with `pytest-randomly` enabled in parallel: 不明. Not run.

## AI Implementation Instruction
Measure first and report numbers before editing. Fix the three failures by understanding their cause, not by skipping them. Do not weaken the isolation guard to allow parallel runs. Keep the change to settings and documentation unless a test proves to be order-dependent; report any such test instead of rewriting it silently.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261112-183922
- **Related target files**: `pyproject.toml`, `tests/conftest.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/mcp_servers/test_require_auth_token.py`, `rules/toolchain.md`, `skills/python-test-and-fix/workflow.md`, `skills/code-implementation/workflow.md`
