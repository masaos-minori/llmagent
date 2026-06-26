# Implementation: Add partial-completion persistence test to test_orchestrator.py

Steps covered: Plan 20260626-091911 — Step 2-2

---

## Goal

Add a test verifying that when a workflow task fails mid-execution, `_handle_partial_completion()` is called with the correct arguments.

---

## Scope

- **In scope**: `tests/test_orchestrator.py` — add 1-2 test functions
- **Out of scope**: production code changes (steps 1-1, 1-2 must be completed first)

---

## Assumptions

- After steps 1-1 and 1-2, `orchestrator.py` calls `_handle_partial_completion()` in the exception path.
- `_handle_partial_completion()` is mockable via `mocker.patch`.

---

## Implementation

### Target file
`tests/test_orchestrator.py`

### Procedure
1. Read existing `tests/test_orchestrator.py` to understand fixture patterns.
2. Add `test_partial_completion_recorded_on_mid_workflow_failure`:
   ```python
   @pytest.mark.asyncio
   async def test_partial_completion_recorded_on_mid_workflow_failure(mocker):
       ctx = build_ctx()
       mock_handle = mocker.patch.object(ctx.session, "_handle_partial_completion")
       # simulate: step 1 succeeds, step 2 raises
       ...
       with pytest.raises(SomeWorkflowStepError):
           await run_orchestrator(ctx, task_id="t1")
       mock_handle.assert_called_once()
       call_kwargs = mock_handle.call_args.kwargs
       assert call_kwargs["task_id"] == "t1"
       assert "step1" in call_kwargs["completed_steps"]
   ```
3. Add `test_partial_completion_not_called_on_full_success`:
   - All steps succeed → `_handle_partial_completion` is NOT called.

### Method
`pytest-asyncio` + `pytest-mock`.

---

## Validation plan

- Run: `uv run pytest tests/test_orchestrator.py -x -v` — new tests pass.
- Run full suite: `uv run pytest tests/ -x` — no regressions.
