# Implementation: Add workflow context suppression test to test_tool_approval_paths.py

Steps covered: Plan 20260626-090724 — Phase 3, Step 3-2

---

## Goal

Add a test to `tests/test_tool_approval_paths.py` that verifies `run_approval_checks` correctly skips per-tool approval when `skip_in_workflow_mode=True`, returning all tool calls as approved without invoking stdin.

---

## Scope

- **In scope**: `tests/test_tool_approval_paths.py` — add 1-2 new test functions
- **Out of scope**: production code changes (step 2-2 must be completed first)

---

## Assumptions

- After step 2-2, `run_approval_checks` accepts `skip_in_workflow_mode: bool = False`.
- When `skip_in_workflow_mode=True`, the function returns `(tool_calls, [])` without prompting stdin.
- Existing tests (`test_tool_approval_paths.py`) use async fixtures for `AgentContext`.

---

## Implementation

### Target file
`tests/test_tool_approval_paths.py`

### Procedure
1. Read `tests/test_tool_approval_paths.py` to understand existing fixture patterns (especially `build_ctx`, `build_tool_call` helpers).
2. Add `test_run_approval_checks_skips_when_workflow_mode_active`:
   - Build a ctx with `workflow_require_approval=True`.
   - Create a list of MEDIUM-risk tool calls that would normally prompt for approval.
   - Call `run_approval_checks(..., skip_in_workflow_mode=True)`.
   - Assert: all tool calls returned as approved; no denied IDs; no stdin prompt fired.
3. Add `test_run_approval_checks_not_skipped_by_default`:
   - Call `run_approval_checks(..., skip_in_workflow_mode=False)` (default).
   - Confirm existing approval logic fires (stdin mock or risk-based skip).

### Method
Use `pytest-asyncio` for async test functions. Mock stdin / `emit_approval_prompt` to confirm it is NOT called when `skip_in_workflow_mode=True`.

### Details

Test skeleton:
```python
@pytest.mark.asyncio
async def test_run_approval_checks_skips_when_workflow_mode_active(mocker):
    ctx = build_ctx(workflow_require_approval=True)
    tool_calls = [build_tool_call("file_write", risk=RiskLevel.MEDIUM)]
    mock_emit = mocker.patch("agent.tool_approval.emit_approval_prompt")
    
    approved, denied = await run_approval_checks(
        ctx, tool_calls, skip_in_workflow_mode=True
    )
    
    assert approved == tool_calls
    assert denied == []
    mock_emit.assert_not_called()
```

Edge cases:
- `skip_in_workflow_mode=True` with HIGH-risk tools: still skips (logs at DEBUG).
- `skip_in_workflow_mode=False` with HIGH-risk tools: normal approval flow.

---

## Validation plan

- Run: `uv run pytest tests/test_tool_approval_paths.py -x -v` — new tests must pass.
- Run: `uv run pytest tests/test_tool_approval_paths.py -x` — no regressions.
- Type check: `mypy tests/test_tool_approval_paths.py` — no new errors.
