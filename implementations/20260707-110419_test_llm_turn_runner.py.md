## Goal
Rewrite all `runner.run(llm_url)` calls in `tests/test_llm_turn_runner.py` to supply required workflow context; add tests for missing context and extended `_span_ctx()` attributes.

## Scope
**In**: `tests/test_llm_turn_runner.py` — update all `run()` calls; add missing-context test; add span attribute tests.
**Out**: Other test files using `LLMTurnRunner`.

## Assumptions
- `LLMTurnRunner.run()` signature changes to require `workflow_id`, `task_id`, `stage_id`, `attempt_id` after Plan 06 (req06).
- All current calls are `runner.run(llm_url)` without keyword args.
- Standard test values: `workflow_id="wf-test-1"`, `task_id="task-test-1"`, `stage_id="execute"`, `attempt_id="att-test-1"`.

## Implementation

**Target file**: `tests/test_llm_turn_runner.py`

**Procedure**:
1. **Bulk update all `runner.run()` calls**:
   - `grep -n "\.run(" tests/test_llm_turn_runner.py` — find all occurrences
   - Replace each:
     ```python
     # Before:
     result = await runner.run(llm_url)

     # After:
     result = await runner.run(
         llm_url,
         workflow_id="wf-test-1",
         task_id="task-test-1",
         stage_id="execute",
         attempt_id="att-test-1",
     )
     ```
   - Or create a fixture:
     ```python
     WF_CTX = dict(workflow_id="wf-test-1", task_id="task-test-1", stage_id="execute", attempt_id="att-test-1")
     # then: result = await runner.run(llm_url, **WF_CTX)
     ```

2. **Add missing-context test**:
   ```python
   async def test_run_raises_without_workflow_context(runner):
       with pytest.raises(RuntimeError, match="requires non-empty workflow context"):
           await runner.run(llm_url, workflow_id="", task_id="t-1", stage_id="execute", attempt_id="att-1")
   ```

3. **Add `_span_ctx()` attribute tests**:
   ```python
   def test_span_ctx_sets_workflow_attributes(runner, mock_tracer):
       with runner._span_ctx("llm", task_id="t-1", workflow_id="wf-1", stage_id="execute", attempt_id="att-1"):
           pass
       attrs = mock_tracer.started_spans[-1].attributes
       assert attrs["workflow.workflow_id"] == "wf-1"
       assert attrs["workflow.stage_id"] == "execute"
       assert attrs["workflow.attempt_id"] == "att-1"

   def test_span_ctx_empty_workflow_id_not_set_as_attribute(runner, mock_tracer):
       with runner._span_ctx("llm", workflow_id=""):
           pass
       assert "workflow.workflow_id" not in mock_tracer.started_spans[-1].attributes

   def test_handle_llm_error_includes_workflow_context(runner, mocker):
       diagnostics = mocker.MagicMock()
       runner._handle_llm_error(..., workflow_id="wf-1", task_id="t-1")
       diagnostics.save.assert_called_with(..., workflow_id="wf-1", task_id="t-1")
   ```

**Method**: Bulk call-site update + new test additions.

**Details**:
- Creating a `WF_CTX` dict fixture reduces repetition across 20+ test cases.
- `mock_tracer` fixture: capture span starts with a test double that records attributes.

## Validation plan
- `uv run pytest tests/test_llm_turn_runner.py -x -q`
- `grep -n "\.run(llm_url)" tests/test_llm_turn_runner.py | grep -v "workflow_id"` → 0

---
*Plans: 20260707-103631 (req06) Phase 5, 20260707-103632 (req07) Phase 6, 20260707-105308 (req12) Phase 3*
