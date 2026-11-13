## Goal
- Make the connection-failure test of `tests/deploy/test_setup_services_eventbus.py` wait only a few attempts instead of 15, keep a retry margin where the path depends on a real process, and state for each test that stays above about 2 s why (`REQ-004`; `REQ-001`: record causes and before and after durations).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `_run_setup` helper and `test_setup_services_connection_failure_aborts`; recording the duration and reason per test of the file.
- Not in scope: `deploy/setup_services.sh` (production script, read only), the canned-server helpers, adding the `integration` marker (see Design decisions).

## Assumptions
- `deploy/setup_services.sh` reads `LLM_HEALTH_RETRIES` and `LLM_HEALTH_INTERVAL` and uses the interval in bash integer arithmetic (`$((LLM_HEALTH_RETRIES * LLM_HEALTH_INTERVAL))`) under `set -euo pipefail`, so the interval must stay an integer and the wait floor is retries times 1 s plus the real eventbus child start. Falsifier: a decimal interval is accepted by the script.
- The connection-failure path only ends after the retry loop is exhausted, so fewer retries still exercise it and still print the `000` retry line. Falsifier: the `000` assertion fails with 3 retries.
- The process-exit path (`malformed=True`) depends on the child exiting during start-up before the retries run out; with few retries the script could instead end through the "did not become ready" path, which would stop testing the exit path.

## Design decisions
- Add a `retries` parameter (new) to `_run_setup` (default 15, today's value) and pass a small value only from the connection-failure test.
- Leave the process-exit, healthy-start, and canned-server tests at the default margin; they start a real eventbus process, so about 4 s or more is their floor. Record them as kept with that reason instead of marking `integration`, which would drop them from default runs.

## Alternatives considered
- A decimal `LLM_HEALTH_INTERVAL` such as 0.2: rejected, it breaks the script's arithmetic in the FATAL message path.
- Marking the file `integration`: rejected as the default; the owner can decide after the measurement (Plan `UNK-02`).

## Implementation
### Target file
`tests/deploy/test_setup_services_eventbus.py`

### Procedure
1. Measure first: `uv run pytest tests/deploy/test_setup_services_eventbus.py --durations=12 -o addopts=""`; note each test's duration.
2. Add a `retries` parameter (new), typed `int` with default 15, to `_run_setup(sb, health_url)` and use `str(retries)` for the `LLM_HEALTH_RETRIES` entry of its environment; keep `LLM_HEALTH_INTERVAL` at `"1"`.
3. In `test_setup_services_connection_failure_aborts`, call `_run_setup(sb, f"http://127.0.0.1:{unreachable}/health", retries=3)`.
4. Re-run the file with `--durations=12`; for each test still above about 2 s record, in the commit message, the duration and the reason (real eventbus child start; retry floor of retries times 1 s).

### Method
`_run_setup` builds the child environment dictionary `env` and runs `bash deploy/setup_services.sh` through `subprocess.run`; only the retry count changes. The connection-failure test keeps its assertions on `returncode == 1`, `[FATAL] Event Bus` in stderr, `000` in stdout, the absence of the READY line, and the child being killed by `eb_gate_fail`.

### Details
- Do not change the process-exit, status-not-ok, healthy-start, malformed-body, missing-liveness, or accepts-real-payload tests.
- Add a one-line comment above `retries` stating that the interval must stay an integer because the script multiplies it.
- If `000` is missing from stdout with 3 retries, raise the value to the smallest that shows it and record the number.

## Compatibility considerations
N/A: test-only change; the script and its defaults are untouched.

## Security considerations
N/A: the helper keeps its sandbox environment (`DEPLOY_DB`, `DEPLOY_LOGS`, `LLMAGENT_CONFIG_DIR` under the sandbox); no production path is added.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/deploy/test_setup_services_eventbus.py --durations=12 -o addopts=""` serially, then with `-n auto`, repeated a few times.
- `uv run ruff check tests/deploy/test_setup_services_eventbus.py` and `uv run mypy --no-namespace-packages tests/deploy/test_setup_services_eventbus.py`.

## Completion criteria
- The connection-failure test no longer waits 15 attempts and keeps every assertion; the other tests are unchanged.
- Each test above about 2 s has a stated reason in the change record (`AC-004`).
- No file under `deploy/` changed.

## Out of Scope
- `deploy/setup_services.sh`.
- Adding the `integration` marker (a follow-up decision).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (record causes and durations), REQ-004 (shorten the script retry wait)
- **Source issue**: issues/20261112-183849_testspeed003_cut-timeout-test-waits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-092136_testspeed003_cut-timeout-test-waits.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-101644
- **Related target files**: `tests/deploy/test_setup_services_eventbus.py`
