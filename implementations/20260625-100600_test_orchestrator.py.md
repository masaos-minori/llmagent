# tests/test_orchestrator.py — update required mode test for construction-time fail-fast

**Plan:** `plans/20260625-093349_plan.md` (req #61)
**Target:** `tests/test_orchestrator.py`

## What to change

The existing test `test_required_mode_no_workflow_def_raises` (line 743) tests the OLD behavior
(construction succeeds → `handle_turn` raises). After the `orchestrator.py` change, `Orchestrator()`
will raise at construction time in required mode when `WorkflowLoader` fails.

### Replace `test_required_mode_no_workflow_def_raises` (line 742-750)

**Before:**
```python
@pytest.mark.asyncio
async def test_required_mode_no_workflow_def_raises(self) -> None:
    ctx = _make_ctx()
    with patch("agent.orchestrator.WorkflowLoader") as mock_loader:
        mock_loader.return_value.load.side_effect = Exception("not found")
        orch = Orchestrator(ctx, workflow_mode="required")
    assert orch._workflow_def is None
    with pytest.raises(RuntimeError, match="workflow unavailable"):
        await orch.handle_turn("hello")
```

**After:**
```python
def test_required_mode_raises_at_construction_when_loader_fails(self) -> None:
    ctx = _make_ctx()
    with (
        patch("agent.orchestrator.WorkflowLoader") as mock_loader,
        pytest.raises(RuntimeError, match="mode=required"),
    ):
        mock_loader.return_value.load.side_effect = Exception("not found")
        Orchestrator(ctx, workflow_mode="required")
```

Note: No longer `@pytest.mark.asyncio` — synchronous construction-time check.

### Also add: test that auto mode still falls back (no raise at construction)

Verify the existing `test_auto_mode_no_workflow_def_runs_direct` at line 717 still passes —
no change needed to it, but confirm behavior is preserved.

### Optional: add test for WorkflowLoadError specifically

```python
def test_required_mode_raises_on_workflow_load_error(self) -> None:
    from agent.workflow.loader import WorkflowLoadError
    ctx = _make_ctx()
    with (
        patch("agent.orchestrator.WorkflowLoader") as mock_loader,
        pytest.raises(RuntimeError, match="mode=required"),
    ):
        mock_loader.return_value.load.side_effect = WorkflowLoadError("bad yaml")
        Orchestrator(ctx, workflow_mode="required")
```

## Validation

```
uv run pytest tests/test_orchestrator.py::TestWorkflowMode -v
uv run pytest tests/test_orchestrator.py -q
```
