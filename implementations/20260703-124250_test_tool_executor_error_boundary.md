# Implementation: Add `TestToolExecutorErrorBoundary` to `tests/test_tool_executor.py`

## Goal

Add a new `TestToolExecutorErrorBoundary` test class after the existing `TestHttpTransportRetry` class, covering all six acceptance-criteria scenarios for `ToolExecutor` error boundary behavior.

## Scope

- In-Scope: Append the `TestToolExecutorErrorBoundary` class to `tests/test_tool_executor.py`; add any required imports if not already present.
- Out-of-Scope: No changes to any other test file; no changes to any production Python file; no modifications to existing test methods.

## Assumptions

1. `McpServerHealthRegistry` is importable from `shared.mcp_config` (confirmed: line 28 of `tool_executor.py` imports it from that path).
2. The `ToolExecutor` constructor requires `http`, `cache_ttl`, `server_configs` as positional/keyword arguments (confirmed at lines 279-288 of `tool_executor.py`). A minimal `McpServerConfig` stub is required.
3. `ToolExecutor.set_health_registry(mock_registry)` works correctly via the method at line 343 of `tool_executor.py`.
4. `ToolExecutor._raw_execute()` is the internal method that calls `_record_success()` / `_record_transport_error()` — tests call the public path via `_raw_execute` directly or via a minimal `ToolRouteResolver` stub.
5. `McpServerConfig` can be constructed with at minimum `url` and `transport` fields; other fields have defaults.
6. `httpx.TimeoutException("msg")` is a valid constructor call (confirmed by existing test at line 222).
7. `asyncio.sleep` can be patched as `patch("asyncio.sleep", return_value=None)` (established pattern at lines 105, 127, etc.).
8. The existing `unittest.mock` import is not present in the file — it needs to be added.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_tool_executor.py`

### Procedure

1. Read the current end of the file to confirm the last line (currently line 288).
2. Check the import block (lines 1-19) for `unittest.mock` imports; add `from unittest.mock import AsyncMock, MagicMock, patch` if missing.
3. Check for `McpServerConfig` import; add `from shared.mcp_config import McpServerConfig, McpServerHealthRegistry` if missing.
4. Add a blank line after line 288 (end of `TestHttpTransportRetry`), then append the full `TestToolExecutorErrorBoundary` class.
5. Run `uv run pytest tests/test_tool_executor.py -v` to confirm all 6 new tests pass and no existing tests regress.
6. Run `uv run ruff check tests/test_tool_executor.py` to confirm 0 linting errors.

### Method

**Imports to add** (if not already present):

```python
from unittest.mock import AsyncMock, MagicMock, patch

from shared.mcp_config import McpServerConfig, McpServerHealthRegistry
```

**Helper to build a minimal `ToolExecutor` instance:**

Use `ToolExecutor.__new__(ToolExecutor)` + manual attribute injection as the `TestCacheStampede` class does. However, the `_raw_execute` path requires `_resolver`, `_transports`, `_health_registry`, `stat_tool_errors`, `stat_transport_errors`, `_lifecycle`, `_semaphores`, and `_concurrency_limits`. Alternatively, construct a real `ToolExecutor` with a minimal `McpServerConfig`:

```python
def _make_executor(fake_client: Any, server_key: str = "test") -> ToolExecutor:
    cfg = McpServerConfig(url="http://localhost:9999", transport="http")
    executor = ToolExecutor(
        http=fake_client,
        cache_ttl=60.0,
        server_configs={server_key: cfg},
    )
    return executor
```

**Pattern for faking `ToolRouteResolver.resolve()`**: when using a real `ToolExecutor`, call `_raw_execute("some_tool", {})` where `"some_tool"` resolves to the configured `server_key`. Override the resolver with a `MagicMock` if needed: `executor._resolver = MagicMock(); executor._resolver.resolve.return_value = "test"`.

**Pattern for spying on HealthRegistry:**

```python
registry = McpServerHealthRegistry()
registry.record_success = MagicMock(wraps=registry.record_success)
registry.record_failure = MagicMock(wraps=registry.record_failure)
executor.set_health_registry(registry)
```

**Pattern for faking HTTP responses:**

```python
class _FakeClient:
    async def post(self, url: str, **kw: Any) -> httpx.Response:
        req = httpx.Request("POST", url)
        return httpx.Response(200, request=req, json={"result": "ok", "is_error": False})
```

### Details

**Six test methods** (all `@pytest.mark.asyncio`):

---

**`test_http_200_is_error_true_increments_tool_error`**

- `_FakeClient.post` returns HTTP 200 with `json={"result": "err msg", "is_error": True}`.
- Create `executor` with a `McpServerHealthRegistry`, spied on via `MagicMock(wraps=...)`.
- Call `await executor._raw_execute("write_file", {})`.
- Assert `result.error_type == "tool"`.
- Assert `executor.stat_tool_errors.get("test", 0) == 1`.
- Assert `registry.record_success.call_count == 1`.
- Assert `registry.record_failure.call_count == 0`.

---

**`test_http_500_raises_transport_error_internally`**

- `_FakeClient.post` returns HTTP 500 (non-retryable; `raise_for_status()` raises `httpx.HTTPStatusError`).
- Assert `result.error_type == "transport"`.
- Assert `executor.stat_transport_errors.get("test", 0) == 1`.
- Assert `registry.record_failure.call_count == 1`.
- Assert `registry.record_success.call_count == 0`.

Note: `httpx.Response(500, ...)` does not raise on construction; `HttpTransport.call()` calls `resp.raise_for_status()` which raises `httpx.HTTPStatusError` internally, caught and re-raised as `TransportError`.

---

**`test_timeout_classified_as_transport_error`**

- `_FakeClient.post` raises `httpx.TimeoutException("timed out")`.
- Assert `result.error_type == "transport"`.
- Assert `executor.stat_transport_errors.get("test", 0) == 1`.
- Assert `registry.record_failure.call_count == 1`.

---

**`test_malformed_response_classified_as_transport_error`**

- `_FakeClient.post` returns HTTP 200 with `json={"no_result_key": "bad"}` (missing `"result"` key).
- `HttpTransport._parse_http_response()` raises `ValueError("MCP /v1/call_tool missing 'result' str field")`, caught as `ValueError` in `except (httpx.RequestError, ValueError)` block, re-raised as `TransportError`.
- Assert `result.error_type == "transport"`.
- Assert `executor.stat_transport_errors.get("test", 0) == 1`.
- Assert `registry.record_failure.call_count == 1`.

---

**`test_503_retry_exhausted_becomes_transport_error`**

- `_FakeClient.post` always returns HTTP 503.
- All 3 retry attempts fail; `TransportError("Retry exhausted ...")` is raised after the loop.
- Patch `asyncio.sleep` to skip delays.
- Assert `result.error_type == "transport"`.
- Assert `executor.stat_transport_errors.get("test", 0) == 1`.
- Assert `registry.record_failure.call_count == 1`.

```python
with patch("asyncio.sleep", return_value=None):
    result = await executor._raw_execute("write_file", {})
```

---

**`test_tool_error_calls_record_success`**

- Same setup as `test_http_200_is_error_true_increments_tool_error` (HTTP 200, `is_error=True`).
- Primary assertion: `registry.record_success.call_count == 1` (server responded, so success is recorded).
- Secondary assertion: `registry.record_failure.call_count == 0` (tool error does not affect health state).

This test is a duplicate focus of the first test but emphasizes the HealthRegistry side. Both can exist as separate methods — the plan explicitly lists them as two distinct rows.

---

**Resolver stub for all tests:**

Since `ToolRouteResolver` resolves tool names from the registry, and `write_file` is a known tool, the real resolver should work if `server_configs={"test": cfg}`. However, `ToolRouteResolver` may raise if `write_file` is not in the config's `tool_names`. Use the approach of injecting a mock resolver to avoid import-time dependency on tool constants:

```python
executor._resolver = MagicMock()
executor._resolver.resolve.return_value = "test"
```

This is cleaner than constructing a full registry and matches the `ToolExecutor.__new__` + injection pattern seen in `TestCacheStampede`.

---

**Import notes for `McpServerConfig`:**

`McpServerConfig` is a dataclass in `shared.mcp_config`. Check its fields before constructing. At minimum it needs `url` and `transport`:

```python
from shared.mcp_config import McpServerConfig, McpServerHealthRegistry
cfg = McpServerConfig(url="http://localhost:9999", transport="http")
```

If `McpServerConfig.__init__` requires additional non-default fields, check `scripts/shared/mcp_config.py` and add them.

## Validation plan

```bash
# Run all tests in the file
uv run pytest tests/test_tool_executor.py -v
# Expected: 0 failures; exactly 6 new tests collected under TestToolExecutorErrorBoundary

# Confirm 6 new test names appear
uv run pytest tests/test_tool_executor.py -v 2>&1 | grep "TestToolExecutorErrorBoundary"
# Expected: 6 lines, each PASSED

# Lint check
uv run ruff check tests/test_tool_executor.py
# Expected: 0 errors

# Type check (optional but preferred)
uv run mypy tests/test_tool_executor.py --ignore-missing-imports
# Expected: 0 errors
```
