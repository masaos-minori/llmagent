## Goal

Add regression coverage for the background-failure pause resume path: a same-type clean
completion clears the pause, a cancellation does not, and a different task name's success
does not (REQ-1, REQ-4; REQ-2 keeps the breach-set behavior green via the existing
characterization tests).

## Scope

- New test class and cases in `tests/agent/test_orchestrator_bg_failure_threshold.py`.
- Existing tests in this module are not modified.
- The orchestrator-level pause characterization tests in `tests/agent/test_orchestrator.py`
  are reference only and stay untouched.

## Assumptions

- The cleared-pause assertions depend on the behavior created by the seq 01 procedure
  document (`scripts/agent/bg_task_monitor.py` clean-completion clear); run seq 01
  first — `code-implementation` executes documents in seq order.
- Module convention: these are unit-level tests driving `BgTaskMonitor` directly with a
  `MagicMock` ctx (existing `_make_ctx`, `_await_raising`, `_make_cancelled` helpers), not
  orchestrator integration tests.
- `tests/agent/test_orchestrator.py` already characterizes breach-set/pause-disabled at
  the orchestrator level (L2529-2609); this module only adds the resume-path cases.

## Design decisions

- Reuse the module's existing direct-monitor pattern and helpers; add one new helper
  `_await_ok` (new) mirroring `_await_raising` for a task that completes cleanly, so
  `on_task_done` observes `task.exception() is None` without the body escaping the helper.
- Assert both observable surfaces the blocking consumer uses: the `bg_pause_state`
  property and `check_pause_state()` returning `(False, [])`.

## Alternatives considered

- Adding the cases to `tests/agent/test_orchestrator.py`: rejected — the Plan's frozen
  target row names this module, and the monitor-level resume semantics do not need the
  orchestrator harness.
- Reaching into `_bg_pause_state` directly: rejected — use the public `bg_pause_state`
  property and `check_pause_state()` contract, matching existing assertions.

## Implementation

### Target file

`tests/agent/test_orchestrator_bg_failure_threshold.py`

### Procedure

Add a `TestPauseResumePath` (new) class with three async cases and the `_await_ok` (new)
helper, exercising a monitor built with `pause_on_critical_failure=True`.

### Method

1. `_await_ok` (new): create `asyncio.create_task(_ok_task(), name=name)` whose body
   returns normally, `await asyncio.sleep(0)` once so the body finishes, return the
   finished task. `_ok_task` (new) is the trivial non-raising coroutine body.
2. Common breach setup: `monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None, pause_on_critical_failure=True)`;
   loop `for i in range(BG_FAILURE_THRESHOLD): monitor.on_task_done(await _await_raising(f"error {i}", "bg_task_0"))`;
   then assert `monitor.bg_pause_state == {"bg_task_0": True}` (precondition).
3. `test_clean_completion_after_breach_clears_pause` (new): breach, then
   `monitor.on_task_done(await _await_ok("bg_task_0"))`; assert
   `monitor.bg_pause_state == {}` and `monitor.check_pause_state() == (False, [])`.
4. `test_cancelled_task_after_breach_keeps_pause` (new): breach on `"bg_task_0"`, then
   `monitor.on_task_done(await _make_cancelled("bg_task_0"))`; assert
   `monitor.bg_pause_state == {"bg_task_0": True}`.
5. `test_other_task_success_after_breach_keeps_pause` (new): breach on `"bg_task_0"`,
   then `monitor.on_task_done(await _await_ok("other_task"))`; assert
   `monitor.bg_pause_state == {"bg_task_0": True}` and
   `monitor.check_pause_state() == (True, ["bg_task_0"])`.

### Details

- Follow the module's existing style: `@pytest.mark.asyncio`, `tasks: set[asyncio.Task[object]] = set()`,
  `_make_ctx()` per test; no logging handlers needed (pause assertions read state, not logs).
- `_make_cancelled` already awaits the cancellation and asserts `task.cancelled()`; reuse
  it unchanged.
- No changes to imports beyond what the new helper needs (none new: `asyncio` already imported).

## Compatibility considerations

- New cases depend on the seq 01 code change; before it lands, case 3 fails by design
  (that is the regression being locked in).
- Existing cases in this module and the orchestrator pause characterization tests must
  stay green unchanged (REQ-2).

## Security considerations

N/A: test-only change on an in-memory monitor with mocked context.

## Rollback considerations

N/A: revert the commit (test additions only).

## Validation plan

| Check | Command | Expected |
|-------|---------|----------|
| targeted resume tests | `uv run pytest tests/agent/test_orchestrator_bg_failure_threshold.py` | all green (after seq 01 lands) |
| existing pause characterization | `uv run pytest tests/agent/test_orchestrator.py -k "pause or threshold or failure"` | green, no test edited |
| full suite | `uv run pytest` | green |
| lint/type | `uv run ruff check . && uv run ruff format --check . && uv run mypy scripts/` | clean |

## Completion criteria

- Breach → paused → same-type clean completion → `check_pause_state()` returns
  `(False, [])` is asserted green (REQ-1, REQ-4).
- Cancellation-after-breach and other-name-success-after-breach keep the pause, asserted
  green (REQ-2 boundary cases).
- No existing test in either module was edited (REQ-2).

## Out of Scope

- Modifications to `scripts/agent/bg_task_monitor.py` (seq 01 document) or
  `tests/agent/test_orchestrator.py`.
- Orchestrator end-to-end pause-guard tests (`TestHandleTurnPauseGuard` already covers
  the blocking side).
- Documentation updates (seq 03 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestPauseResumePath` (new) and `_await_ok` (new) per Procedure/Method | Completed | 20261028-122500 | 20261028-122833 | Depends on the seq 01 code change for case 3 to pass Added TestPauseResumePath (3 cases) and _await_ok helper; ruff clean |
| 2 | Run targeted pytest (this module + `test_orchestrator.py -k "pause or threshold or failure"`) | Completed | 20261028-122500 | 20261028-122833 | 13 passed incl. 3 new TestPauseResumePath cases |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-122500 | 20261028-122833 | ruff clean; full suite 10300 passed; diff-cover 100% on bg_task_monitor.py changed line |

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
- **Requirement ID**: `REQ-1` (clean completion clears the pause entry), `REQ-2` (existing breach-set/disable behaviors unchanged), `REQ-4` (resume-path regression tests)
- **Source issue**: `issues/20261026-225036_bgmonitor001_reset-background-failure-pause.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-085246_bgmonitor001_reset-background-failure-pause.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-235926
- **Related target files**: `tests/agent/test_orchestrator_bg_failure_threshold.py`