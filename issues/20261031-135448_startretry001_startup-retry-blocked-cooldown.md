# MCP subprocess startup retry never launches a second attempt because of the failure cooldown

## Priority
High

## Summary
`McpServerStarter.start_servers` is documented to retry a failed MCP subprocess start once. The first failure records a failure cooldown in `_ServerLifecycleRouter`, and the retry call reaches `start_http_subprocess`, whose cooldown guard returns `None` without starting anything and without raising. The retry therefore never launches a process, startup aborts with a generic "failed to start after retry" message, and the real failure reason is lost from the operator's console. Make the startup retry a genuine second attempt and keep the original failure as the cause.

## Background
Found during an adversarial review (`python-code-review`) of the agent startup path.
- `issues/done/20261005-121409_stp001_mcp-server-startup-retry-no-longer-retries-runtimeerror-and-loses-the-fatal-context.md` restored the retry for `RuntimeError`/`HttpStartupError` (the common startup failure). That fix is intact; the retry is entered, but the second call is suppressed below it.
- The cooldown guard in `_ServerLifecycleRouter.start_http_subprocess` and `_run_lifecycle_transition` (failure timestamp, 30-second window) comes from the split of the lifecycle router out of the factory. The startup retry delay (`RETRY_DELAY_SEC`) is 1 second, far shorter than the cooldown.
- The MCP subprocess startup documentation states that the starter retries once after `RETRY_DELAY_SEC` and then raises a `[fatal]` `RuntimeError`.
- Existing starter and startup tests mock the lifecycle manager; none of `test_startup_mcp_starter.py`, `test_startup_mcp_lifecycle.py`, `test_startup.py`, or `test_retry_helper.py` references the cooldown, so the interaction is untested.

## Problem
Sequence for one subprocess server whose first start fails with `HttpStartupError`:
1. `start_servers` calls `_start_http_subprocess_once`; the router runs the start in `_run_lifecycle_transition`, which records the failure time and state `FAILED` and re-raises.
2. `start_servers` catches the error (it is a `RuntimeError`) and calls `retry_once_with_delay`, whose first action is to call the same start function immediately.
3. The router's `start_http_subprocess` finds the server in cooldown and returns `None`. No process is started and nothing is raised.
4. `retry_once_with_delay` treats the `None` return as success and returns; `start_servers` sees `None` and raises "MCP subprocess ... failed to start after retry".

Observed in a reproduction using the real router and starter with only the subprocess layer faked (fails once, would succeed on a second call): exactly one attempt reached the subprocess layer, the exception was the generic `RuntimeError`, and the router state was `FAILED`. A transient failure (for example a port race or slow dependency) is therefore always fatal. The first failure's reason (server key and stderr tail) is only written to an INFO log line.

Related ambiguity: `_start_http_subprocess_once` returns `None` both for "suppressed by cooldown or shutdown" and for "no process started". On the first attempt `start_servers` treats `None` as success, and on the retry it treats `None` as failure.

## Reason for Change
The documented retry-once behavior does not exist at runtime, so startup is less robust than documented, and the console error ("failed to start after retry") hides the actual cause. The earlier fix (`stp001`) only moved the retry into the `RuntimeError` path; without this change that path is still a no-op.

## Implementation Intent
The cooldown exists to throttle automatic restarts at runtime (`ensure_ready`); it should not silently veto the explicit startup retry. Make "suppressed" distinguishable from "started" so a suppressed start cannot be mistaken for success or for a completed retry, and make the startup retry a real second launch attempt. Preserve the original failure (server key and reason) as the cause of the final error. Keep the runtime cooldown behavior for `ensure_ready` and `restart`.

## Target Files or Areas
- `scripts/agent/lifecycle_router.py` (`_ServerLifecycleRouter.start_http_subprocess`, `_run_lifecycle_transition`, cooldown helpers)
- `scripts/agent/startup_mcp_starter.py` (`McpServerStarter.start_servers`, `_start_http_subprocess_once`)
- `scripts/agent/shared/retry_helper.py` (`retry_once_with_delay`)
- `tests/agent/test_startup_mcp_starter.py`, `tests/agent/test_startup_mcp_lifecycle.py`

## Required Changes
- Ensure the second startup attempt actually reaches the subprocess layer after a first failure.
- Replace the `None` return used for "start suppressed" with an unambiguous signal (a typed error or an explicit result), and handle it in `start_servers` so it is never reported as success.
- Carry the first failure's server key and reason into the final raised error.
- Add an integration-style test that uses the real router with only the subprocess layer faked: first call fails, second succeeds; and a second test where both fail.

## Constraints
- Runtime cooldown for `ensure_ready` and `restart` must keep working as today.
- `retry_once_with_delay` must keep preserving the original exception type and secret masking.
- The shutdown-event handling during the retry delay must still raise `StartupInterrupted`.
- All subprocess MCP servers stay required and fail closed when startup finally fails.

## Acceptance Criteria
- A first-attempt failure followed by a successful second attempt results in the server being started and startup continuing.
- Two consecutive failures abort startup with an error that names the server and carries the last failure reason.
- A suppressed start is never treated as a successful start by `start_servers`.
- Runtime `ensure_ready` still refuses restarts inside the cooldown window.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Integration-style unit tests as described in Required Changes, using the real `_ServerLifecycleRouter` and `McpServerStarter`.
- Regression: run `tests/agent/test_startup_mcp_starter.py`, `tests/agent/test_startup_mcp_lifecycle.py`, `tests/agent/test_startup.py`, `tests/agent/test_retry_helper.py`.
- Run `ruff` and `mypy --no-namespace-packages` on the touched files.

## Documentation Impact
The MCP subprocess startup documentation already describes retry-once-then-fatal. After the fix, check that its wording (retry after `RETRY_DELAY_SEC`, final `[fatal]` error) matches the behavior, and note that the runtime restart cooldown does not apply to the startup retry. No concrete timing values should be copied into the documents.

## Out of Scope
- Changing the length of `RETRY_DELAY_SEC` or the cooldown window.
- Orphan handling of a process that fails its readiness poll (tracked in `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md`).
- The post-startup health-check retry in `verify_health`.

## Dependencies
- Related to `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md`: a "shutdown requested" `HttpStartupError` flows into this retry path today. Either issue can be fixed first; after both are fixed, an interrupted start should surface as `StartupInterrupted`.
- `issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md` changes the masker used by `retry_once_with_delay` and is independent of this issue.

## Unresolved Questions
- Whether the cooldown should be bypassed for the explicit startup path or the router should expose a separate start entry point for startup: a design choice for the implementer, not decided here.
- Whether any startup flow other than `start_servers` depends on `start_http_subprocess` returning `None` during cooldown: `Needs confirmation` by a caller search before changing the return contract.

## AI Implementation Instruction
Keep the change to the startup start path and its tests. Do not change the cooldown duration, the runtime restart behavior, or the retry helper's exception-preservation contract. Write the failing integration-style test first, then fix. Stop and report if removing the `None` return breaks callers outside `scripts/agent/`.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-135448
- **Related target files**: scripts/agent/lifecycle_router.py, scripts/agent/startup_mcp_starter.py, scripts/agent/shared/retry_helper.py, tests/agent/test_startup_mcp_starter.py, tests/agent/test_startup_mcp_lifecycle.py
