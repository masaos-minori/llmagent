## Goal

Add the red responsiveness tests that pin REQ-004 and REQ-005: a transport-failure write
and a serialization-event write must run off the event loop, keep their call-site ordering,
and release the loop while blocked — written first so they fail against the current
synchronous implementation and go green only after the seq 04/05 code changes (REQ-006(a);
AC-4, AC-5, AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `tests/agent/test_tool_runner.py` row (seq 08) of
`plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md`. This row is NOT
companion-eligible — the `scripts/agent/tool_runner.py` and `scripts/agent/tool_run_recorder.py`
rows both list it in their `Related Tests` cells (companion condition 2 fails) — so it has
its own document. Runs before
`implementations/20261103-113432_05_scripts_agent_tool_run_recorder.py.md` and
`implementations/20261103-113432_04_scripts_agent_tool_runner.py.md` (its tests are red
until both land in the same commit).

## Assumptions
- Verified against current source (20261103): the file already exercises the paths under
  test — `TestTransportFailureDiagnostics` (1900) drives `execute_one_tool_call` with a
  stubbed `ctx.services_required.tools.execute` returning a `ToolCallResult(error_type=
  "transport")` and asserts `save_transport_failure.assert_called_once_with(session_id=...,
  tool_name=..., server_key=..., error_msg=...)`; `test_tool_level_error_does_not_write_transport_diagnostics`
  (1931) pins the early-return; `test_side_effect_calls_diagnostic_save` (1663) drives a
  full `execute_all_tool_calls` round with `ctx.diagnostics = MagicMock()` and asserts
  `save_serialization_event` call kwargs; helpers `_make_ctx`, `_tc`, `_pc`, `_cfg`,
  `_write_registry` exist.
- No test calls `_record_transport_failure` or `_record_round_serialization_events`
  directly (rg 20261103), so making them coroutines breaks no existing test call (REQ-007).
- `inflightcancel001`, `wfretry001`, `maskargs001` and `toolarg001` share this file; all four
  plans are archived under `plans/done/` with their code on master (re-verified 20261103),
  satisfying the Plan's "after toolarg001" sequencing. `inflightcancel001`'s remaining work in
  this file is its Pending procedure
  `implementations/20261103-121149_04_scripts_agent_tool_runner.py.md` (its test row is
  companion-eligible), which lands after this document; both sides only append new test
  functions and imports — no edits to shared helpers (Plan Risks mitigation).
- Plan REQ-006(a) mechanism constraint: the stub blocks the worker thread via a
  `threading.Event`; never `time.sleep` on the loop.

## Design decisions
- Block on `threading.Event` inside the diagnostic stub and prove loop freedom with a
  callback scheduled via `loop.call_soon` that sets a flag while the write is blocked
  (Plan REQ-006(a) wording), with a generous `Event.wait(timeout=...)`-style release in a
  `finally` so a failed assertion never hangs the suite.
- Ordering proofs use a `MagicMock` manager (or explicit call-order list appended from the
  stubs) instead of timing assertions: `save_transport_failure` completes before
  `guard.observe_availability` runs; the awaited serialization save completes before the
  mocked `_record_round_exec` runs.

## Alternatives considered
- Asserting only that `asyncio.to_thread` is called (patching it): rejected — it pins the
  mechanism, not the observable loop-freedom and ordering the ACs state; the Plan's Tests
  section prescribes the blocking-stub pattern.

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
1. Add a `TestDiagnosticWritesOffEventLoop` (new) class with three tests, following the
   fixture patterns above:
   - `test_transport_failure_write_off_loop` (new): `_make_ctx()` with
     `ctx.diagnostics.save_transport_failure` stubbed to record the call, block on a
     `threading.Event` (worker thread only) and record release; run `execute_one_tool_call`
     (imported at test_tool_runner.py:33) as a task with the transport-error stub registry
     (pattern from 1900-1927) and a `MagicMock` guard; assert a `loop.call_soon` callback
     fired while the write is blocked, `guard.observe_availability` was not yet called, and
     after `Event.set()` the task completes and the early-return tests' kwargs assertions
     still hold (REQ-004, REQ-006(a); AC-4, AC-6).
   - `test_non_transport_results_touch_no_diagnostics` (new): non-error and tool-level-error
     results leave `save_transport_failure` uncalled (REQ-004 unchanged early returns;
     AC-4 last clause) — mirrors the existing 1931 test but through the same new class for
     the post-change contract.
   - `test_serialization_event_write_off_loop` (new): the 1663 fixture pattern
     (`serial_tool_calls=True`, `_write_registry`, patched `run_approval_checks`,
     `ctx.diagnostics = MagicMock`) with `save_serialization_event` stubbed to block on a
     `threading.Event`; patch `agent.tool_runner._record_round_exec` with a recording mock;
     run `execute_all_tool_calls` as a task; assert the loop callback fires while the write
     is blocked, `ctx.stats.stat_serialization_events` already has its entry (stats stayed
     on the loop thread), the save completed before `_record_round_exec` was called, and
     after release every serialization event produced exactly one save call in event order
     (REQ-005, REQ-006(a); AC-5, AC-6).
2. Confirm all new tests fail against the current synchronous implementation (the loop
   callback cannot fire while a synchronous write blocks the loop).
3. Hand off: they turn green only after the seq 05 + seq 04 changes land in one commit; do
   not mark this document complete before running Validation plan 2 on the green suite.

### Method
Add-only: one new test class and (if not already present) a `threading` import at the file
top; no edits to existing tests or shared helpers (collision mitigation for the three other
Plans sharing this file).

### Details
- Stub shape: `def blocking_save(*args, **kwargs): calls.append(...); event.wait(5);
  ...` recording completion timestamps/order into a shared list read by the assertions.
- Task lifecycle: `asyncio.create_task` + `await asyncio.wait_for(task, timeout=...)`-style
  awaiting inside the test's loop; set the event in `finally` every time.
- The guard for the transport test: a `MagicMock` (the parameter only needs
  `observe_availability`/`record_tool_result`), matching how neighboring tests pass
  `ToolLoopGuard(ctx)` or mocks.

## Compatibility considerations
- Existing tests in the file stay byte-identical (REQ-007); the new class must not mutate
  shared helpers (Plan Risks).
- Test-only change: nothing to deploy; no `docs/` or manifest impact.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
1. `uv run pytest tests/agent/test_tool_runner.py -q` — new tests red at Procedure 2;
   after seq 05 + seq 04 land, all green; existing transport/serialization tests unchanged.
2. After the code documents land: `uv run pytest tests/agent/test_tool_runner.py
   tests/agent/commands/test_cmd_mcp.py tests/agent/test_orchestrator.py
   tests/integration/test_robustness_chaos.py -q` (Plan Validation rows 3-4 regression set).
3. Determinism: run the new class 3x (`uv run pytest tests/agent/test_tool_runner.py -q -k
   TestDiagnosticWritesOffEventLoop --count 2` if the repeat plugin is configured, else two
   consecutive runs) to rule out flakiness from thread timing (never sleeps on the loop).
4. `uv run ruff check tests/agent/test_tool_runner.py`, `uv run ruff format --check`,
   `uv run mypy tests/agent/test_tool_runner.py`.

## Completion criteria
- AC-6 for AC-4/AC-5: each new test demonstrates a loop callback firing while the stubbed
  write is blocked and the awaiting coroutine finishing only after release.
- AC-4/AC-5 ordering halves: observe-after-write and save-before-`_record_round_exec`
  assertions hold after the code changes.
- The file's existing tests pass unchanged (REQ-007).

## Out of Scope
- The production offload changes (seq 04/05) and the guard/runner tests (seq 01/03
  companions).
- `tool_call_state` recorder writes (UNK-03) and containment (UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestDiagnosticWritesOffEventLoop` (new) tests and confirm they fail (Procedure 1-2) | Pending | — | — | |
| 2 | After seq 04+05 land: confirm green and run the determinism/regression checks (Procedure 3; Validation plan 2-4) | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (responsiveness tests for REQ-004/REQ-005 with blocking
  stubs), REQ-004/REQ-005 (the offloaded behaviors these tests pin)
- **Source issue**: issues/20261003-180333_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-113432
- **Related target files**: `tests/agent/test_tool_runner.py`
