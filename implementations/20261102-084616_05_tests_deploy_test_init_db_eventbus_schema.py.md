## Goal

Make the deploy test's subprocess inherit the isolation variables by building its environment through the shared fixture (`REQ-004`: subprocess inherits the isolation variables).

## Scope

- Change `_run` in `tests/deploy/test_init_db_eventbus_schema.py` and its three call sites to take the environment from `isolated_subprocess_env`.
- The other deploy tests that build `env` by hand stay unchanged.

## Assumptions

- Plan overlaps: none names this Plan (`tools/check_plan_target_overlaps.py`, 2026-11-02); no sibling Plan targets this file: compatible.
- Verified 2026-11-02: `_run(driver_path)` builds `env` from `PATH` and `HOME` only and is called by three tests; the driver script already exports `LLMAGENT_CONFIG_DIR` and `LLMAGENT_LOG_DIR` to the sandbox, and `_write_config` pins `workflow_db_path` in the sandbox `agent.toml`, so the file's docstring claim (nothing under `/opt/llm/db` touched) already holds for those paths; the fixture adds the remaining isolation variables (`EVENTBUS_CONFIG_PATH`, `EVENTBUS_SCHEMA_PATH`, `LLMAGENT_TEST_ROOT`).
- Because the driver exports its own `LLMAGENT_CONFIG_DIR` and `LLMAGENT_LOG_DIR` after the process environment is set, the driver values win; the inherited `EVENTBUS_*` variables point into the isolation root, not production. Whether `create_schema.py` reads `EVENTBUS_CONFIG_PATH` in a way that changes these tests' outcomes is not exercised yet: non-blocking, covered by AC-4 (the three tests must pass) and the Plan's Risks.
- `isolated_subprocess_env` is created by procedure 01 (earlier `seq`).

## Design decisions

- Pass the fixture's builder into `_run` as a parameter, keeping `_run` a plain function; tests request the fixture by argument name.

## Alternatives considered

- N/A: adopting the other four hand-built callers is a later cleanup (Plan Design).

## Implementation
### Target file
`tests/deploy/test_init_db_eventbus_schema.py`

### Procedure
1. Change the signature to `_run(driver_path, env)` and replace the hand-built `env` dict with the argument.
2. Add `isolated_subprocess_env` to each of the three tests' parameters and pass `isolated_subprocess_env()` at each `_run` call.
3. Update the "Sandboxing" docstring paragraph to say the subprocess environment comes from the shared fixture.

### Method
- Keep the `subprocess.run` arguments (timeout 180, `capture_output`, `text`) unchanged.
- Remove the `os` import only if nothing else in the module uses it (the helper no longer reads `os.environ`).

### Details
- The skip condition on `/opt/llm/pyproject.toml` stays; without it the module is skipped and the change is not exercised on CI.

## Compatibility considerations

- The subprocess now also sees `EVENTBUS_CONFIG_PATH`, `EVENTBUS_SCHEMA_PATH`, and `LLMAGENT_TEST_ROOT`; the driver still overrides config and log directories. A changed outcome in any of the three tests is the signal named in the Plan Risks.

## Security considerations

- N/A: the fixture forwards only isolation variables plus `PATH` and `HOME`; the sandbox paths remain under `tmp_path`.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/deploy/test_init_db_eventbus_schema.py -v` (all three pass; requires `/opt/llm/pyproject.toml`, present on this host).
- `uv run ruff format`, `uv run ruff check`, and `uv run mypy` on the file per `rules/toolchain.md`.

## Completion criteria

- `_run` takes its environment from `isolated_subprocess_env`, the three tests pass, and the subprocess environment contains the isolation variables.

## Out of Scope

- The other deploy and eventbus tests that build `env` by hand; changes to `deploy/init_db.sh`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Use `isolated_subprocess_env` in `_run` and its three call sites | Pending | — | — | |
| 2 | Run the test file and the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (deploy test uses the isolated environment fixture)
- **Source issue**: issues/20261030-191351_flowimp006_suite-production-guard.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075648_flowimp006_suite-production-guard.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084616
- **Related target files**: `tests/deploy/test_init_db_eventbus_schema.py`
