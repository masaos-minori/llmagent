## Goal
Add startup hardening tests to `tests/test_startup.py`: assert agent startup aborts on missing workflow definition, invalid JSON, and missing workflow schema tables.

## Scope
**In**: `tests/test_startup.py` — remove warning-only tests; add RuntimeError abort tests for each workflow preflight failure mode.
**Out**: Other startup tests (MCP, config load, session init); `repl_health.py` implementation.

## Assumptions
- Tests named `test_startup_continues_with_warning_on_missing_workflow`, `test_startup_degraded_when_workflow_loader_fails` are removed.
- After Plan 04 (req04), any `WorkflowLoadError` or missing-schema error aborts startup with `RuntimeError`.
- `AgentStartup._check_workflow_definition()` and `_check_workflow_schema()` are the startup gates.
- `WorkflowLoader`, `check_workflow_definition`, `check_workflow_schema` are mockable via `unittest.mock.patch`.

## Implementation

**Target file**: `tests/test_startup.py`

**Procedure**:
1. **Remove**:
   - `test_startup_continues_with_degraded_workflow_mode`
   - `test_startup_logs_warning_on_workflow_load_failure`
   - `test_startup_continues_when_check_workflow_definition_returns_errors`
   - Any test asserting `logger.warning` is the only outcome of workflow failure

2. **Add**:
   ```python
   def test_startup_aborts_on_missing_workflow_definition(tmp_path, mocker):
       mocker.patch("agent.repl_health.check_workflow_definition", side_effect=RuntimeError("missing"))
       with pytest.raises(RuntimeError, match="missing"):
           startup = AgentStartup(ctx=mock_ctx)
           asyncio.run(startup.run())

   def test_startup_aborts_on_invalid_workflow_json(tmp_path, mocker):
       mocker.patch("agent.repl_health.check_workflow_definition", side_effect=RuntimeError("invalid JSON"))
       with pytest.raises(RuntimeError):
           asyncio.run(startup.run())

   def test_startup_aborts_on_missing_workflow_schema(mocker):
       mocker.patch("agent.repl_health.check_workflow_definition")  # passes
       mocker.patch("agent.repl_health.check_workflow_schema", side_effect=RuntimeError("missing table"))
       with pytest.raises(RuntimeError, match="missing table"):
           asyncio.run(startup.run())

   def test_startup_check_runs_definition_before_schema(mocker):
       check_def = mocker.patch("agent.repl_health.check_workflow_definition")
       check_schema = mocker.patch("agent.repl_health.check_workflow_schema")
       asyncio.run(startup.run())
       # assert definition check called before schema check
       assert check_def.call_count == 1
       assert check_schema.call_count == 1
       assert check_def.call_args_list[0].args < check_schema.call_args_list[0].args  # or use call order mock

   def test_startup_error_message_has_no_workflow_mode_suggestion(mocker):
       mocker.patch("agent.repl_health.check_workflow_definition",
                    side_effect=RuntimeError("definition missing"))
       with pytest.raises(RuntimeError) as exc_info:
           asyncio.run(startup.run())
       assert "workflow_mode" not in str(exc_info.value)
       assert "disabled" not in str(exc_info.value)
   ```

3. **Update `AgentStartup` constructor tests** that pass `workflow_mode` kwarg:
   - Remove `workflow_mode=` from any `AgentStartup(...)` or `Orchestrator(...)` call in tests

**Method**: Test removal + new test additions using mocks.

**Details**:
- Use `mocker.patch` (pytest-mock) to intercept `check_workflow_definition` and `check_workflow_schema` at the `repl_health` module level.
- Call order assertion: use `mock.call_args_list` index comparison or `side_effect` with a counter.

## Validation plan
- `uv run pytest tests/test_startup.py -x -q`
- `grep -n "workflow_mode.*continues\|warning.*workflow" tests/test_startup.py` → 0

---
*Plan: 20260707-095941 (req04) Phase 4, 20260707-103633 (req08) Phase 4 (shared startup tests)*
