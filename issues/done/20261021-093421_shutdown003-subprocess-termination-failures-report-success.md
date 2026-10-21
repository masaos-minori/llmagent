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

### Verification (re-read at HEAD `d30bef5c3`, 2026-10-22)

Confirmed against the current tree:

- `terminate_with_timeout()` (`http_lifecycle_process_terminator.py:115-211`) has nine exits. Eight return
  `True`; the only `False` is `:208-211`, reached when `os.killpg(pgid, SIGKILL)` raises an `OSError` that is
  not `ProcessLookupError`. The file contains no `raise` statement at all (`grep -n "raise"
  scripts/agent/http_lifecycle_process_terminator.py` → no match), so the documented `Raises:
  HttpStartupError` (`:125-126`) never happens; `HttpStartupError` (`http_lifecycle_errors.py:28`) is raised
  only by the startup/health-check path.
- Success is reported on arms where no termination was observed: `:129-144` (no resolvable pgid: `proc
  .terminate()` errors are swallowed at `:142-143`, then `return True` with no wait and no exit check);
  `:168-180` (`os.killpg(SIGTERM)` raises `OSError`, the fallback is tried, `return True` although the
  graceful signal was never delivered); `:201-204` (after the wait deadline, `return True` on the *success* of
  the `os.killpg(SIGKILL)` call — signal delivery is reported as termination, and no post-kill confirmation
  exists); `:205-207` (`ProcessLookupError` on SIGKILL → `True`, and the malformed log at `:206` emits the
  literal `%d`). The only arms that confirm an exit are `:130-132` and `:147-149` (`_already_exited`,
  `:43-51`) and `:196-198` (`os.killpg(pgid, 0)` raising `ProcessLookupError` inside the poll loop,
  `:191-195`).
- `_terminate_one()` (`http_lifecycle_shutdown_coordinator.py:55-77`) never inspects the value:
  `manager.cleanup_server_key(server_key)` runs at `:69` for every non-exception return, so `True` and
  `False` are indistinguishable downstream. `except (OSError, TimeoutError)` (`:70`) can only be reached
  through `OSError` — the terminator raises no `TimeoutError`.
- The tracking entry is already gone before termination: `manager.remove_process_entry(server_key)` at `:122`
  (`http_lifecycle.py:170-177`, whose own docstring says "Called before termination to prevent double-shutdown
  if termination fails"). Therefore the log text at `:71-77` ("tracking entry retained for manual cleanup") is
  false. What is actually retained on that arm is `_http_pgids` and the stderr-log tracking, because
  `cleanup_server_key` (`http_lifecycle.py:158-168`) is the only thing that clears them.
- No termination result crosses a module boundary anywhere in the shutdown path:
  `ShutdownCoordinator.shutdown_all(...) -> None` (`:79-84`), `HttpServerLifecycleManager.shutdown_all() ->
  None` (`http_lifecycle.py:338-343`), `cleanup_server_key(...) -> None` (`:158`), `remove_process_entry(...)
  -> None` (`:170`), `_SubprocessLifecycleManager.shutdown_all() -> None` and the router's
  (`lifecycle_router.py:76-78`, `:254-256`), `ServerLifecycleProtocol.shutdown_all() -> None`
  (`lifecycle_protocol.py:35`), and `ResourceShutdownCoordinator.close_resources()` collects only exceptions
  (`resource_shutdown_coordinator.py:137-145`) and then logs a summary (`:149-151`). The only operator-visible
  trace of a failed termination is one `logger.error` line in `/opt/llm/logs/agent.log`.
- A primitive that already answers "did it exit" exists and is unused in production: `wait_exited()`
  (`:83-113`) polls the same liveness probe and returns `False` at `:113` when the deadline passes.
  `grep -rn "wait_exited" scripts/` → the definition and the comment at `:19` only; its only callers are
  `tests/agent/test_http_lifecycle_process_terminator.py:102` and `:257`.
- Four production call sites reach `terminate_with_timeout()` with three different timeouts and one implicit
  default: `timeout=_SHUTDOWN_TIMEOUT_SEC` = 30.0 (`coordinator.py:25`, read only at `:114`);
  `self._terminate_timeout_sec` = `TERMINATE_TIMEOUT_SEC: float = 5.0` (`http_lifecycle.py:57`, injected at
  `:103`, used at `http_lifecycle_subprocess_launcher.py:144-145`); `timeout=terminate_timeout_sec` = the same
  5.0 at `http_lifecycle_health_checker.py:181-182` (injected at `http_lifecycle.py:283`); and `restart()`
  (`http_lifecycle.py:332`) passes no timeout at all, so the signature default `timeout: float = 5.0` (`:116`)
  applies there. `_KILL_TIMEOUT_SEC = 5.0` (`coordinator.py:26`) has no read site. No configuration key exists
  (`grep -rn "termination_timeout" config/ scripts/` → no match).
- `_spawned_subprocesses` is confirmed dead at the REPL level: declared at `repl.py:123`, assigned by the
  unpacking at `:129-132`, never read again (`grep -n "_spawned_subprocesses" scripts/agent/repl.py` → those
  two lines only). It is produced by `startup_mcp_starter.py:49`, `:189`, `:117` and returned by
  `startup.py:73`, `:94`. It *is* used inside `McpServerStarter` and asserted by
  `tests/agent/test_startup_rollback.py:200`, `:220` and `tests/agent/test_startup_mcp_lifecycle.py:146`.
- `start_new_session: True` is confirmed at `http_lifecycle_subprocess_launcher.py:99`, and the two signal
  mechanisms the Unresolved Questions describe are both present: `loop.add_signal_handler`
  (`signal_handler.py:51-63`) versus `signal.signal(SIGINT, …)` with a `finally` restore
  (`coordinator.py:104-110`, `:141-146`).

Gaps between the issue text and HEAD:

- `_terminate_one()` is at `coordinator.py:55-77`, not `:133-141`; `:130-139` is the `asyncio.gather` that
  calls it. The concurrency constraint itself holds, and the comment the issue cites is at `:130-131`.
- `cleanup_server_key` is at `http_lifecycle.py:158-168` and returns `None`. The claim that it "discards
  `_http_procs` and `_http_pgids`" is accurate; there is simply no value to inspect.
- The Constraints' claim that `cleanup_server_key` has a contract with `http_lifecycle_health_checker.py:181`
  and `http_lifecycle_subprocess_launcher.py:144` is not true at HEAD: those two lines call
  `terminate_with_timeout`. `cleanup_server_key` has exactly two production call sites (`coordinator.py:69`,
  `coordinator.py:127`). What must not break is the `terminate_with_timeout` signature those two sites use.
- `restart()` does not call `shutdown_all()`; it calls the terminator directly with no timeout
  (`http_lifecycle.py:327-334`).
- The issue's framing "either raise the documented `HttpStartupError` or return an explicit three-state result"
  puts the fix inside the terminator. At HEAD the failure signal is destroyed one layer above, in
  `_terminate_one` and the `-> None` returns listed above: a three-state value that stays unconsumed would
  change no observable behavior. Both halves are needed.
- Existing coverage locks parts of the current contract, and several test names do not describe what they
  assert: `test_http_lifecycle_process_terminator.py:16 test_sigkill_failure_logs_error_and_returns_false`
  patches the whole `os` module so SIGTERM and SIGKILL both succeed, asserts only `killpg.call_count == 2`, and
  never asserts a return value — the failure in its name never occurs; `:117`, `:124`, `:140`, `:153` assert
  `result is True` for arms that confirm nothing;
  `test_http_lifecycle_shutdown_coordinator.py:13 test_tracking_entry_persists_on_termination_failure` asserts
  only `cleanup_server_key.assert_not_called()` and never observes the removal at `:122`; `test_lifecycle.py`
  `:969`, `:992`, `:1014`, `:1040` assert only which signals were sent. Real-child coverage exists in
  `test_http_lifecycle_process_terminator.py:231-277` (`_spawn`, `_cleanup`).
- The Testing Expectations say "do not spawn a real server", which contradicts the real-child harness already
  in this area. The real-child path is the only one that can demonstrate "no orphan remains"; the stub rule is
  kept for the signal-failure arms and recorded as a deviation in the Plan.

Answers to the Unresolved Questions:

- Which behavior is the contract today: signal-delivery-based. `True` means "a signal call did not fail", not
  "the process exited". The exit-confirmation judgment exists only in `wait_exited()` (`:83-113`), which no
  production path calls.
- Consumers of the returned value: none, in any module (see the `-> None` chain above). The observable contract
  today is: every shutdown is reported as clean, and the only trace of a failure is a log line.
- Mixing `loop.add_signal_handler` and `signal.signal` is real and belongs to `repl001`, which owns the
  shutdown-event wiring; this issue's scope is reporting only, consistent with its Out of Scope section.

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
