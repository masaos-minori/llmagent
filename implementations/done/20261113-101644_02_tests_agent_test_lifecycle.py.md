## Goal
- Make `test_raises_on_timeout` finish in about 2 s or less instead of about 8 s while keeping its `did not become healthy` assertion (`REQ-003`: shorten the terminate and poll waits from the test side; `REQ-001`: record the measured split).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the one test body of `TestStartHttpSubprocess.test_raises_on_timeout`.
- Not in scope: production constants, the three `integration` tests of the file, other timeout tests.

## Assumptions
- Measured at implementation time (corrects the derivation above): the 8.2 s is `timeout=1` plus `TERMINATE_TIMEOUT_SEC` (5.0, the SIGTERM wait: `os.killpg` is mocked, so `os.killpg(pgid, 0)` never reports the group gone) plus the post-SIGKILL confirmation window `_DEFAULT_KILL_CONFIRM_TIMEOUT_SEC` of `ProcessTerminator` (2.0, the same reason). Patching only `TERMINATE_TIMEOUT_SEC` gave 3.2 s; additionally patching `HEALTH_POLL_INTERVAL_SEC` changed nothing, so it is not part of the fix. Falsifier: the final run is still above about 2 s.
- `TERMINATE_TIMEOUT_SEC` is read at call time (passed to the poll loop in `HttpServerLifecycleManager`), so patching the module attribute before `start_http_subprocess` is enough. The kill-confirm window is a `ProcessTerminator` constructor argument; the existing tests of this file already inject `ProcessTerminator(kill_confirm_timeout_sec=0.02)` into a manager, and the router's manager is `_ServerLifecycleRouter._subprocess_mgr._http_mgr`.

## Design decisions
- Patch `TERMINATE_TIMEOUT_SEC` of `agent.http_lifecycle` through the `monkeypatch` fixture (automatic cleanup) and give the router's manager a `ProcessTerminator` with short `terminate_poll_interval_sec` and `kill_confirm_timeout_sec`, as the file's other tests do; production values stay.
- Keep `timeout=1` so the real deadline still expires, which keeps the timeout path exercised.

## Alternatives considered
N/A: a clock patch would also affect the event loop; the constants are the existing injection points.

## Implementation
### Target file
`tests/agent/test_lifecycle.py`

### Procedure
1. Measure first (done at implementation time): baseline 8.2 s; with only `TERMINATE_TIMEOUT_SEC` patched 3.2 s; with `HEALTH_POLL_INTERVAL_SEC` also patched 3.2 s (record in the commit message; Plan `UNK-03`).
2. In `test_raises_on_timeout`, take the `monkeypatch` fixture, set `agent.http_lifecycle.TERMINATE_TIMEOUT_SEC` to 0.05 with it, and after `mgr = _ServerLifecycleRouter({"s": cfg}, ex)` replace `mgr._subprocess_mgr._http_mgr._process_terminator` with `ProcessTerminator(terminate_poll_interval_sec=0.01, kill_confirm_timeout_sec=0.05)`.
3. Re-run the command and note the duration.

### Method
`agent.http_lifecycle` defines `TERMINATE_TIMEOUT_SEC` at module level and passes it to `poll_until_ready` at call time, so `monkeypatch.setattr` on the module attribute reaches it. The health checker terminates through `manager.process_terminator`, which returns the manager's `_process_terminator`, so replacing that attribute shortens both the SIGTERM poll and the post-SIGKILL window. `ProcessTerminator` is already imported in the test module.

### Details
- Keep `pytest.raises(RuntimeError, match="did not become healthy")` and the `client_instance.get` side effect `httpx.ConnectError("connect refused")` unchanged.
- Do not change the three `@pytest.mark.integration` tests.
- If the measured time stays above about 2 s because of the mocked client, report the split rather than lowering `timeout`.

## Compatibility considerations
N/A: test-only change; no production source or default changes.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py -m "not integration and not production_paths_allowed" --durations=10 -o addopts=""` serially, then with `-n auto`, repeated a few times.
- `uv run ruff check tests/agent/test_lifecycle.py` and `uv run mypy --no-namespace-packages tests/agent/test_lifecycle.py`.

## Completion criteria
- `test_raises_on_timeout` finishes in about 2 s or less in an 8-way parallel run and still asserts the `did not become healthy` error (`AC-003`).
- The measured split of the former 8 s is in the commit message.

## Out of Scope
- Changes to `scripts/agent/http_lifecycle.py`.
- The other waiting tests of the Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-105218 | 20261113-110422 | Changed tests/agent/test_lifecycle.py (test_raises_on_timeout: monkeypatch TERMINATE_TIMEOUT_SEC to 0.05 and a ProcessTerminator with short poll and kill-confirm windows). Procedure corrected at Step 3b: measured split 8.17 s = 1 s deadline + 5 s SIGTERM wait + 2 s post-SIGKILL window; HEALTH_POLL_INTERVAL_SEC has no effect. Result 1.22 s. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-110422 | 20261113-110422 | Targeted file 79 passed serially (3 integration deselected) and twice with -n auto; the change is the test itself. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-110422 | 20261113-110422 | ruff clean. mypy on this file reports 31 errors, the same 31 at HEAD (none in the changed lines; unrelated, file outside the CI mypy scope). Full suite serial 12159 passed, 3 failed: the known mdq cases (unrelated, Plan testspeed004). diff-cover N/A: no source file changed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-110422 | 20261113-110422 | N/A: no docs/00_index.md task-scope mapping for tests/agent/test_lifecycle.py |

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
- **Requirement ID**: REQ-001 (record the cause and split), REQ-003 (cut the terminate and poll waits)
- **Source issue**: issues/20261112-183849_testspeed003_cut-timeout-test-waits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-092136_testspeed003_cut-timeout-test-waits.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-101644
- **Related target files**: `tests/agent/test_lifecycle.py`
