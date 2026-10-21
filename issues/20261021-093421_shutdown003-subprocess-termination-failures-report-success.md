# Subprocess termination failures are reported as success and leave no trace

## Priority
Medium

## Summary
Make MCP subprocess termination failures observable: do not report a terminated server when no termination
signal was actually delivered.

## Background
`ShutdownCoordinator.shutdown_all()` terminates every tracked HTTP/subprocess MCP server concurrently via
`_terminate_one()` (`scripts/agent/http_lifecycle_shutdown_coordinator.py:133-141`), which treats a normal
return from `ProcessTerminator.terminate_with_timeout()` as success and then removes all tracking for that
server with `manager.cleanup_server_key(server_key)` (`:64-69`, `scripts/agent/http_lifecycle.py:159-168`).

## Problem
`terminate_with_timeout()` documents `Raises: HttpStartupError: If process termination fails.`
(`scripts/agent/http_lifecycle_process_terminator.py:125-126`) but never raises; it returns a bool. Most
failure paths return `True`:
- `terminate_method()` wrapped in `except (OSError, AttributeError, TypeError): pass` and then `return True`
  in three separate fallback branches (`:138-144`, `:161-167`, `:174-180`). An `OSError` from
  `proc.terminate()` is discarded and the caller still records success.
- After the graceful timeout, SIGKILL is sent and `True` is returned on `ProcessLookupError` and on the
  success path (`:201-207`). Only a final `OSError` returns `False` (`:208-211`) — and nothing in
  `_terminate_one` inspects the return value, so `False` and `True` behave identically.
- `cleanup_server_key()` then discards `_http_procs` and `_http_pgids` entries (`http_lifecycle.py:166-168`),
  so a possibly-still-running process leaves no record for the operator to clean up.
- The log line at `:206` is malformed: `logger.info("Process group %d already exited after timeout")` has no
  argument, so it emits the literal `%d`.
- Separately, `AgentREPL.run()` receives the started subprocess list from `startup.run()` and binds it to
  `_spawned_subprocesses`, which is never read (`scripts/agent/repl.py:123`, `:132`; the list is produced by
  `scripts/agent/startup.py:73`, `:94` and `startup_mcp_starter.py:117`). Nothing at the REPL level knows
  which subprocesses it started.

## Reason for Change
These servers are started with `start_new_session: True`
(`scripts/agent/http_lifecycle_subprocess_launcher.py:99`), so they do not receive signals with the REPL.
When graceful termination fails, an orphaned MCP server keeps running and holding its port while the REPL
reports a clean shutdown, and the tracking entry that would have told the operator about it is deleted.

## Implementation Intent
Report termination outcome honestly: distinguish "terminated", "already exited", and "could not be
signalled", and keep a record when the last case happens.

## Target Files or Areas
- `scripts/agent/http_lifecycle_process_terminator.py` (`terminate_with_timeout`)
- `scripts/agent/http_lifecycle_shutdown_coordinator.py` (`_terminate_one`, `shutdown_all`)
- `scripts/agent/http_lifecycle.py` (`cleanup_server_key`)
- `scripts/agent/repl.py`, `scripts/agent/startup.py` (`_spawned_subprocesses`, reference)

## Required Changes
- Make `terminate_with_timeout()` either raise the documented `HttpStartupError` or return an explicit
  three-state result; do not return `True` after a swallowed `OSError`.
- In `_terminate_one()`, act on the outcome: keep tracking entries when termination could not be delivered,
  and report the server as not terminated.
- Fix the malformed log call at `http_lifecycle_process_terminator.py:206`.
- Decide whether `AgentREPL` should retain the spawned-subprocess list it already receives, or whether the
  parameter should be removed from the `startup.run()` contract.

## Constraints
- Concurrent termination must stay concurrent: every server is signalled before any wait begins (the comment
  at `http_lifecycle_shutdown_coordinator.py:132` states this intent).
- `_SHUTDOWN_TIMEOUT_SEC` and the terminate/kill escalation order must not change.
- `_absorb_sigint_during_shutdown` and its restore in `finally` (`:98-146`) must keep working.
- `cleanup_server_key`'s contract with `http_lifecycle_health_checker.py:181` and
  `http_lifecycle_subprocess_launcher.py:144` must not break.

## Acceptance Criteria
- When `proc.terminate()` raises `OSError`, the shutdown reports that server as not terminated and its
  tracking entry is retained.
- No `except …: pass` path returns a success value.
- The log line at `:206` prints the pid.
- Either `_spawned_subprocesses` is used at the REPL level or it is removed from the startup return contract.

## Testing Expectations
- Regression tests per failure path: a stub `Popen` whose `terminate()` raises, asserting the failure is
  reported and tracking is retained; a stub that never exits within the timeout, asserting escalation still
  reports accurately.
- Use a stub process; do not spawn a real server, and keep timing margins wide.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document what a clean MCP shutdown means (terminated vs orphaned), what the operator sees when a server could
not be terminated, and the `start_new_session: True` consequence: force-killing the REPL leaves the servers
running. Record it in the operations docs as an operational note.

## Out of Scope
- Orphan prevention for `kill -9` of the REPL process (see `repl001`); only the reporting is in scope here.
- Startup timeout and health-check policy.
- The SIGINT guard during shutdown (see Unresolved Questions).

## Dependencies
- Related to `repl001` (force-kill is currently the only way out) and `turn005` (same shutdown coordinator).

## Unresolved Questions
- `shutdown_all()` replaces the SIGINT handler with `signal.signal()` while `SignalHandler` uses
  `loop.add_signal_handler()` (`scripts/agent/signal_handler.py:61-63`). Mixing the two mechanisms in one
  session needs a decision.
- Should the REPL refuse to report a clean exit when a server it started could not be terminated? Needs a
  product decision.

## AI Implementation Instruction
Make failure states distinct values instead of a bool that defaults to success. Do not change the escalation
algorithm.

## Traceability
- **Workflow phase**: `python-code-review` (startup/shutdown lifecycle review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/http_lifecycle_process_terminator.py`,
  `scripts/agent/http_lifecycle_shutdown_coordinator.py`, `scripts/agent/http_lifecycle.py`,
  `scripts/agent/repl.py`
