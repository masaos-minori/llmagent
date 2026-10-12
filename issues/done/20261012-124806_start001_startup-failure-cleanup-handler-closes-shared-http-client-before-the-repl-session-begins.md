# Startup-failure cleanup handler closes the shared HTTP client before the REPL session begins

## Priority
High

## Summary
`AgentREPL.run()` calls `ResourceShutdownCoordinator.close_resources()` from a `finally`
block that wraps only `startup.run()`. That `finally` runs on the success path too, so on a
successful startup the shared `httpx.AsyncClient` (held by `LLMClient`) is closed and all MCP
subprocess servers are stopped before the REPL input loop starts. Move the cleanup so it runs
only after the session ends (or on the failure path), never ahead of the input loop.

## Background
`repl.py` extracts startup orchestration into `StartupOrchestrator` and resource cleanup into
`ResourceShutdownCoordinator`. The original implementation placed `close_resources()` in a
`finally` attached to the `try` around `startup.run()` (commit `26dc21eff6`). The intent was
cleanup-on-startup-failure, but a `finally` also executes on success.

## Problem
On a successful startup the sequence is: `startup.run()` returns, then `close_resources()`
runs, then the input loop begins. `close_resources()` calls `svc.http.aclose()` and
`svc.lifecycle.shutdown_all()`. `LLMClient._http` and `HistoryManager` hold the same
`httpx.AsyncClient` instance built once in `factory._build_llm_client`; nothing rebuilds it
after startup. A closed client raises on the next request, so the first LLM call after
startup fails and MCP tools are unavailable until a restart.

## Reason for Change
The cleanup handler that is meant to run on startup failure is running on every successful
startup, ahead of the session. This breaks normal operation (LLM calls, tool calls) and, on
normal user exit, there is no post-loop cleanup at all because the single `close_resources()`
call already happened at startup.

## Implementation Intent
Restructure the control flow in `AgentREPL.run()` so that resource cleanup happens exactly
once, after the REPL input loop exits, and the startup-failure rollback stays on the failure
path only. Do not change what `close_resources()` itself does; change only where it is
invoked. Preserve `StartupOrchestrator.run()`'s own rollback (`shutdown_all()` on its error
path) semantics.

## Target Files or Areas
- `scripts/agent/repl.py` (`AgentREPL.run()`)
- `scripts/agent/resource_shutdown_coordinator.py` (`close_resources()`) — read only
- `scripts/agent/startup.py` (`StartupOrchestrator.run()`) — read only
- `scripts/shared/llm_client.py` — read only (evidence)

## Required Changes
- Remove `close_resources()` from the `finally` that wraps `startup.run()`.
- After `await self._input_loop.run(...)` returns, call `await self._shutdown.close_resources()`
  once to cover normal user exit.
- Keep the startup-failure rollback in `StartupOrchestrator.run()` (its own
  `shutdown_all()` on exception) so a failed startup still cleans up spawned subprocesses.
- Confirm the failure path still writes the fatal message and re-raises.

## Constraints
- Do not change the shutdown ordering inside `close_resources()` (WAL checkpoint before task
  cancellation, LIFO task cancel, concurrent service shutdown).
- Do not drop cleanup on the failure path; a failed startup must still terminate spawned
  subprocesses.
- Preserve the `raise` in the `except` block so callers see the startup error.

## Acceptance Criteria
- `close_resources()` is not called before `input_loop.run()` on the success path.
- `close_resources()` is called exactly once per `run()` invocation, after the input loop.
- A startup failure still triggers `StartupOrchestrator.run()`'s rollback and the fatal view
  write, and re-raises.
- Normal user exit (`/exit`, EOF) triggers exactly one `close_resources()`.

## Testing Expectations
- Add/adjust a test that asserts `close_resources()` is NOT called before `input_loop.run()`
  when `startup.run()` succeeds (instrument with a spy, not an AsyncMock that hides the call).
- Add a test that asserts `close_resources()` IS called after the input loop on normal exit.
- Re-run `tests/agent/test_repl.py` and `tests/agent/test_startup_rollback.py`.
- `ruff check`, `mypy`, full suite green.

## Documentation Impact
If `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` describes the
shutdown/cleanup ordering, update it to reflect that cleanup runs after the input loop, not
during startup. Otherwise no doc change.

## Out of Scope
- Any change to `close_resources()` internals.
- Changes to `StartupOrchestrator.run()` rollback logic beyond confirming it stays on the
  failure path.
- Rebuilding the HTTP client or MCP servers lazily as a workaround.

## Dependencies
N/A: none

## Unresolved Questions
- Whether any component reconnects the shared HTTP client after `aclose()` (current source
  shows no rebuild in `scripts/agent/`). Confirm before closing to pin the exact blast radius.
- Whether production currently exhibits breakage or is masked by lazy MCP server restart via
  `_ServerLifecycleRouter.ensure_ready()`.

## AI Implementation Instruction
Do not rewrite `close_resources()`. Only move its single call site out of the startup
`finally` to after `input_loop.run()`, and keep the startup-failure rollback where it is.
Verify with a spy-based test that the call order is correct; do not rely on an AsyncMock
that cannot observe the call.

## Traceability
- **Workflow phase**: `python-code-review` + `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `N/A: not filed from a Plan`
- **Source implementation procedure**: `N/A: not filed from an implementation procedure`
- **Generated at**: 20261012-124806
- **Related target files**: `scripts/agent/repl.py`, `scripts/agent/resource_shutdown_coordinator.py`
