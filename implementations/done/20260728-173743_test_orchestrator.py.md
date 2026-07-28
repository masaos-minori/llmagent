## Goal

Ensure a `WorkflowTimeoutError` raised by `WorkflowEngine` during a stage timeout is caught by `Orchestrator._handle_workflow_engine()` and never propagates uncaught to the REPL loop, and add test coverage that exercises this end-to-end (a real short `timeout_sec` triggering the exception through the actual `WorkflowEngine.run()` path, not just a mocked side effect), confirming `handle_turn()` returns normally and the user receives a visible notification.

## Scope

**In-Scope:**
- Verify (before/while implementing) that `scripts/agent/orchestrator.py`'s `_handle_workflow_engine()` except clause is widened to `except (WorkflowHaltError, WorkflowTimeoutError) as exc:` routed through `_handle_workflow_halt(exc)`, with `engine_status_handled` set `True` on that branch — this exact change is already fully specified by `plans/20260727-142940_plan.md` (source requirement `requires/done/20260727-132533_require.md`). This plan does not redefine that change; it depends on it.
- Add new test(s) to `tests/test_orchestrator.py` that exercise a **genuine** `WorkflowTimeoutError` (via a `WorkflowDef`/`StageDefinition` with a very short `timeout_sec`, mirroring the pattern already used in `tests/test_workflow_engine.py:181-186`) driven through the real `WorkflowEngine.run()` call inside `_handle_workflow_engine()`, asserting:
  - `Orchestrator.handle_turn()` returns normally (does not raise).
  - `self._on_error` was invoked with the `WorkflowTimeoutError` instance (user-facing notification path).
  - The task's final DB status is `"halted"`, not overwritten to `"completed"`.
- Optionally add a lightweight REPL-level regression test driving `_dispatch_line()` with a stubbed orchestrator whose `handle_turn()` raises `WorkflowTimeoutError`, asserting `_repl_loop()` does not terminate and proceeds to read the next line (per the source requirement's "if feasible" test note).

**Out-of-Scope:**
- Any change to `scripts/agent/orchestrator.py`'s except clause, `engine_status_handled` flag, or `_handle_workflow_halt()` type hint — already fully covered by `plans/20260727-142940_plan.md`. Do not duplicate this fix; implementing that plan is a prerequisite for this one.
- Any change to `scripts/agent/workflow/workflow_engine.py` — confirmed by direct read that `run()` (lines 126-154) already catches `(WorkflowHaltError, WorkflowTimeoutError)` together, sets status `"halted"`, and re-raises; `_run_stage_with_retry()` (lines 262-284) already converts a real `asyncio.wait_for` `TimeoutError` into `WorkflowTimeoutError` correctly. No engine change needed.
- Introducing a distinct `"timed_out"` task status separate from `"halted"` — the source requirement's Implementation Instructions (item 4) explicitly leave this as an implementer's judgment call, and `plans/20260727-142940_plan.md` already resolved it by keeping `"halted"` for both exception types. Not revisited here.
- Adding a separate `_handle_workflow_timeout()` handler distinct from `_handle_workflow_halt()` — the source requirement's Implementation Intent explicitly permits reusing the halt handler "if a timeout should be treated identically to a halt from the user's perspective"; `plans/20260727-142940_plan.md` made that choice. Not revisited here.
- Changes to `scripts/agent/repl.py` — no changes needed. Once `WorkflowTimeoutError` no longer escapes `handle_turn()`, `_dispatch_line()`/`_repl_loop()`/`_run_repl_loop()` (lines 575-591, 462-502, 617-649) continue exactly as today; these were read as reference to confirm the current (bug) propagation path, not as an edit target.

## Assumptions

1. `plans/20260727-142940_plan.md` will be implemented essentially as written (except clause widened to `except (WorkflowHaltError, WorkflowTimeoutError) as exc:`, `engine_status_handled` guard added). If its implementation deviates in structure (e.g., a separate `except WorkflowTimeoutError` clause instead of a tuple), the test additions proposed here remain valid unchanged, since they assert only externally observable behavior (`handle_turn()` does not raise, `_on_error` is called, status is `"halted"`), not internal implementation shape.
2. `self._on_error: Callable[[Exception], None] | None` (`orchestrator.py` lines 131, 144) accepts any `Exception` subtype — confirmed by direct read; passing a `WorkflowTimeoutError` instance (itself `class WorkflowTimeoutError(Exception)`, `workflow_engine.py:81-82`) requires no signature or type-hint change anywhere.
3. Confirmed by direct read of the current (pre-fix) `scripts/agent/orchestrator.py:290-294` that `WorkflowTimeoutError` is caught by neither `except WorkflowPendingApprovalError` nor `except WorkflowHaltError` today — the bug described in the source requirement is real and reproducible in the current codebase, and the `finally` block (lines 295-303) would today incorrectly write `"completed"` over the engine's `"halted"` status on the way out, since `WorkflowTimeoutError` is not a `WorkflowHaltError`.
4. `tests/test_workflow_engine.py:181-186` already demonstrates constructing a `WorkflowDef`/`StageDefinition` with `timeout_sec=1` on the `execute` stage to deterministically trigger a real `WorkflowTimeoutError` in a test (not a mocked side effect). This plan's new orchestrator-level test reuses that same construction pattern but drives it through `Orchestrator._handle_workflow_engine()` / `handle_turn()` instead of calling `WorkflowEngine.run()` directly, which is a materially different (and currently missing) test scenario from the mocked-`side_effect` test already listed in `plans/20260727-142940_plan.md`'s Phase 3.
5. This is a document-only planning cycle; the sibling plan (`plans/20260727-142940_plan.md`) has not yet been implemented (it remains under `plans/`, not `plans/done/`) at the time this plan was written, so both plans' implementation steps must be sequenced — this plan's code-adjacent test additions should land in the same implementation pass as, or immediately after, that plan's fix, not before.

## Design decisions

- Add a genuine-timeout test using a real `WorkflowDef` with `timeout_sec=0.01` to drive through `WorkflowEngine.run()` rather than mocking `side_effect`.
- Assert three things: `handle_turn()` returns normally, `_on_error` is called with the `WorkflowTimeoutError`, and task status is `"halted"`.
- Include optional REPL-level regression test if existing fixtures make it cheap.

## Alternatives considered

- Use a mocked `side_effect` to raise `WorkflowTimeoutError` directly. Rejected — insufficient per requirement; the requirement specifically asks for a genuine timeout through the real `WorkflowEngine.run()` path, not just a mocked side effect.
- Create a separate `_handle_workflow_timeout()` handler. Rejected — the sibling plan already resolved this by reusing `_handle_workflow_halt()` for both exception types.

## Implementation

### Target file

- `tests/test_orchestrator.py` — add new test(s) for the genuine-timeout end-to-end path
- Optionally a new REPL-level test section if added per UNK-02

### Procedure

1. Confirm `plans/20260727-142940_plan.md` has been implemented (grep `scripts/agent/orchestrator.py` for `except (WorkflowHaltError, WorkflowTimeoutError)`); if not yet implemented, coordinate so this plan's tests are added in the same implementation pass as that fix.
2. Re-read `tests/test_orchestrator.py`'s existing fixtures (`_make_ctx()`, `_make_orchestrator()`, the autouse `_patch_workflow_loader()` fixture) and `tests/test_workflow_engine.py:181-210` (the short-`timeout_sec` `WorkflowDef` construction pattern) immediately before writing new tests, to reuse them rather than re-deriving equivalent fixtures.
3. In `tests/test_orchestrator.py`, add a test that builds a `WorkflowDef` with a stage `timeout_sec` short enough (e.g. `timeout_sec=0.01`) to guarantee `asyncio.wait_for` expiry, wires it into the orchestrator's real `WorkflowEngine` (not a mocked `run()`), calls `await orchestrator.handle_turn(line)`, and asserts:
   - the call returns without raising `WorkflowTimeoutError` or any other exception,
   - `self._on_error` (or the test's `on_error` stub) was called exactly once with a `WorkflowTimeoutError` instance,
   - the task's status read back from the store is `"halted"`.
4. Optionally add a REPL-level test (per UNK-02) that stubs `orchestrator.handle_turn` to raise `WorkflowTimeoutError`, drives it through `_dispatch_line()`, and asserts the exception does not propagate out of `_dispatch_line()`/`_repl_loop()` — document in a comment that this is a regression guard for the layer above the fix, not a test of the fix itself.
5. Run `uv run pytest tests/test_orchestrator.py -k timeout -q` and confirm the new test(s) pass once `plans/20260727-142940_plan.md`'s fix is applied (and fail — demonstrating the bug — if run against unfixed `orchestrator.py`, as a sanity check of test validity).
6. Run `uv run pytest tests/test_orchestrator.py tests/test_workflow_engine.py -q` to confirm no regressions.
7. Run `uv run ruff check tests/test_orchestrator.py` and `uv run mypy tests/test_orchestrator.py` to confirm no new lint/type errors.
8. No deploy step required; test-only change.

### Method

- Direct test addition using existing fixtures (`_make_ctx()`, `_make_orchestrator()`, `_patch_workflow_loader()`).
- Reuse the short-`timeout_sec` `WorkflowDef` construction pattern from `tests/test_workflow_engine.py:181-186`.

### Details

```python
# New test in tests/test_orchestrator.py
def test_handle_turn_returns_normally_on_genuine_workflow_timeout(self):
    """When WorkflowEngine.run() raises WorkflowTimeoutError via a real asyncio.wait_for timeout, handle_turn() must return normally."""
    # Build a WorkflowDef with a stage having timeout_sec=0.01
    # Wire it into the orchestrator's real WorkflowEngine (not mocked)
    # Call await orchestrator.handle_turn(line)
    # Assert:
    #   1. No exception raised from handle_turn()
    #   2. self._on_error was called exactly once with a WorkflowTimeoutError instance
    #   3. Task status read back from store is "halted", not "completed"
```

```python
# Optional REPL-level regression test (per UNK-02)
def test_dispatch_line_does_not_propagate_workflow_timeout_to_repl_loop(self):
    """Regression guard: _dispatch_line() must not let WorkflowTimeoutError escape to _repl_loop()."""
    # Stub orchestrator.handle_turn to raise WorkflowTimeoutError
    # Drive through _dispatch_line()
    # Assert loop does not terminate; proceeds to next input
    # NOTE: This is a regression guard for the layer above the fix, not a test of the fix itself.
```

Exception path behavior:
- On genuine `WorkflowTimeoutError`: `handle_turn()` returns normally, `_on_error` is invoked, task status is `"halted"`.
- On any other uncaught exception: continues to propagate (unchanged).

## Compatibility considerations

- Test-only change; no runtime code touched by this plan. Zero production blast radius.
- Depends on `plans/20260727-142940_plan.md` landing first (or in the same change) for the new tests to pass — if that plan's fix is not applied, the genuine-timeout test added here will fail (correctly demonstrating the bug), which is an acceptable and expected interim state if the two plans' implementation cycles are sequenced independently.

## Security considerations

N/A — test-only change; no authentication, authorization, or data exposure changes.

## Rollback considerations

- Simple revert: remove the new test(s) from `tests/test_orchestrator.py`.
- Low blast radius: test-only change; no code paths affected.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/orchestrator.py::_handle_workflow_engine` (via `handle_turn`) | Integration — real short-`timeout_sec` stage triggers genuine `WorkflowTimeoutError` through `WorkflowEngine.run()` | `uv run pytest tests/test_orchestrator.py -k timeout -q` | `handle_turn()` returns normally; `_on_error` invoked with `WorkflowTimeoutError`; task status is `halted` |
| `scripts/agent/repl.py::_dispatch_line`/`_repl_loop` (optional) | Unit — stubbed orchestrator raising `WorkflowTimeoutError` | `uv run pytest tests/test_orchestrator.py -k repl_timeout -q` (or a new test module) | Loop does not terminate; proceeds to next input |
| Full orchestrator + workflow_engine suite | Regression | `uv run pytest tests/test_orchestrator.py tests/test_workflow_engine.py -q` | No new failures |
| Test file lint/type | Static analysis | `uv run ruff check tests/test_orchestrator.py` and `uv run mypy tests/test_orchestrator.py` | 0 new errors |

## Out of scope

- Any change to `scripts/agent/orchestrator.py`'s except clause, `engine_status_handled` flag, or `_handle_workflow_halt()` type hint.
- Changes to `scripts/agent/workflow/workflow_engine.py`.
- Introducing a distinct `"timed_out"` task status.
- Adding a separate `_handle_workflow_timeout()` handler.
- Changes to `scripts/agent/repl.py`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260727-133021_require.md
- Source plan: plans/20260727-144112_plan.md
- Source implementation procedure: N/A
- Generated at: 20260728-173743
- Related target files: scripts/agent/orchestrator.py, scripts/agent/workflow/workflow_engine.py, scripts/agent/repl.py, tests/test_orchestrator.py
