## Goal
Remove all direct-execution and degraded-startup tests from `tests/test_orchestrator.py`; add fail-fast tests asserting workflow is always required.

## Scope
**In**: `tests/test_orchestrator.py` — remove disabled-mode and direct-execution tests; add fail-fast and always-workflow tests.
**Out**: Other orchestrator tests (workflow engine integration, turn routing); test fixtures.

## Assumptions
- Tests named `test_handle_turn_direct_execution_*`, `test_handle_turn_workflow_disabled_*`, `test_orchestrator_init_degraded_*`, `test_handle_turn_fallback_*` are being removed.
- After Plan 02/03 changes, `handle_turn()` with `_workflow_def = None` should raise `RuntimeError` (not call `_process_turn` directly).
- After Plan 04 changes, `Orchestrator.__init__()` raises `RuntimeError` when `WorkflowLoader().load()` raises.
- `WorkflowLoader` is importable and mockable: `from unittest.mock import patch`.

## Implementation

**Target file**: `tests/test_orchestrator.py`

**Procedure**:
1. **Remove direct-execution tests**:
   - Remove `test_handle_turn_direct_execution_when_disabled`
   - Remove `test_handle_turn_direct_execution_returns_answer`
   - Remove `test_process_turn_called_directly_when_workflow_disabled`
   - Remove any test that asserts `_process_turn` is called at the top level without workflow context

2. **Remove fallback/degraded startup tests**:
   - Remove `test_orchestrator_init_succeeds_when_workflow_loader_fails`
   - Remove `test_orchestrator_init_logs_warning_on_workflow_failure`
   - Remove `test_handle_turn_falls_back_to_direct_when_workflow_unavailable`
   - Remove any test with `logger.warning.*WorkflowLoader` in assertions

3. **Add fail-fast tests**:
   ```python
   def test_handle_turn_raises_when_workflow_def_none(orchestrator):
       orchestrator._workflow_def = None
       with pytest.raises(RuntimeError, match="workflow definition not loaded"):
           asyncio.run(orchestrator.handle_turn("hello", ctx, turn_started_at=0.0))

   def test_handle_turn_never_calls_process_turn_directly(orchestrator, mocker):
       spy = mocker.spy(orchestrator, "_process_turn")
       # handle_turn goes through _handle_workflow_engine only
       asyncio.run(orchestrator.handle_turn("hello", ctx, turn_started_at=0.0))
       spy.assert_not_called()  # _process_turn only called inside workflow stage callbacks

   def test_orchestrator_init_fails_when_workflow_loader_raises():
       with patch("agent.orchestrator.WorkflowLoader") as mock_loader:
           mock_loader.return_value.load.side_effect = WorkflowLoadError("missing")
           with pytest.raises(RuntimeError, match="WorkflowLoader failed"):
               Orchestrator(ctx=mock_ctx)

   def test_orchestrator_init_fails_on_invalid_workflow_json():
       with patch("agent.orchestrator.WorkflowLoader") as mock_loader:
           mock_loader.return_value.load.side_effect = WorkflowLoadError("invalid JSON")
           with pytest.raises(RuntimeError):
               Orchestrator(ctx=mock_ctx)

   def test_orchestrator_workflow_id_fallback_removed():
       # Resuming a task with workflow_id=None raises RuntimeError
       task = TaskRecord(task_id="t-1", workflow_id=None, ...)
       with pytest.raises(RuntimeError, match="no workflow_id.*cannot resume"):
           orchestrator._init_workflow_task(task)
   ```

4. **Update existing workflow tests**:
   - Any test using `Orchestrator(workflow_mode="disabled")` → remove the kwarg
   - Any test using `Orchestrator(workflow_mode="required")` → remove the kwarg
   - Any test using `require_approval=False` in `WorkflowEngine` construction → remove kwarg

**Method**: Targeted function removal + new test additions.

**Details**:
- Use `grep -n "def test_.*direct\|def test_.*disabled\|def test_.*fallback\|def test_.*degraded" tests/test_orchestrator.py` to find all candidates before deleting.
- Check for `_process_turn` spy assertions — they may be valid in stage callback context; only remove ones asserting top-level direct call.

## Validation plan
- `uv run pytest tests/test_orchestrator.py -x -q`
- `rg "workflow_mode.*disabled\|direct.*execution\|_process_turn.*called_once\b" tests/test_orchestrator.py` → 0

---
*Plans: 20260707-095939 (req02), 20260707-095940 (req03), 20260707-095941 (req04) Phase 2*
