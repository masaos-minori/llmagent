## Goal
- Make `test_raises_on_timeout` finish in about 2 s or less instead of about 8 s while keeping its `did not become healthy` assertion (`REQ-003`: shorten the terminate and poll waits from the test side; `REQ-001`: record the measured split).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the one test body of `TestStartHttpSubprocess.test_raises_on_timeout`.
- Not in scope: production constants, the three `integration` tests of the file, other timeout tests.

## Assumptions
- The 8 s is `timeout=1` plus `HEALTH_POLL_INTERVAL_SEC` (0.5) plus `TERMINATE_TIMEOUT_SEC` (5.0), because the mocked process (`_make_mock_proc()`, `poll` returns `None`) never exits, so the terminate-on-timeout call waits its full timeout. This is derived, not measured (Plan `UNK-03`); step 1 measures it. Falsifier: the patched run is still above about 2 s.
- `TERMINATE_TIMEOUT_SEC` is read at manager construction (passed to the subprocess launcher in `HttpServerLifecycleManager.__init__`) and again at call time (passed to the poll loop in `HttpServerLifecycleManager`), and `HEALTH_POLL_INTERVAL_SEC` at call time, so the patches must be active before `_ServerLifecycleRouter(...)` is constructed.

## Design decisions
- Patch the two module constants of `agent.http_lifecycle` from the test; production values stay.
- Keep `timeout=1` so the real deadline still expires, which keeps the timeout path exercised.

## Alternatives considered
N/A: a clock patch would also affect the event loop; the constants are the existing injection points.

## Implementation
### Target file
`tests/agent/test_lifecycle.py`

### Procedure
1. Measure first: run `uv run pytest "tests/agent/test_lifecycle.py::TestStartHttpSubprocess::test_raises_on_timeout" --durations=3 -o addopts=""`; then run it once with only `TERMINATE_TIMEOUT_SEC` patched and note which constant carries the time (record in the commit message; Plan `UNK-03`).
2. In `test_raises_on_timeout`, enter `patch("agent.http_lifecycle.TERMINATE_TIMEOUT_SEC", 0.05)` and `patch("agent.http_lifecycle.HEALTH_POLL_INTERVAL_SEC", 0.05)` before the line that builds `mgr = _ServerLifecycleRouter({"s": cfg}, ex)`, and keep them active through `await mgr.start_http_subprocess("s", cfg)`.
3. Re-run the command and note the duration.

### Method
`agent.http_lifecycle` defines both constants at module level and passes them to `HttpServerLifecycleManager`'s launcher at construction and to `poll_until_ready` at call time, so a `unittest.mock.patch` of the module attribute reaches both. Reuse the file's existing `patch` import; add the two patches to a `with` that encloses the manager construction, or restructure the existing `with` so construction happens inside it.

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
- **Requirement ID**: REQ-001 (record the cause and split), REQ-003 (cut the terminate and poll waits)
- **Source issue**: issues/20261112-183849_testspeed003_cut-timeout-test-waits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-092136_testspeed003_cut-timeout-test-waits.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-101644
- **Related target files**: `tests/agent/test_lifecycle.py`
