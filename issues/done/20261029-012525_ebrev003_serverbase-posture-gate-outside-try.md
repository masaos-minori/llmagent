# `run_http()` posture-gate runs outside the try block that is documented to catch it

## Priority
Medium

## Summary
In `scripts/mcp_servers/server.py`, `run_http()` documents that it catches the
`SystemExit` raised by `_enforce_startup_posture_gate()` during startup, and the
`except SystemExit` handler carries a `# noqa: BLE001` comment stating it exists for
"posture-gate failure during startup". In fact `_enforce_startup_posture_gate()` is
invoked before the `try` block that wraps `server.run()`. The `except SystemExit`
handler therefore never runs for a posture-gate failure.

## Background
`MCPServer.run_http()` enforces loopback binding, config isolation, and the server's
security posture gate before creating any socket. Each gated server defines
`_enforce_posture_gate()` raising `SystemExit(1)` on policy violation. The base class
method `_enforce_startup_posture_gate()` invokes that gate via
`importlib.import_module(module_name)._enforce_posture_gate()`.

## Problem
Control flow in `run_http()` runs the loopback check, the config-permission check, and
then the posture gate before the `try` block that wraps `server.run()`:

```
if self.http_host not in ("127.0.0.1", "::1"): ...
if self.own_config_file: ... else: raise ConfigPermissionError(...)
self._enforce_startup_posture_gate()      # raises SystemExit on policy violation
class _LoopbackVerifyingServer(uvicorn.Server): ...
server = _LoopbackVerifyingServer(config=config)
try:
    server.run()
except SystemExit as e:  # noqa: BLE001 — posture-gate failure during startup
    logging.getLogger(...).error("Posture-gate failure during startup: %s", e)
    raise
```

`_enforce_startup_posture_gate()` runs before the `try` block that wraps
`server.run()`. A `SystemExit` from the gate therefore propagates uncaught past
`run_http()` to the caller.

The docstring claims:

> Catches ``SystemExit`` raised by ``_enforce_startup_posture_gate()`` during startup so
> that the failure reason is logged before the process terminates.

The `# noqa: BLE001` on the `except SystemExit` justifies it as catching
the posture-gate failure — but the gate never raises inside that `try`.

An existing test confirms the uncaught propagation:
`tests/mcp_servers/test_posture_gate_start_path.py::test_failed_posture_exits_before_binding`
asserts the failed posture exits before binding, i.e. the `SystemExit` leaves
`run_http()` without being handled by the `except SystemExit` handler.

## Reason for Change
The documented and commented contract does not match the control flow. The logging
handler that is supposed to emit "Posture-gate failure during startup" never runs for a
gate failure, and the `# noqa` suppresses a lint rule on a branch that does not cover
its stated purpose.

## Implementation Intent
Either (a) move the `_enforce_startup_posture_gate()` call inside the `try` block so the
documented `except SystemExit` actually logs gate failures, or (b) correct the docstring
and `# noqa` comment to state that the gate runs before the `try` and its `SystemExit`
is not handled here. Option (a) changes behavior (adds a log line) and must be verified
against `test_failed_posture_exits_before_binding`; option (b) is a pure documentation
fix. Recommend (b) unless a fix is explicitly requested, since the current behavior
(fail-fast via uncaught `SystemExit`) is the intended fail-closed outcome.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (`run_http`; its docstring; the `# noqa` on the
  `except SystemExit`; the `_enforce_startup_posture_gate()` call site)
- `tests/mcp_servers/test_posture_gate_start_path.py` (reference only)

## Required Changes
- Align the docstring and `# noqa` comment with the actual control flow, OR move the
  gate call into the `try` and confirm the existing test still passes.
- If left as-is, make the comment state that the `SystemExit` is intentionally not
  caught here.

## Constraints
- Must preserve fail-closed behavior: a failed posture gate must terminate the process
  (via `SystemExit`), never fall through to bind a socket.
- Any change must keep `test_failed_posture_exits_before_binding` green.

## Acceptance Criteria
- The docstring and inline comment accurately describe whether the gate's `SystemExit`
  is handled in `run_http()`.
- If the gate call is moved into the `try`, the existing posture-gate test still passes.

## Testing Expectations
Run `pytest tests/mcp_servers/test_posture_gate_start_path.py`. If behavior changes,
add a test asserting the gate-failure log line is emitted. ruff/mypy clean.

## Documentation Impact
Correct the misleading error-handling description in `run_http()` and the inaccurate
`# noqa` justification.

## Out of Scope
Other servers' posture gates and the loopback-binding logic.

## Dependencies
N/A: none

## Unresolved Questions
Whether the intended design is to log gate failures inside `run_http()` (option a) or
to let them propagate (option b); recommend confirming before changing behavior.

## AI Implementation Instruction
Do not change runtime behavior unless explicitly asked. Prefer correcting the
docstring/comment in `run_http()` to state that the posture gate runs before the
`try`/`except SystemExit`, so its `SystemExit` is intentionally not handled there.
Keep the failing process exiting via uncaught `SystemExit`.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-012525
- **Related target files**: `scripts/mcp_servers/server.py`
