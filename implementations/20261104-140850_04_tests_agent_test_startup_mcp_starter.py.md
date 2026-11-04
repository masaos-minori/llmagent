## Goal
- Add integration-style tests, with the real `_ServerLifecycleRouter` and the real `McpServerStarter` and only the subprocess layer faked, that show the startup retry is a genuine second launch attempt, that a double failure aborts with a named error and a visible first failure, and that a start suppressed by shutdown becomes `StartupInterrupted` (`REQ-005`: fail-then-succeed, fail-then-fail, and shutdown-suppressed start; they fail on the pre-change code and pass after it).

## Scope
**Release unit**: N/A: not part of a release unit

- New test code only, in `tests/agent/test_startup_mcp_starter.py`. No production code, no change to the existing tests of the file.

## Assumptions
- Execution order: this procedure depends on no name created by the others (it uses `HttpStartupError`, `StartupFailure`, `LifecycleState`, `StartupInterrupted`, and the router and starter as they exist today), so the executor SHOULD run it first, per the Plan's Phase 1, to record the new tests failing on the pre-change code (`AC-5`), then run the release-unit procedures.
- The starter module's `logger` is a `shared.logger.Logger` wrapper whose underlying logger has `propagate = False`, so `caplog` cannot capture its records; the first-failure warning is asserted by patching `agent.startup_mcp_starter.logger` (checked in Step 3a).
- The retry delay is read as the module constant `RETRY_DELAY_SEC` at call time, so patching `agent.startup_mcp_starter.RETRY_DELAY_SEC` to a negligible value avoids a real sleep.
- `_ServerLifecycleRouter(...)` builds a real `_SubprocessLifecycleManager` and `HttpServerLifecycleManager` without spawning anything; the tests replace `router._subprocess_mgr._http_mgr` with a fake, as `tests/agent/test_agent_factory.py` already does.
- The existing starter tests of this file build a real `McpServerStarter` around a `MagicMock` context; the new class follows that style and keeps local imports inside helpers or tests like the file does.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- One helper `_real_router_ctx(failures)` (new) builds the context: a real `McpServerConfig` (HTTP, subprocess startup, a `cmd`), a real router with its `_http_mgr` replaced by an `AsyncMock` whose `_http_procs` is a dict and whose `start` side effect raises the given exceptions in order and then records a `MagicMock(spec=subprocess.Popen)` under the server key; the context's `services_required.lifecycle` is the router.
- Three tests in a class `TestStartupRetryWithRealRouter` (new); each assertion targets the observable contract, not self-assigned mock state.

## Alternatives considered
N/A: the test shape is fixed by the Plan's Tests section; faking only the subprocess manager is what makes the cooldown interaction observable.

## Implementation
### Target file
`tests/agent/test_startup_mcp_starter.py`

### Procedure
1. Append the helper `_real_router_ctx` (new) and the class `TestStartupRetryWithRealRouter` (new) at the end of the file.
2. Mark the async tests with `@pytest.mark.asyncio`, like the file's other async tests.
3. Patch `agent.startup_mcp_starter.RETRY_DELAY_SEC` to `0.0` in the two tests that reach the retry.

### Method
- Helper: `failures` is a list of exceptions; `start` is `AsyncMock(side_effect=_start)` where `_start(key, cfg, shutdown_event=None)` counts calls, raises `failures[n-1]` while `n <= len(failures)`, otherwise stores the fake process in `_http_procs[key]` and returns `None`. Return the context, the router, the fake manager, and the fake process. Build failures as `HttpStartupError(StartupFailure("srv", "port busy", ""))` (all three `StartupFailure` fields are required).
- Test 1, `test_first_failure_then_success_launches_second_attempt` (new): one failure; `await McpServerStarter(ctx, MagicMock()).start_servers()` returns `[proc]`; `fake_mgr.start.await_count == 2`; `router.get_transport_state("srv") == LifecycleState.RUNNING`; `"srv" not in router._failed_starts`.
- Test 2, `test_two_failures_abort_with_named_error_and_visible_first_failure` (new): two distinct failures with different reasons; `pytest.raises(HttpStartupError)`; the text of the raised error contains `srv` and the second reason; `fake_mgr.start.await_count == 2`; the raised error's `__cause__.__context__` is the first failure; `patch("agent.startup_mcp_starter.logger")` records a `warning` call whose format string contains `First attempt failed` and whose arguments contain `srv` and the first reason.
- Test 3, `test_shutdown_suppressed_start_raises_startup_interrupted` (new): no failures; make the fake manager's `shutdown_all` an `AsyncMock` returning `[]`, `await router.shutdown_all()`, then `pytest.raises(StartupInterrupted)` around `start_servers()`; `fake_mgr.start.assert_not_called()`. Import `StartupInterrupted` from `agent.startup` inside the test.

### Details
- Use only public or already-tested names: `LifecycleState` from `agent.lifecycle`, `HttpStartupError` and `StartupFailure` from `agent.http_lifecycle_errors`.
- Do not assert on state the test assigned to a mock; the router state and call counts come from the real router and the fake's call counter.
- Keep the file's existing tests and imports untouched.

## Compatibility considerations
N/A: test-only change; the new tests rely on the production change of the sibling procedures and are expected to fail before it.

## Security considerations
N/A: synthetic server key and reasons; no real process, network, or credential.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before the production procedures run: `uv run pytest tests/agent/test_startup_mcp_starter.py -k TestStartupRetryWithRealRouter -q` shows the three tests failing; record the output in the Failure Log.
- After them: the same command passes with at least three tests collected, and `uv run pytest tests/agent/test_startup_mcp_starter.py -q` passes in full.
- `uv run ruff format --check`, `uv run ruff check`, `uv run python tools/check_mock_patch_targets.py`, and `uv run python tools/check_suppression_justification.py` report no findings.

## Completion criteria
- The three tests exist and pass after the production change; two or more of them were seen failing on the pre-change code (`AC-1`, `AC-2`, `AC-3`, `AC-5`).
- The first-failure warning and the exception chain are asserted, and no test sleeps for the real retry delay.

## Out of Scope
- Production code, the existing mock-based retry tests, and the characterization tests in the other test files (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the helper and the three tests as described in Implementation > Procedure/Method | Pending | — | — | |
| 2 | Run the new tests before the production change and record the failures, then run them after | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (integration-style tests with the real router and starter)
- **Source issue**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095204_startretry001_startup-retry-blocked-cooldown.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-140850
- **Related target files**: `tests/agent/test_startup_mcp_starter.py`
