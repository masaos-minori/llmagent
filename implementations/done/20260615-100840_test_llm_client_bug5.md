# Implementation: BUG-5 — TransportErrorInfo dict access fix

## Goal

Fix `TestFormatTransportError._call()` in `tests/test_llm_client.py` to return
`TransportErrorInfo` instead of a `cast`-ed `dict[str, str]`, and update all
assertion sites to use attribute access.

## Scope

**In**: `tests/test_llm_client.py` (class `TestFormatTransportError` only).
**Out**: No changes to production code or other test classes.

## Assumptions

1. `TransportErrorInfo` fields: `summary: str`, `detail: str`
   (`scripts/shared/tool_executor.py:61-62`).
2. `format_transport_error(...)` already returns `TransportErrorInfo` — the `cast`
   was a workaround that suppressed the TypeError at runtime.
3. 5 test methods in `TestFormatTransportError` access the result via `result["key"]`
   or `"key" in result`.

## Implementation

### Target file

`tests/test_llm_client.py` — class `TestFormatTransportError` (L610-L666)

### Procedure

**Edit 1 — `_call()` return type and body (L611-L636)**:
```python
# Before
def _call(self, ...) -> dict[str, str]:
    from typing import cast
    return cast(
        dict[str, str],
        format_transport_error(...),
    )

# After
def _call(self, ...) -> TransportErrorInfo:
    from shared.tool_executor import TransportErrorInfo, format_transport_error
    return format_transport_error(...)
```

**Edit 2 — assertion sites**:

| Line (approx) | Before | After |
|---|---|---|
| L640 | `assert "summary" in result` | `assert result.summary` |
| L641 | `assert "detail" in result` | `assert result.detail` |
| L645 | `assert "LLM" in result["summary"]` | `assert "LLM" in result.summary` |
| L646 | `assert "HTTP_STATUS_FATAL" in result["summary"]` | `assert "HTTP_STATUS_FATAL" in result.summary` |
| L652 | `data = orjson.loads(result["detail"])` | `data = orjson.loads(result.detail)` |
| L659 | `assert "TOOL" in result["summary"]` | `assert "TOOL" in result.summary` |
| L665 | `data = orjson.loads(result["detail"])` | `data = orjson.loads(result.detail)` |

### Method

Two Edit operations: one for `_call()`, one for the assertion block.
The `from typing import cast` line inside `_call()` is removed.

## Validation plan

1. `uv run pytest tests/test_llm_client.py::TestFormatTransportError -v` — all 5 pass
