# Goal

Define `ToolCallResult` and `TransportErrorInfo` DTOs, change all
`tuple[str, bool, str]` return values to `ToolCallResult`, add MCP response JSON
validation, narrow all four `except Exception` clauses to specific types, and
change `format_transport_error()` to return `TransportErrorInfo`.

# Scope

- `scripts/shared/tool_executor.py`
- `scripts/agent/tool_runner.py` (caller: one tuple unpack at line 65)
- `scripts/agent/repl_tool_exec.py` (if it accesses the tuple directly — check)

# Assumptions

1. `ToolCallResult` and `TransportErrorInfo` are defined in `tool_executor.py`
   (not `db/models.py`). They are `frozen=True` dataclasses.
2. The four `except Exception` sites map to:
   - `HttpTransport.call()` line ~98: unexpected non-HTTP/network error → delete;
     let propagate (only `httpx.HTTPStatusError` and `httpx.RequestError` are expected).
   - `StdioTransport.call()` line ~192: `OSError`, `BrokenPipeError` for I/O errors.
   - `StdioTransport.stop()` line ~232: `OSError`, `BrokenPipeError` for stop errors.
   - `ToolExecutor.execute()` line ~463: plugin tool error — keep catch but validate
     return type; do NOT silently catch all; use `Exception` only as last resort with
     explicit re-raise prevention. Actually per constraint: remove it, let propagate;
     OR narrow to most likely exceptions from plugin code.
3. `tool_runner.py:65` does `text, is_error, x_request_id = await ctx.services.tools.execute(name, args)`.
   Change to:
   ```python
   result = await ctx.services.tools.execute(name, args)
   text, is_error, x_request_id = result.output, result.is_error, result.request_id
   ```
4. `format_transport_error()` callers: check with
   `grep -rn "format_transport_error" scripts/` before implementing.
5. MCP response JSON validation: in `HttpTransport.call()`, after `resp.json()`:
   ```python
   data = orjson.loads(resp.content)
   if not isinstance(data, dict):
       raise ValueError(f"MCP /v1/call_tool returned non-dict: {type(data).__name__}")
   result_val = data.get("result")
   if not isinstance(result_val, str):
       raise ValueError(f"MCP /v1/call_tool missing 'result' field")
   is_error_val = data.get("is_error", False)
   if not isinstance(is_error_val, bool):
       raise ValueError(f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}")
   ```

# Implementation

## Target file

`scripts/shared/tool_executor.py`, `scripts/agent/tool_runner.py`

## Procedure

### A. Define DTOs in `tool_executor.py` (before the transports)

```python
@dataclass(frozen=True)
class ToolCallResult:
    """Typed result from a single tool call execution."""
    output: str
    is_error: bool
    request_id: str    # x-request-id from HTTP transport; "" for stdio/plugin/cache
    server_key: str    # server key that handled the call; "" for plugin tools


@dataclass(frozen=True)
class TransportErrorInfo:
    """Structured error info for LLM/tool transport failures (for audit logs)."""
    summary: str
    detail: str  # JSON-encoded dict for audit log


@dataclass(frozen=True)
class _CacheEntry:
    """Internal cache entry replacing tuple[str, bool, float]."""
    output: str
    is_error: bool
    cached_at: float
```

### B. `HttpTransport.call()` → `ToolCallResult`

1. Replace `resp.json()` with `orjson.loads(resp.content)` + validation (see above).
2. Return `ToolCallResult(output=result_val, is_error=is_error_val, request_id=x_request_id, server_key=self._server_key)`.
3. Error returns: `ToolCallResult(output=msg, is_error=True, request_id="", server_key=self._server_key)`.
4. Delete `except Exception` — let unexpected exceptions propagate.

### C. `StdioTransport.call()` → `ToolCallResult`

1. Return `ToolCallResult(...)` throughout.
2. `except Exception as e:` (line 192) → `except (OSError, BrokenPipeError) as e:`.

### D. `StdioTransport.stop()`

1. `except Exception as e:` → `except (OSError, BrokenPipeError) as e:`.

### E. `ToolExecutor._raw_execute()`, `_execute_with_cache()`, `execute()` → `ToolCallResult`

1. All return `ToolCallResult`.
2. Internal `_cache: OrderedDict[str, tuple[str, bool, float]]` → `OrderedDict[str, _CacheEntry]`.
3. `execute()` plugin path: `except Exception as e:` → remove entirely. Plugin
   exceptions propagate to caller (documented in plugin docstring).
   OR narrow to `except Exception` with `raise` after logging if silencing is required.
   **Decision**: remove; let propagate. Plugin authors are responsible for not raising.

### F. `format_transport_error()` → `TransportErrorInfo`

1. Check callers: `grep -rn "format_transport_error" scripts/` and update them.
2. Change return type and construction.

### G. `tool_runner.py` caller update

```python
# Before (line 65)
text, is_error, x_request_id = await ctx.services.tools.execute(name, args)

# After
result = await ctx.services.tools.execute(name, args)
text, is_error, x_request_id = result.output, result.is_error, result.request_id
```

Also update line 85 (`return tc["id"], name, args, text, is_error, llm_text`) —
`text` is now a local string unpacked above, so no change needed at that site.

## Method

DTO definition + pervasive return type change + one caller update + 4× except narrowing.

# Validation plan

- `grep -n "except Exception" scripts/shared/tool_executor.py` → 0 hits
- `grep -n "tuple\[str, bool" scripts/shared/tool_executor.py` → 0 hits
  (except `_cache` type annotation if `_CacheEntry` not fully applied)
- `grep -n "format_transport_error" scripts/` → all callers use `TransportErrorInfo` attributes
- `uv run ruff check scripts/shared/tool_executor.py scripts/agent/tool_runner.py`
- `uv run mypy scripts/shared/tool_executor.py scripts/agent/tool_runner.py`
- `uv run pytest tests/test_shared_tool_executor.py tests/ -k "tool_run" --ignore=tests/test_create_schema.py -v`
