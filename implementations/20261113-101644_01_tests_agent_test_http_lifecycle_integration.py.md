## Goal
- Make `test_restart_clears_stderr_file` finish in about 2 s or less instead of 30 s while keeping its assertions (`REQ-002`: cut the busy-loop wait; `REQ-001`: record why it waited).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the one test body of `TestSubprocessLifecycle.test_restart_clears_stderr_file`.
- Not in scope: production timeouts, other tests of the file, the `_make_cfg` default of 30.

## Assumptions
- The wait is the deadline loop `while time.monotonic() < deadline` in `scripts/agent/http_lifecycle_health_checker.py`; with `asyncio.sleep` patched out it busy-spins until the deadline, which `HttpServerLifecycleManager` computes as `time.monotonic() + cfg.startup_timeout_sec`. Falsifier: after the change the test still takes about 30 s.
- This test does not patch `mgr._process_terminator.terminate_with_timeout`, unlike its sibling above it. That is existing behavior and stays unchanged here; the owner may want it hardened separately.

## Design decisions
- Shorten the config's `startup_timeout_sec` instead of patching `time.monotonic`: a global clock patch also feeds the event loop's own timers.
- Use 1 second: the loop must still reach its deadline so `HttpStartupError` is raised by the timeout path.

## Alternatives considered
N/A: a clock patch is rejected in Design decisions; no other alternative applies.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_integration.py`

### Procedure
1. Before editing, run `uv run pytest tests/agent/test_http_lifecycle_integration.py::TestSubprocessLifecycle::test_restart_clears_stderr_file --durations=3 -o addopts=""` and note the duration (about 30 s).
2. In `test_restart_clears_stderr_file`, pass `_make_cfg(startup_timeout_sec=1)` to `mgr.restart` instead of `_make_cfg()`.
3. Re-run the same command and note the duration.

### Method
`_make_cfg` applies keyword overrides through `defaults.update(overrides)`, so `startup_timeout_sec=1` replaces the default 30.

### Details
- Keep `pytest.raises(HttpStartupError)` and both closing assertions (`mgr._stderr_files.get("test") is None` and `mgr._stderr_log_manager.get_log_path("test") is None`).
- Do not touch `patch.object(asyncio, "sleep", return_value=None)`; the loop spins for about 1 s, which is the intended cost.
- Record in the commit message: cause (deadline loop busy-spin for the 30 s `startup_timeout_sec`), before and after durations.

## Compatibility considerations
N/A: test-only change; no production source, public interface, or default changes.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_integration.py -o addopts=""` serially, then with `-n auto`, repeated a few times.
- `uv run ruff check tests/agent/test_http_lifecycle_integration.py` and `uv run mypy --no-namespace-packages tests/agent/test_http_lifecycle_integration.py`.

## Completion criteria
- The test finishes in about 2 s or less in an 8-way parallel run and still asserts the `HttpStartupError`, the cleared stderr file, and the cleared log path (`AC-002`).
- No file under `scripts/` changed.

## Out of Scope
- Any change to `scripts/agent/http_lifecycle_health_checker.py` or `scripts/agent/http_lifecycle.py`.
- The other waiting tests of the Plan (separate rows).

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
- **Requirement ID**: REQ-001 (record the cause), REQ-002 (cut the 30 s busy-loop wait)
- **Source issue**: issues/20261112-183849_testspeed003_cut-timeout-test-waits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-092136_testspeed003_cut-timeout-test-waits.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-101644
- **Related target files**: `tests/agent/test_http_lifecycle_integration.py`
