## Goal
Remove approval-disabled tests from `tests/test_workflow_engine.py`; add tests verifying `_gate_approval()` is always called and `task.workflow_id` is always non-empty in spans.

## Scope
**In**: `tests/test_workflow_engine.py` — remove `require_approval=False` tests; add always-on approval tests; add `workflow_id` invariant tests.
**Out**: Stage execution tests; artifact tests; approval logic itself.

## Assumptions
- Tests named `test_workflow_engine_require_approval_false_*`, `test_workflow_engine_no_approval_when_disabled`, `test_verify_runs_without_approval` are removed.
- `WorkflowEngine` constructor no longer accepts `require_approval` after Plan 05 (req05).
- `task.workflow_id` is `str` (not `str | None`) after Plan 09 (req09).

## Implementation

**Target file**: `tests/test_workflow_engine.py`

**Procedure**:
1. **Remove**:
   - `test_workflow_engine_require_approval_false_by_default`
   - `test_workflow_engine_receives_require_approval_from_config`
   - `test_verify_never_runs_without_approval` (if this tests approval=False behavior)
   - Any call to `WorkflowEngine(..., require_approval=False)`
   - Any test asserting `_gate_approval` is NOT called

2. **Add**:
   ```python
   def test_workflow_engine_always_calls_gate_approval(mocker):
       gate = mocker.patch.object(engine, "_gate_approval")
       asyncio.run(engine.run(task, ctx))
       gate.assert_called_once()

   def test_verify_never_runs_before_approval(mocker):
       gate = mocker.patch.object(engine, "_gate_approval", side_effect=WorkflowPendingApprovalError(...))
       with pytest.raises(WorkflowPendingApprovalError):
           asyncio.run(engine.run(task, ctx))
       # verify stage should NOT have been called
       mocker.patch.object(engine, "_run_stage").assert_not_called()  # or check call_args

   def test_workflow_engine_span_uses_stable_workflow_id(mocker):
       task = TaskRecord(task_id="t-1", workflow_id="wf-stable-1", ...)
       # confirm no "or ''" masking — span attribute is exactly "wf-stable-1"
       span_mock = mocker.MagicMock()
       ...
       assert span_mock.set_attribute.call_args_list contains ("workflow.workflow_id", "wf-stable-1")

   def test_create_task_requires_workflow_id():
       with pytest.raises(TypeError):  # or RuntimeError
           create_task(db, session_id="s1", turn_number=1, workflow_version="v1")
           # omitting workflow_id should fail
   ```

3. **Update test fixtures**:
   - Any `TaskRecord(workflow_id=None)` → `TaskRecord(workflow_id="wf-test-1")`
   - Any `WorkflowEngine(..., require_approval=...)` → remove `require_approval` kwarg

**Method**: Targeted test removal + new test additions.

## Validation plan
- `uv run pytest tests/test_workflow_engine.py -x -q`
- `grep -n "require_approval\|approval_false\|workflow_id=None" tests/test_workflow_engine.py` → 0

---
*Plans: 20260707-095942 (req05) Phase 5, 20260707-103632 (req07) Phase 6, 20260707-103634 (req09) Phase 6*
