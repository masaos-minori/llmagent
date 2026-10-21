# Clarify MCP subprocess termination ownership and remove unused spawned-subprocess list return

## Priority
Medium

## Summary
Remove the `list[subprocess.Popen]` value that `StartupOrchestrator.run()` returns for the spawned HTTP MCP subprocesses, because `AgentREPL.run()` receives it but never uses it to terminate those processes. Subprocess termination is already handled exclusively by `lifecycle.shutdown_all()`. Make the ownership explicit so no future reader assumes the caller terminates the subprocesses.

## Background
`StartupOrchestrator.run()` (`scripts/agent/startup.py`) spawns HTTP-subprocess MCP servers via `McpServerStarter.start_servers()` and returns a `list[subprocess.Popen]` as its third tuple element. The docstring/comment at `startup.py` says "Pass subprocess list to caller for termination". `AgentREPL.run()` (`scripts/agent/repl.py`) unpacks that third element into a local named `_spawned_subprocesses` and never references it again on any later line. Termination actually happens in `ResourceShutdownCoordinator.close_resources()` (`scripts/agent/resource_shutdown_coordinator.py`), which calls `svc.lifecycle.shutdown_all()`. That routes through `_ServerLifecycleRouter.shutdown_all()` -> `_SubprocessLifecycleManager.shutdown_all()` -> `ShutdownCoordinator.shutdown_all()`, which iterates every process tracked in `HttpServerLifecycleManager._http_procs` and terminates each one. Every successfully spawned process is registered in that dict by `SubprocessLauncher.create_and_validate_proc()`.

## Problem
The returned subprocess list creates a false contract: a comment claims the caller terminates the processes, but the caller never touches the list. Ownership of subprocess termination is therefore undocumented and split across two mental models — the return-value path (dead) and the lifecycle-manager path (real). If anyone later removes subprocess handling from `shutdown_all()` believing the caller already handles it, the subprocesses will be orphaned with no error.

## Reason for Change
The dead return value and its misleading comment are a latent maintainability hazard. They encode a termination responsibility that does not exist, so a plausible future refactor could silently drop subprocess cleanup. Removing the dead path and stating the real owner removes the ambiguity at its source.

## Implementation Intent
- Remove the `list[subprocess.Popen]` element from the tuple returned by `StartupOrchestrator.run()` and from `McpServerStarter.start_servers()` only if it is purely a pass-through (keep the internal `_spawned_subprocesses` tracking used for stagger/retry bookkeeping; do not remove that).
- Update `AgentREPL.run()` to stop unpacking the third element, or keep a throwaway binding (`_ = ...`) with an explicit comment that termination is owned by the lifecycle manager, not the caller.
- Correct the "Pass subprocess list to caller for termination" comment to state that the lifecycle manager owns termination and the list is returned only for observability/testing, or remove the return entirely.
- Preserve the existing rollback behavior in `StartupOrchestrator.run()` (terminate subprocesses on setup failure via `lifecycle.shutdown_all()`); do not move termination to the caller.

## Target Files or Areas
- `scripts/agent/startup.py` (`StartupOrchestrator.run()` return signature and comment)
- `scripts/agent/repl.py` (`AgentREPL.run()` unpacking of the third tuple element)
- `scripts/agent/startup_mcp_starter.py` (`start_servers()` return) — only if the list is a pure pass-through

## Required Changes
- Stop returning the spawned-subprocess list as a caller-facing termination handle.
- Remove the unused `_spawned_subprocesses` binding in `AgentREPL.run()`.
- Rewrite the misleading comment to reflect that `lifecycle.shutdown_all()` owns termination.
- Add or update a unit test asserting that `AgentREPL.run()` does not rely on the returned list for cleanup and that shutdown goes through the lifecycle manager.

## Constraints
- Do not change which processes get terminated or the timing of shutdown.
- Do not break any existing test that inspects the returned tuple shape.
- Keep the internal per-server tracking used for stagger delay and retry bookkeeping intact.

## Acceptance Criteria
- No code path in `AgentREPL.run()` references the previously returned subprocess list.
- The "caller for termination" comment no longer asserts a non-terminated contract.
- Subprocess cleanup on both normal shutdown and startup-rollback still routes through `lifecycle.shutdown_all()`.
- Startup and shutdown unit tests pass.

## Testing Expectations
- Unit tests for `StartupOrchestrator.run()` and `AgentREPL` shutdown paths.
- A focused test confirming the lifecycle manager terminates every spawned process after `run()` returns.
- `uv run ruff check`, `uv run mypy`, `uv run bandit` on edited files.

## Documentation Impact
No governance documents are affected. If a design note exists for the startup/shutdown contract, record that termination is lifecycle-manager-owned; otherwise none.

## Out of Scope
- Any change to which processes are spawned, their health checks, or the stagger/retry logic.
- Refactoring `ResourceShutdownCoordinator` or the lifecycle manager termination order.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether `McpServerStarter.start_servers()`'s return should be dropped entirely or kept solely for test observability; dropping is recommended if nothing else reads it.

## AI Implementation Instruction
- Change only the return-value plumbing and the misleading comment; do not alter shutdown semantics or the internal tracking list.
- Confirm with a grep that no other module reads the third tuple element before removing it.
- Do not touch health-check, stagger, or retry logic.
- Stop and report if another caller of `StartupOrchestrator.run()` depends on the returned list.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-220228
- **Related target files**: `scripts/agent/startup.py`, `scripts/agent/repl.py`, `scripts/agent/startup_mcp_starter.py`
