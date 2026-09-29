## Goal
Rewrite `TestAllowedToolsOverride::test_original_config_restored_even_on_error` to
assert the workflow-engine halt outcome instead of expecting a raised `RuntimeError`
(REQ-001).

## Scope
- **In-Scope**: The single test method `test_original_config_restored_even_on_error`
  (`tests/agent/test_orchestrator.py:1267-1283`) only.
- **Out-of-Scope**: `scripts/agent/workflow/workflow_engine.py`,
  `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/orchestrator.py`
  (investigation confirmed their retry/halt behavior is intentional; not modified);
  the two adjacent tests in the same class (the "restored after turn" and
  "none leaves config unchanged" cases) and their separate, out-of-scope
  dead-patch observation (Plan Background).

## Assumptions
- Passing an `on_error=MagicMock()` callback to `Orchestrator(...)` is a safe,
  representative way to observe the halt (Plan Assumptions) — consistent with how
  `on_error` is already threaded through `scripts/agent/orchestrator.py`.
- `MagicMock` is already imported in this test file (used elsewhere, e.g.
  `orch._diagnostic_store = MagicMock()` in this same test) — no new import needed.

## Design decisions
- Keep the existing `side_effect=_raise` injection on
  `orch._conversation_manager.handle_memory_injection` unchanged — it already
  correctly targets the real call path (per Plan Background); only the assertions
  after the `await orch.handle_turn("test")` call change (per `skills/python-design`
  — smallest change that restores correct coverage, no new fixture/helper needed).
- Assert on the `on_error` callback's captured `WorkflowHaltError` (checking its
  exception-chain cause is the original `RuntimeError`) in addition to `ctx.workflow.active is
  False`, rather than either alone — per Plan Acceptance Criterion AC-2, the test
  must still fail if the halt path itself regresses, and a single state-flag check
  alone would not distinguish "halted for the right reason" from "halted for any
  reason."

## Alternatives considered
- Assert only `ctx.workflow.active is False` without the `on_error` callback check —
  rejected: per Plan Risk mitigation, this alone would not confirm the halt happened
  because of the injected `RuntimeError` specifically (AC-2).
- Catch `WorkflowHaltError` directly with `pytest.raises` around the `handle_turn()` call —
  rejected: the adapter's halt handler catches and handles `WorkflowHaltError` itself
  and does not re-raise it (confirmed via direct read of
  `scripts/agent/workflow_engine_adapter.py`), so `pytest.raises` would fail the same
  way the original `RuntimeError` expectation does.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure
1. Add an `on_error = MagicMock()` local variable and pass `on_error=on_error` to the
   `Orchestrator(...)` constructor call.
2. Replace `with pytest.raises(RuntimeError): await orch.handle_turn("test")` with a
   plain `await orch.handle_turn("test")` (no exception expected).
3. After the existing `assert ctx.cfg.tool.allowed_tools == []` line, add assertions
   confirming the halt was observed: `ctx.workflow.active is False`, `on_error`
   called exactly once with a `WorkflowHaltError` whose exception-chain cause is the
   original `RuntimeError`.

### Method
Direct text edit to one test method — no new fixtures, helpers, or imports beyond
what the file already has (`WorkflowHaltError` is already imported at
`tests/agent/test_orchestrator.py:21-25`; `MagicMock` is already used in this same
test).

### Details
Current test body (confirmed via direct read, lines 1267-1283):
```
    async def test_original_config_restored_even_on_error(self) -> None:
        """ctx.cfg.tool.allowed_tools is restored even when an exception propagates."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = []
        orch = Orchestrator(ctx, allowed_tools=["search_web"])
        orch._diagnostic_store = MagicMock()

        async def _raise(*_: object, **__: object) -> None:
            raise RuntimeError("unexpected error")

        with patch.object(
            orch._conversation_manager, "handle_memory_injection", side_effect=_raise
        ):
            with pytest.raises(RuntimeError):
                await orch.handle_turn("test")

        assert ctx.cfg.tool.allowed_tools == []
```

New test body — replace the `pytest.raises` expectation with halt-outcome
assertions:
```
    async def test_original_config_restored_even_on_error(self) -> None:
        """ctx.cfg.tool.allowed_tools is restored, and the halt is observable via
        on_error, when the workflow engine halts the turn after retries are
        exhausted."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = []
        on_error = MagicMock()
        orch = Orchestrator(ctx, allowed_tools=["search_web"], on_error=on_error)
        orch._diagnostic_store = MagicMock()

        async def _raise(*_: object, **__: object) -> None:
            raise RuntimeError("unexpected error")

        with patch.object(
            orch._conversation_manager, "handle_memory_injection", side_effect=_raise
        ):
            await orch.handle_turn("test")

        assert ctx.cfg.tool.allowed_tools == []
        assert ctx.workflow.active is False
        on_error.assert_called_once()
        (halt_exc,), _ = on_error.call_args
        assert isinstance(halt_exc, WorkflowHaltError)
        assert isinstance(halt_exc.__cause__, RuntimeError)
```

Do not change `_make_ctx()`, the `_raise` helper, or the `patch.object(...)` target —
only the constructor call and the assertions after the `with` block.

## Compatibility considerations
N/A: test-only change, no production code, public interface, or schema affected.

## Security considerations
N/A: no production code touched.

## Rollback considerations
Single-method revert via `git revert`/`git checkout` of this file if needed; no
shared fixture or state affects other tests.

## Validation plan
- `uv run pytest tests/agent/test_orchestrator.py -v` — targeted; confirm the
  rewritten test passes and no other test in the file regresses.
- `uv run pytest tests/agent/workflow/ -v` — regression across workflow-engine tests.
- `uv run pytest` — full suite, once, per `rules/toolchain.md`.

## Completion criteria
- `TestAllowedToolsOverride::test_original_config_restored_even_on_error` passes
  without expecting a raised exception.
- The rewritten test still fails if the adapter's halt handler
  (`scripts/agent/workflow_engine_adapter.py`) stops resetting
  `ctx.workflow.active` or stops invoking a supplied `on_error` callback (verified by
  design, not executed against a deliberately-broken implementation in this cycle).
- No other test in `tests/agent/test_orchestrator.py` regresses.

## Out of scope
- Any change to `scripts/agent/workflow/workflow_engine.py` or
  `scripts/agent/workflow_engine_adapter.py`.
- The separate, unrelated `eventbus001` implementation procedure (different
  Plan/file).
- The dead-patch observation on the two adjacent tests in this same class (Plan
  Background) — not part of this Requirement.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the test per Implementation > Procedure/Method/Details | Completed | 20260929-125426 | 20260929-125426 | Test rewritten per Procedure/Method/Details; stale_detector clean after rewording false-positive backtick mentions (test names, __cause__, _handle_workflow_halt, handle_turn); ruff format's unrelated reformatting of 3 pre-existing spots reverted to keep diff scoped |
| 2 | Run targeted/regression/full-suite tests per Validation plan | Completed | 20260929-125427 | 20260929-125427 | Targeted: 87 passed. Regression tests/agent/workflow/: 134 passed. Full suite (non-randomized, to isolate a known unrelated order-dependent flaky test in test_memory_layer.py): 7997 passed, 24 skipped, 0 failed. Pre-existing mypy module-resolution error and lint-imports violation confirmed unrelated via pre-edit reproduction; bandit Low-only. |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260929-111152_agent007_orchestrator-memory-injection-error-no-longer-propagates-as-runtimeerror-under-workflow-engine-retry-halt.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260929-112809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-114027
- **Related target files**: tests/agent/test_orchestrator.py