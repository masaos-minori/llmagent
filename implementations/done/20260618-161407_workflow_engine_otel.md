# Implementation: WorkflowEngine OTel spans

## Goal

Add OTel span instrumentation to WorkflowEngine.run() and per-stage execution.

## Scope

- `scripts/agent/workflow/workflow_engine.py`

## Details

Add `tracer: Any = None` to `WorkflowEngine.__init__()`.

Add `_span_ctx()` method (same pattern as `LLMTurnRunner._span_ctx()`):
```python
def _span_ctx(self, name: str, **attrs: Any) -> Any:
    from contextlib import nullcontext  # noqa: PLC0415
    if self._tracer is not None:
        span = self._tracer.start_as_current_span(name)
        # set_attribute calls would go inside the with block at call site
        return span
    return nullcontext()
```

Wrap `run()` with `"workflow.run"` span:
```python
async def run(self, task, plan_fn, execute_fn, verify_fn):
    with self._span_ctx("workflow.run") as span:
        if hasattr(span, "set_attribute"):
            span.set_attribute("workflow.task_id", task.task_id)
            span.set_attribute("workflow.version", task.workflow_version)
        # existing logic ...
```

Wrap each stage call in `_run_stage()` with `"workflow.stage"` span:
```python
with self._span_ctx("workflow.stage") as span:
    if hasattr(span, "set_attribute"):
        span.set_attribute("workflow.stage_id", stage_id)
        span.set_attribute("workflow.attempt", attempt)
    # existing stage logic ...
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/workflow/workflow_engine.py` | 0 errors |
| Type | `uv run mypy scripts/agent/workflow/workflow_engine.py` | 0 errors |
| Tests | `uv run pytest tests/test_workflow_engine.py -v` | all pass |
