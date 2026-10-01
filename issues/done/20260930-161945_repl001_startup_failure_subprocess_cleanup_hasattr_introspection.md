# Startup-failure subprocess cleanup relies on hasattr introspection and double termination

## Priority
Low

## Summary
`AgentREPL.run()` (`scripts/agent/repl.py`) terminates spawned MCP subprocesses on startup failure by collecting them through `hasattr(startup, "_spawned_subprocesses")` introspection, while `StartupOrchestrator.run()` already calls `lifecycle.shutdown_all()` on its own exception path. Replace the introspection-based collection with a single, authoritative shutdown source to remove redundancy and fragility.

## Background
`StartupOrchestrator.run()` spawns HTTP-subprocess MCP servers, tracks them in `self._spawned_subprocesses`, and on any setup exception calls `await self._ctx.services_required.lifecycle.shutdown_all()` before re-raising. `repl.py`'s `run()` wraps `startup.run()` and, in its `except`, also terminates the returned processes.

## Problem
The `except` block builds its process list via `all_procs = _spawned_subprocesses` then conditionally appends `list(startup._spawned_subprocesses)` using `hasattr`. This depends on attribute introspection and on the local `_spawned_subprocesses` remaining empty when `startup.run()` raises mid-unpacking, and it double-terminates processes that `shutdown_all()` already tore down. It works today but is fragile and redundant.

## Reason for Change
Resource-cleanup code on the failure path should be obvious and singular. Introspection-based collection invites future breakage if `StartupOrchestrator` changes how it exposes spawned processes.

## Implementation Intent
Establish one authoritative shutdown path for startup-spawned subprocesses. Either (a) rely solely on `StartupOrchestrator.run()`'s internal `shutdown_all()` and remove the termination loop from `repl.py`, or (b) have `startup.run()` propagate the process list reliably and terminate there once. Confirm with whoever owns the lifecycle contract which is correct; do not leave two partial terminations.

## Target Files or Areas
- `scripts/agent/repl.py` (`AgentREPL.run()`, the startup-failure except block)
- `scripts/agent/startup.py` (`StartupOrchestrator.run()`)

## Required Changes
- Remove the `hasattr`-based process collection from `repl.py` once the authoritative shutdown source is fixed.
- Ensure each spawned subprocess is terminated exactly once on startup failure.

## Constraints
- Must not introduce orphaned processes on any startup-failure path.
- Must not change the success-path return contract `(cmds, orchestrator, spawned_subprocesses)`.

## Acceptance Criteria
- On startup failure, every spawned MCP subprocess is terminated exactly once (no leak, no double-terminate error).
- `repl.py` no longer references `startup._spawned_subprocesses` via `hasattr`.
- Existing startup-success and startup-failure flows behave as before.

## Testing Expectations
- Simulate a startup failure after N subprocesses spawned; assert all N are terminated and no exception is raised by double termination.
- Assert the success-path return value is unchanged.

## Documentation Impact
If the startup/shutdown contract is documented, note which component owns subprocess termination on failure.

## Out of Scope
- Changing how subprocesses are spawned or health-checked.
- Refactoring the normal REPL shutdown path (`ResourceShutdownCoordinator`).

## Dependencies
N/A: none.

## Unresolved Questions
Which component should be the single authoritative terminator on startup failure -- `StartupOrchestrator.run()`'s `shutdown_all()`, or `repl.py`? Needs owner confirmation before changing.

## AI Implementation Instruction
Do not assume ownership. Determine the correct single shutdown owner; until confirmed, make no behavioral change beyond removing the `hasattr` fragility in a way that cannot leak or double-terminate processes.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-161945
- **Related target files**: scripts/agent/repl.py, scripts/agent/startup.py
