# Implementation: BUG-4 — ToolCallResult tuple unpack fix

## Goal

Fix all tuple-unpack patterns in `test_tool_executor_routing.py` and
`test_tool_runner.py` that assume `ToolCallResult` (a frozen dataclass) is iterable.
Also fix mock `return_value`s that still return tuples, which causes `AttributeError`
inside `_execute_with_cache()` before the unpack is even reached.

## Scope

**In**:
- `tests/test_tool_executor_routing.py`
- `tests/test_tool_runner.py`

**Out**: No changes to production code.

## Assumptions

1. `ToolCallResult` fields: `output: str`, `is_error: bool`, `request_id: str`,
   `server_key: str` (`scripts/shared/tool_executor.py:48-54`).
2. `ToolExecutor.execute()` and `_raw_execute()` both return `ToolCallResult`.
3. `_execute_with_cache()` accesses `result.is_error` on the return value of
   `transport.call()` — so any mock returning a tuple causes `AttributeError` there
   before the test's own unpack. Both the mock AND the unpack must be fixed.
4. `_result, _is_err` prefixed variables are unused; they can be dropped in favour of
   reading only the needed field.

## Implementation

### Target file 1: `tests/test_tool_executor_routing.py`

**Add import** at the top (after existing `from shared.tool_executor import ...`):
```python
from shared.tool_executor import ToolCallResult
```

**Pattern A** — `transport.call()` 3-var (L244, L257, L266, L276, L293, L308, L322, L336):
```python
# Before
result, is_err, x_req_id = await transport.call("my_tool", {})
# After
res = await transport.call("my_tool", {})
result, is_err, x_req_id = res.output, res.is_error, res.request_id
```

**Pattern B** — `_result, _is_err` unused vars (L213, L227):
```python
# Before
_result, _is_err, x_req_id = await transport.call("my_tool", {})
# After
res = await transport.call("my_tool", {})
x_req_id = res.request_id
```

**Pattern B2** — `execute()` unused vars (L404):
```python
# Before
_result, _is_err, x_req = await ex.execute("read_text_file", {"path": "f"})
# After
res = await ex.execute("read_text_file", {"path": "f"})
x_req = res.request_id
```

**Pattern C** — `_raw_execute()` (L138, L147, L618, L634):
```python
# Before
result, is_err, _ = await ex._raw_execute(...)
# After
res = await ex._raw_execute(...)
result, is_err = res.output, res.is_error
```

**Pattern D** — `execute()` 3-var, plugin tools (L351, L366 — no mock change needed):
```python
# Before
result, is_err, x_req = await ex.execute("plugin_ok_tool", {})
# After
res = await ex.execute("plugin_ok_tool", {})
result, is_err, x_req = res.output, res.is_error, res.request_id
```

**Pattern D-mock** — `execute()` 3-var WITH mock fix (L380, L399, L408):

L376 mock + L380 unpack:
```python
# mock before (L376)
mock_transport.call = AsyncMock(return_value=("cached result", False, "req-1"))
# mock after
mock_transport.call = AsyncMock(
    return_value=ToolCallResult(output="cached result", is_error=False, request_id="req-1", server_key="")
)
# unpack before (L380)
result, is_err, x_req = await ex.execute("read_text_file", {"path": "f"})
# unpack after
res = await ex.execute("read_text_file", {"path": "f"})
result, is_err, x_req = res.output, res.is_error, res.request_id
```

L391 mock + L399 unpack:
```python
# mock before (L391)
mock_transport.call = AsyncMock(return_value=("result", False, "req-1"))
# mock after
mock_transport.call = AsyncMock(
    return_value=ToolCallResult(output="result", is_error=False, request_id="req-1", server_key="")
)
# unpack before (L399)
result, is_err, x_req = await ex.execute("read_text_file", {"path": "f"})
# unpack after
res = await ex.execute("read_text_file", {"path": "f"})
result, is_err, x_req = res.output, res.is_error, res.request_id
```

L407 mock (L408 uses Pattern B2 above):
```python
# mock before (L407)
mock_transport.call = AsyncMock(return_value=("ok", False, "req-xyz"))
# mock after
mock_transport.call = AsyncMock(
    return_value=ToolCallResult(output="ok", is_error=False, request_id="req-xyz", server_key="")
)
```

### Target file 2: `tests/test_tool_runner.py`

**Add import** at the top:
```python
from shared.tool_executor import ToolCallResult
```

**Fix 4 mock sites** (L70, L125, L183, L204):
```python
# Before
ctx.services.tools.execute = AsyncMock(return_value=("result", False, "req-1"))
# After
ctx.services.tools.execute = AsyncMock(
    return_value=ToolCallResult(output="result", is_error=False, request_id="req-1", server_key="")
)
```

Note: `test_tool_runner.py` does NOT unpack the return value directly in tests;
only the mock's return_value shape needs fixing.

## Validation plan

1. `uv run pytest tests/test_tool_executor_routing.py -v` — 15+ previously failing tests pass
2. `uv run pytest tests/test_tool_runner.py -v` — related failures resolved
3. `uv run mypy scripts/` — no new errors (test files not type-checked by default)
