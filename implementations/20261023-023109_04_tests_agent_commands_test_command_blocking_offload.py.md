## Goal

Add a new behavior-lock file proving that, once `/session` storage work is offloaded
(row 02), a concurrent coroutine on the same event loop advances while a long storage
callable is running (loop responsiveness, AC-3), and that cancelling/abandoning the await
does not stop the running callable (completion semantics, AC-5).

## Scope

New file `tests/agent/commands/test_command_blocking_offload.py` (Create). Drives
`await cmd._cmd_session("vacuum")` with `DbMaintenanceService` stubbed, exactly as
`tests/agent/commands/test_agent_cmd_session.py:509-600` does. No production file modified.

## Assumptions

- `cmd._cmd_session` is the awaited entry point for the `/session` maintenance group
  (`cmd_session.py:_cmd_session`), reached through the `db_dispatch` table converted to
  awaitables by row 02.
- `tests/agent/commands/test_agent_cmd_session.py` constructs a command via `_make_cmd()`
  and patches `agent.commands.db_session_ops.DbMaintenanceService`; this file reuses that
  pattern.
- The storage call opens and closes its own SQLite connection inside the call
  (`db_maintenance_service.py:35`), so running it on a worker thread is valid (REQ-004).

## Design decisions

- **Event-based blocking, not sleep.** The stub blocks on a `threading.Event`/`asyncio.Event`
  pair instead of `time.sleep`, so the tests are deterministic and free of tight timing
  assertions (plan Tests).
- **Two independent assertions:**
  1. `test_loop_advances_while_storage_runs`: schedule a probe coroutine alongside
     `cmd._cmd_session("vacuum")` via `asyncio.gather`; assert the probe completed its
     iterations while the storage call was blocked on the event (proves the loop was not
     held — AC-3).
  2. `test_await_cancel_does_not_stop_work`: start `cmd._cmd_session("vacuum")` as a task,
     cancel/abandon the await, then assert the stubbed callable still completed and its
     effect was observed before the loop returns (AC-5).
- **Generous margins.** Any timing-adjacent assertions use wide margins; the event-based
  signaling is the real contract.

## Alternatives considered

- **Assert `asyncio.to_thread` was called (patch it).** Rejected: couples the test to the
  exact offload mechanism; the behavioral probe (loop responsiveness + work completion) is
  more robust and matches AC-3/AC-5 wording.
- **Drive via `db_dispatch` CLI context.** Rejected: heavier to construct and bypasses
  `cmd._cmd_session`; the coroutine entry point is the contract under test.

## Implementation
### Target file
`tests/agent/commands/test_command_blocking_offload.py` (Create)

### Procedure
1. Create `tests/agent/commands/test_command_blocking_offload.py`.
2. Mirror `tests/agent/commands/test_agent_cmd_session.py`'s driving pattern: import the
   same patch targets, build the command via the same constructor / `_make_cmd()` helper
   (copy the construction from `test_agent_cmd_session.py`), and patch
   `agent.commands.db_session_ops.DbMaintenanceService` so the storage call resolves to a
   controllable stub.
3. Write `test_loop_advances_while_storage_runs`:
   - The stub sets an `asyncio.Event` when it starts and blocks on a `threading.Event`.
   - `asyncio.gather` the stub-driven `await cmd._cmd_session("vacuum")` with a probe
     coroutine that awaits `asyncio.sleep(0)` repeatedly until the start event is set,
     counting iterations.
   - Assert the probe made progress (loop stayed responsive) and then release the
     `threading.Event` so the call completes.
4. Write `test_await_cancel_does_not_stop_work`:
   - Launch `task = asyncio.create_task(cmd._cmd_session("vacuum"))`, let the stub start,
     then cancel the await (or abandon it) and assert the stub still ran to completion and
     its side effect (e.g. the patched method's call count) is observed.
5. Use generous margins; keep assertions event-driven.

### Method
- `pytest` + `asyncio` + `threading`/`asyncio.Event`. Reuse whatever async support
  `test_agent_cmd_session.py` already uses (conftest/plugin); do not add a new fixture.
- Offload proof = the probe coroutine advances while the stub blocks; a synchronous/on-loop
  call would starve it.
- Completion-semantics proof = the stub completes despite the cancelled await, matching the
  documented `asyncio.run()` joins-worker behavior (REQ-006).

### Details
- The stub must return the same value the real callable returns for `vacuum` so success
  output is unchanged (REQ-005 / AC-4): model it on the existing purge/vacuum stubs in
  `test_agent_cmd_session.py`.
- Do not assert that the storage call was interrupted — AC-5 forbids that; assert the
  opposite (it finished).
- Keep the `sqlite3.Error` propagation intact if the test exercises an error path (as
  `test_agent_cmd_session.py:497-503` does for `vacuum`); offloading must not swallow
  exceptions (AC-4).
- New file only; no other file modified.

## Compatibility considerations

New test file only. Depends on row 02's offload; without it the responsiveness test fails
(by design), which is the regression guard.

## Security considerations

No security impact: pure unit test, no network/shell/secrets.

## Rollback considerations

Delete the single new file. Nothing else references it.

## Validation plan

1. `uv run pytest tests/agent/commands/test_command_blocking_offload.py -v` passes against
   the row-02 offload.
2. Confirm it FAILS against the pre-offload inline call (row 02 reverted) — this is the
   regression signal (AC-3).
3. Broader suite: `uv run pytest tests/agent/commands/test_command_blocking_offload.py
   tests/agent/commands/test_agent_cmd_session.py -v` (AC-4).

## Completion criteria

- `test_command_blocking_offload.py` exists; loop-responsiveness (AC-3) and
  completion-semantics (AC-5) tests pass against the offloaded code.
- The responsiveness test fails against the inline (pre-offload) call.
- Existing `/session` tests (incl. `sqlite3.Error` cases) still pass (AC-4).

## Out of Scope

- Testing cancellation/interruption (forbidden by AC-5).
- The offload implementation itself (row 02, `cmd_session.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-006
- **Source issue**: issues/done/20261021-093421_cmd003-commands-block-the-event-loop-and-are-uncancellable.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-020701_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-023109
- **Related target files**: tests/agent/commands/test_command_blocking_offload.py
