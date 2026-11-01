# MCP subprocess is orphaned when startup fails or is interrupted during the readiness poll

## Priority
High

## Summary
When a freshly spawned MCP subprocess fails its startup readiness poll, the lifecycle manager drops the process from its tracking tables without making sure the process is gone. A shutdown request that arrives during the poll leaves the spawned process running and untracked, so neither the startup rollback nor `close_resources()` can stop it. Make every startup-failure path either terminate the process or keep it tracked until termination is confirmed.

## Background
Found during an adversarial review (`python-code-review`) of the agent startup path. Related archived work:
- `issues/done/20261021-220228_star001_clarify-mcp-subprocess-termination-ownership-and-remove-unused-spawned-subprocess-list-return.md` and `plans/done/20261022-082349_plan.md` made `shutdown_all()` report unconfirmed terminations. That work covers the tracked-process shutdown path, not the startup-failure path described here.
- The existing test `test_shutdown_event_set_before_poll_raises_promptly` in `tests/agent/test_http_lifecycle_integration.py` asserts that the tracking entries are removed after a "shutdown requested" start failure. It does not assert that the process was terminated, so it pins the current behavior.

The subprocess is launched with `start_new_session=True`, so it does not die with the agent process.

## Problem
`HealthChecker.poll_until_ready` ends in three ways, and all three call `HttpServerLifecycleManager._raise_startup_failure`, which pops the process and pgid entries and raises `HttpStartupError`:
- Process exited early: the process is already gone. No defect.
- Shutdown requested during the poll sleep: the process is alive, and nothing terminates it before the tracking entry is dropped.
- Readiness timeout: `terminate_with_timeout` is called, but its `TerminationOutcome` is ignored. An unconfirmed exit is dropped from tracking as if it were confirmed.

`ShutdownCoordinator.shutdown_all` iterates only the tracked processes, so an untracked survivor is invisible to the rollback in `StartupOrchestrator._rollback_servers` and to `ResourceShutdownCoordinator.close_resources`.

Reproduction (throwaway script, not committed): a harmless `sleep 30` process registered as the tracked process, a `shutdown_event` that is already set, then `_health_poll_until_ready`. Observed: `HttpStartupError` with reason "shutdown requested"; the child was still alive and no longer tracked; a following `shutdown_all()` returned an empty list and the child was still alive.

## Reason for Change
An orphaned MCP server keeps its configured port and keeps running after the agent has exited. A shutdown request during startup is exactly when an operator restarts the service, so the orphan is created in the situation where it is most likely to be hit again. The shutdown path already treats "exit not confirmed" as a reportable error; the startup-failure path silently does the opposite.

## Implementation Intent
Make process termination and tracking removal one decision on the startup-failure path: terminate first, drop the tracking entry only for a confirmed exit, and keep an unconfirmed process tracked so the existing `shutdown_all()` reporting names it. Keep the early-exit behavior unchanged. Reuse the existing `ProcessTerminator` and `TerminationOutcome` semantics instead of adding a second termination mechanism.

## Target Files or Areas
- `scripts/agent/http_lifecycle_health_checker.py` (`HealthChecker.poll_until_ready`)
- `scripts/agent/http_lifecycle.py` (`HttpServerLifecycleManager._raise_startup_failure`, `start`)
- `scripts/agent/http_lifecycle_subprocess_launcher.py` (`SubprocessLauncher.handle_getpgid_failure`, for consistency with its existing termination handling)
- `tests/agent/test_http_lifecycle_integration.py`

## Required Changes
- In the "shutdown requested" branch of the poll loop, terminate the live process through `ProcessTerminator.terminate_with_timeout` before the startup failure is raised.
- In the readiness-timeout branch, use the returned `TerminationOutcome`: remove tracking only when `confirmed` is true; otherwise keep the process (and pgid) tracked so `shutdown_all()` reports it.
- Apply the same rule to any other startup-failure path that leaves a live process.
- Update the existing shutdown-during-poll test to assert termination, and add tests for the unconfirmed-termination branch.

## Constraints
- Do not change `ShutdownCoordinator.shutdown_all` outcome semantics or the `TerminationOutcome` definition.
- Do not change the early-exit branch.
- Subprocesses must still be started in their own session; termination must still go through the process group.
- A termination failure must not mask the original startup error.

## Acceptance Criteria
- After a shutdown request during the readiness poll, the spawned process is not alive, or it remains tracked with an unconfirmed outcome that `shutdown_all()` returns.
- After a readiness timeout with an unconfirmed termination, the process stays tracked and `shutdown_all()` reports its server key.
- The early-exit behavior is unchanged.
- No test relies on the removed behavior of dropping a live process from tracking.

## Testing Expectations
- Unit/integration: a test with a real harmless child process (for example `sleep`) that sets the shutdown event before the poll and asserts the child is gone afterward; always kill the child in test teardown.
- Unit: a test with a fake terminator returning an unconfirmed outcome, asserting the tracking entry is kept and reported by `shutdown_all()`.
- Run `tests/agent/test_http_lifecycle*.py`, `tests/agent/test_startup_rollback.py`, and the lint/type gates (`ruff`, `mypy --no-namespace-packages`).

## Documentation Impact
Needs confirmation: check whether the MCP subprocess startup documentation under `docs/22_mcp/` states what happens to a process whose startup fails. If it does, state the rule "a failed start never leaves a live untracked process". Otherwise no update is needed.

## Out of Scope
- `ShutdownCoordinator.shutdown_all` and `ProcessTerminator` internals.
- Orphan prevention when the agent process itself is force-killed.
- The startup retry behavior (tracked separately, see Dependencies).

## Dependencies
- Related to `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`: a "shutdown requested" `HttpStartupError` is a `RuntimeError`, so it currently enters the startup retry path and is reported as a generic start failure. Either issue can be fixed first; after both are fixed, an interrupted start should surface as `StartupInterrupted`, not as a retried failure.
- Related to `issues/20261031-135634_validorder001_config-validation-after-spawn.md`: moving config-only validation before server start shrinks the window in which this orphan can occur, but does not remove it. Independent fix order.
- `issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md` touches modules in the same area but is independent.

## Unresolved Questions
- Assumption (not verified end to end): a surviving orphan keeps the configured port, so the next agent start either fails to bind or health-polls the stale server. The exact outcome depends on the server implementation.
- Should a "shutdown requested" start failure be converted to `StartupInterrupted` at this layer or at the caller? This is shared with the retry issue and needs one decision.

## AI Implementation Instruction
Change only the startup-failure paths named above. Keep termination on the existing `ProcessTerminator`. Do not touch unrelated lifecycle code, the retry logic, or the shutdown coordinator. If a termination attempt raises, log it and still raise the original `HttpStartupError`. Stop and report if the fix would require changing `TerminationOutcome` semantics.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-135416
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py, scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_subprocess_launcher.py, tests/agent/test_http_lifecycle_integration.py
