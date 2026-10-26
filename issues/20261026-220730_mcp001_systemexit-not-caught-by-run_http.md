# SystemExit raised by _enforce_posture_gate() is not caught by MCPServer.run_http()

## Priority
High

## Summary
When `_enforce_posture_gate()` raises `SystemExit(1)` during `MCPServer.run_http()`, the process exits immediately without any uvicorn server shutdown or connection draining.

## Background
All MCP servers define `_enforce_posture_gate()` that raises `SystemExit(1)` when the security posture is not validated. This function is called in the `if __name__ == "__main__"` block before `server.run_http()`. However, `MCPServer.run_http()` also calls `_enforce_startup_posture_gate()` internally (line 294 of `server.py`) as part of the startup sequence.

## Problem
If `_enforce_startup_posture_gate()` raises `SystemExit(1)` inside `run_http()`, the `try/except KeyboardInterrupt` block (lines 321-324 of `server.py`) does not catch `SystemExit`. The process terminates abruptly without:
- Closing active HTTP connections gracefully
- Releasing uvicorn server resources
- Logging the failure reason to stderr/stdout in a structured way

This is especially problematic because `run_http()` is the public entry point used by all server launchers (binary launchers, mcp_launcher, python -m). Any launcher that calls `run_http()` directly inherits this silent-exit behavior.

## Reason for Change
A silent `SystemExit` during startup makes it impossible to distinguish between a posture-gate failure and other fatal errors (e.g., port-in-use, config parse error). Operators cannot reliably detect whether the server refused to start due to a security posture violation versus a transient infrastructure issue.

## Implementation Intent
Ensure `SystemExit` raised by `_enforce_startup_posture_gate()` is caught inside `run_http()` and handled consistently with other startup failures. Options include:
1. Catch `SystemExit` alongside `KeyboardInterrupt` in `run_http()` and log the failure reason before exiting.
2. Have `_enforce_startup_posture_gate()` raise a custom exception (e.g., `SecurityPostureError`) instead of `SystemExit`, allowing `run_http()` to handle it uniformly.
3. Move the posture gate check outside of `run_http()` and require callers to invoke it before calling `run_http()`.

## Target Files or Areas
- `scripts/mcp_servers/server.py` — `MCPServer.run_http()` method
- All MCP server modules that define `_enforce_posture_gate()`

## Required Changes
- Add `SystemExit` handling to `MCPServer.run_http()` or replace `SystemExit` with a custom exception in `_enforce_startup_posture_gate()`
- Ensure the failure reason is logged before exit
- Verify all server launch paths handle the new behavior correctly

## Constraints
- Must not change the existing posture-gate semantics (fail-closed on invalid posture)
- Must preserve backward compatibility with existing launcher scripts

## Acceptance Criteria
- `SystemExit(1)` raised during `run_http()` is caught and logged with the failure reason
- Active connections are drained before process exit
- All MCP server launch paths produce consistent error output

## Testing Expectations
- Unit test: verify `run_http()` handles `SystemExit` from `_enforce_startup_posture_gate()`
- Integration test: verify graceful shutdown on posture-gate failure
- Regression test: ensure existing posture-gate failures still prevent HTTP bind

## Documentation Impact
Update `MCPServer.run_http()` docstring to document the `SystemExit` handling behavior.

## Out of Scope
- Changes to the posture validation logic itself
- Changes to how `_enforce_posture_gate()` is called in `__main__` blocks

## Dependencies
N/A: none

## Unresolved Questions
- Should `SystemExit` be caught at the `run_http()` level or should `_enforce_startup_posture_gate()` use a custom exception?
- Does the current `sys.exit(1)` after `server.run()` (line 326) also need similar treatment?

## AI Implementation Instruction
Modify `MCPServer.run_http()` in `scripts/mcp_servers/server.py` to catch `SystemExit` raised by `_enforce_startup_posture_gate()`. Log the failure reason before exiting. Do not modify any other MCP server's `__main__` block or posture gate logic.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/server.py
