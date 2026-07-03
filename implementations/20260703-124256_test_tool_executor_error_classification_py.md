## Goal

Add `_http_cfg` / `_make_executor` helpers and `TestToolExecutorErrorClassification` class (7 test methods) to `tests/test_tool_executor.py` to lock down `error_type` classification, stat counters, and `HealthRegistry` recording in `ToolExecutor._raw_execute()`.

## Scope

- In-Scope:
  - Add module-level `_http_cfg` and `_make_executor` helper functions to `tests/test_tool_executor.py` (mirroring the pattern in `tests/test_tool_executor_routing.py`).
  - Append `TestToolExecutorErrorClassification` class with 7 `@pytest.mark.asyncio` test methods after the last existing class in the file.
  - New imports needed: `AsyncMock`, `MagicMock` from `unittest.mock`; `McpServerConfig`, `McpServerHealthRegistry`, `McpServerHealthState`, `TransportType` from `shared.mcp_config`; `time` stdlib module.
- Out-of-Scope:
  - Any changes to `scripts/shared/tool_executor.py`.
  - Any changes to `tests/test_tool_executor_routing.py`.
  - Creating a new test file or modifying `tests/conftest.py`.
  - Modifying existing test classes (`TestCacheStampede`, `TestHttpTransportRetry`, `TestCacheKeyFormat`).

## Assumptions

1. `ToolExecutor.stat_tool_errors` is `dict[str, int]` and `ToolExecutor.stat_transport_errors` is `dict[str, int]`; both are populated by `_record_success()` and `_record_transport_error()` respectively — confirmed at lines 296-297 and 394-410 of `tool_executor.py`.
2. `ToolCallResult.error_type` is `"tool"` when `is_error=True` from transport mock (set via `ToolCallResult.from_transport()`), `"transport"` when `TransportError` is caught in `_raw_execute()`, and `""` on success — confirmed at lines 52, 63, 414 of `tool_executor.py`.
3. A tool-level error (`is_error=True, error_type="tool"`) calls `registry.record_success()` (not `record_failure()`), so health state stays `HEALTHY` — confirmed by `_record_success()` at lines 389-396.
4. `_make_executor` must call the real `ToolExecutor.__init__` (not `__new__`) and pass `set_health_registry(registry)` separately, as the constructor does not accept a `health_registry` kwarg — confirmed at lines 279-332.
5. The `_FakeClient` pattern used in existing `TestHttpTransportRetry` methods is safe to reuse as an inner class per test method.
6. `asyncio.sleep` must be patched at module level (`asyncio.sleep`) for tests exercising retry logic — pattern confirmed at line 105 of `tests/test_tool_executor.py`.
7. `CacheEntry` from `shared.tool_cache` is `dataclass(frozen=True)` with fields `output: str`, `is_error: bool`, `cached_at: float` — confirmed in `scripts/shared/tool_cache.py`.
8. `uv run pytest` is the only required test runner (per plan Assumption 6).
9. `conftest.py` only adds `scripts/` and `tests/` to `sys.path`; no relevant shared fixtures exist for `ToolExecutor` tests.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_tool_executor.py`

### Procedure

1. Read the current end of `tests/test_tool_executor.py` to confirm the final line number and identify the correct insertion point (after `TestCacheKeyFormat`).

2. Add missing imports at the top of the file, after the existing import block:
   ```python
   import time
   from unittest.mock import AsyncMock, MagicMock
   
   import httpx
   from shared.mcp_config import (
       McpServerConfig,
       McpServerHealthRegistry,
       McpServerHealthState,
       TransportType,
   )
   from shared.tool_cache import CacheEntry
   ```
   Note: `httpx` is already imported. `AsyncMock` and `patch` are already imported from `unittest.mock`. Check what is actually missing vs. already present before adding to avoid duplicate imports.

3. Append module-level helpers immediately before `class TestToolExecutorErrorClassification` (after `TestCacheKeyFormat`):
   ```python
   def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
       return McpServerConfig(transport=TransportType.HTTP, url=url)
   
   def _make_executor(
       configs: dict[str, McpServerConfig] | None = None,
   ) -> ToolExecutor:
       http = MagicMock(spec=httpx.AsyncClient)
       return ToolExecutor(
           http,
           cache_ttl=60.0,
           server_configs=configs or {"file_read": _http_cfg()},
       )
   ```
   If module-level `_http_cfg` / `_make_executor` already exist (they do NOT in the current file — only in `test_tool_executor_routing.py`), skip this step.

4. Append `TestToolExecutorErrorClassification` class with the 7 test methods described in the **Method** section below.

5. Run the test file to verify all existing tests still pass before the new ones:
   ```
   uv run pytest tests/test_tool_executor.py -v
   ```

### Method

**Class skeleton:**
```python
class TestToolExecutorErrorClassification:
    """Regression tests: error_type classification, stat counters, and HealthRegistry
    recording in ToolExecutor._raw_execute()."""
```

**2a — `test_http_200_success_error_type_empty`**
```python
@pytest.mark.asyncio
async def test_http_200_success_error_type_empty(self) -> None:
    registry = McpServerHealthRegistry(failure_threshold=3)
    ex = _make_executor()
    ex.set_health_registry(registry)
    mock_transport = AsyncMock()
    mock_transport.call = AsyncMock(
        return_value=ToolCallResult(
            output="ok", is_error=False, request_id="req-1",
            server_key="file_read", error_type=""
        )
    )
    ex._transports["file_read"] = mock_transport

    result = await ex._raw_execute("read_text_file", {})

    assert result.is_error is False
    assert result.error_type == ""
    assert registry.get_state("file_read") == McpServerHealthState.HEALTHY
```

**2b — `test_http_200_tool_error_increments_stat_tool_errors`**
```python
@pytest.mark.asyncio
async def test_http_200_tool_error_increments_stat_tool_errors(self) -> None:
    registry = McpServerHealthRegistry(failure_threshold=3)
    ex = _make_executor()
    ex.set_health_registry(registry)
    mock_transport = AsyncMock()
    mock_transport.call = AsyncMock(
        return_value=ToolCallResult(
            output="tool error msg", is_error=True, request_id="",
            server_key="file_read", error_type="tool"
        )
    )
    ex._transports["file_read"] = mock_transport

    result = await ex._raw_execute("read_text_file", {})

    assert result.is_error is True
    assert result.error_type == "tool"
    assert ex.stat_tool_errors.get("file_read", 0) == 1
    assert registry.get_state("file_read") == McpServerHealthState.HEALTHY
```

**2c — `test_http_500_transport_error_classification`**
```python
@pytest.mark.asyncio
async def test_http_500_transport_error_classification(self) -> None:
    registry = McpServerHealthRegistry(failure_threshold=3)
    ex = _make_executor()
    ex.set_health_registry(registry)
    mock_transport = AsyncMock()
    mock_transport.call = AsyncMock(
        side_effect=TransportError("HTTP 500")
    )
    ex._transports["file_read"] = mock_transport

    result = await ex._raw_execute("read_text_file", {})

    assert result.is_error is True
    assert result.error_type == "transport"
    assert ex.stat_transport_errors.get("file_read", 0) == 1
    assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
```

**2d — `test_http_503_retry_exhaustion_is_transport_error`**

Use a real `HttpTransport` with a `_FakeClient` that always returns 503, inject into `ex._transports`, and patch `asyncio.sleep`.

```python
@pytest.mark.asyncio
async def test_http_503_retry_exhaustion_is_transport_error(self) -> None:
    registry = McpServerHealthRegistry(failure_threshold=3)
    ex = _make_executor()
    ex.set_health_registry(registry)

    class _FakeClient503:
        async def post(self, url: str, **kw: Any) -> httpx.Response:
            req = httpx.Request("POST", url)
            return httpx.Response(
                503, request=req, json={"result": "", "is_error": False}
            )

    transport = HttpTransport(
        _FakeClient503(),  # type: ignore[arg-type]
        base_url="http://127.0.0.1:8000",
        server_key="file_read",
    )
    ex._transports["file_read"] = transport

    with patch("asyncio.sleep", return_value=None):
        result = await ex._raw_execute("read_text_file", {})

    assert result.error_type == "transport"
    assert ex.stat_transport_errors.get("file_read", 0) == 1
    assert "Retry exhausted" in result.output
```

**2e — `test_timeout_is_transport_error`**
```python
@pytest.mark.asyncio
async def test_timeout_is_transport_error(self) -> None:
    registry = McpServerHealthRegistry(failure_threshold=3)
    ex = _make_executor()
    ex.set_health_registry(registry)

    class _FakeClientTimeout:
        async def post(self, url: str, **kw: Any) -> httpx.Response:
            raise httpx.TimeoutException("timed out")

    transport = HttpTransport(
        _FakeClientTimeout(),  # type: ignore[arg-type]
        base_url="http://127.0.0.1:8000",
        server_key="file_read",
    )
    ex._transports["file_read"] = transport

    result = await ex._raw_execute("read_text_file", {})

    assert result.error_type == "transport"
    assert ex.stat_transport_errors.get("file_read", 0) == 1
    assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
```

**2f — `test_malformed_response_is_transport_error`**

Parametrize over three malformed response bodies. Each must return HTTP 200 with a body that causes `_parse_http_response` to raise `ValueError`, which is caught in `HttpTransport.call` as `(httpx.RequestError, ValueError)` and re-raised as `TransportError`.

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        b"[1, 2]",                           # non-dict JSON
        b'{"is_error": false}',              # missing 'result' key
        b'{"result": "x", "is_error": 1}',  # non-bool is_error
    ],
)
async def test_malformed_response_is_transport_error(
    self, body: bytes
) -> None:
    registry = McpServerHealthRegistry(failure_threshold=3)
    ex = _make_executor()
    ex.set_health_registry(registry)

    class _FakeClientMalformed:
        async def post(self, url: str, **kw: Any) -> httpx.Response:
            req = httpx.Request("POST", url)
            return httpx.Response(200, request=req, content=body)

    transport = HttpTransport(
        _FakeClientMalformed(),  # type: ignore[arg-type]
        base_url="http://127.0.0.1:8000",
        server_key="file_read",
    )
    ex._transports["file_read"] = transport

    result = await ex._raw_execute("read_text_file", {})

    assert result.error_type == "transport"
    assert ex.stat_transport_errors.get("file_read", 0) == 1
```

**2g — `test_cache_hit_no_health_registry_update`**

Pre-populate `_cache` with a valid `CacheEntry` (TTL large enough not to expire); attach `McpServerHealthRegistry`; call `_execute_with_cache`; confirm `stat_cache_hits == 1` and registry stays HEALTHY without any transport mock call.

```python
@pytest.mark.asyncio
async def test_cache_hit_no_health_registry_update(self) -> None:
    registry = McpServerHealthRegistry(failure_threshold=3)
    ex = _make_executor()
    ex._cache_ttl = 3600.0
    ex.set_health_registry(registry)

    cache_key = 'read_text_file:{}'  # _json_dumps({}) == '{}'
    ex._cache[cache_key] = CacheEntry(
        output="cached", is_error=False, cached_at=time.time()
    )

    result = await ex._execute_with_cache("read_text_file", {})

    assert result.request_id == ""
    assert ex.stat_cache_hits == 1
    assert registry.get_state("file_read") == McpServerHealthState.HEALTHY
```

### Details

- The `_make_executor` helper defined here is functionally identical to the one in `test_tool_executor_routing.py` (lines 34-44). It is duplicated per the plan's Assumption 2 — no shared conftest needed.
- `ex._transports["file_read"]` injection works because `_transports` is a plain `dict`; confirmed in `_raw_execute()` at line 472.
- For test 2d, `HttpTransport` is imported already at the top of the file (`from shared.tool_executor import HttpTransport, ...`). No new imports needed for this.
- The `_json_dumps({})` cache key value: import `_json_dumps` from `shared.json_utils` or `shared.tool_executor` to compute the exact cache key rather than hard-coding `'{}'`. Alternatively, call `_json_dumps({})` directly. The existing `TestCacheKeyFormat` class already imports it: `from shared.tool_executor import _json_dumps`.
- For test 2g, import `from shared.tool_cache import CacheEntry` is needed.
- Test 2f's `@pytest.mark.parametrize` must be placed BEFORE `@pytest.mark.asyncio` or in either order — both orderings are supported by pytest-asyncio.
- `httpx.TimeoutException` is the base class; subclasses include `ReadTimeout`, `ConnectTimeout` etc. Using the base class is sufficient for test 2e since `HttpTransport.call` catches `httpx.TimeoutException` specifically at line 182.
- The `error_type` field default on `ToolCallResult` is `""` — confirmed at line 52. A mock that returns `ToolCallResult(..., error_type="")` is explicit and correct.
- `registry.get_state("file_read")` returns `McpServerHealthState.HEALTHY` for a new registry regardless of key — confirmed in `test_tool_executor_routing.py` line 448: `r.get_state("srv") == McpServerHealthState.HEALTHY` for any unrecorded key.

## Validation plan

| Check | Command | Expected outcome |
|-------|---------|------------------|
| New class only | `uv run pytest tests/test_tool_executor.py::TestToolExecutorErrorClassification -v` | 9 tests (7 methods + 3 parametrize cases for 2f) passed, 0 failed |
| Full file no regressions | `uv run pytest tests/test_tool_executor.py -v` | All existing 10 + 7 new = 17 tests passed (note: 2f counts as 3 parametrize variants) |
| Routing tests unaffected | `uv run pytest tests/test_tool_executor_routing.py -v` | All existing tests passed |
| Type check | `uv run mypy scripts/shared/tool_executor.py tests/test_tool_executor.py` | No new errors |
| Lint | `uv run ruff check tests/test_tool_executor.py` | No violations |
