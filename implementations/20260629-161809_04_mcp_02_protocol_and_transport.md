# Implementation: HealthRegistry Error Classification and Integration Tests

## Goal

Verify that the existing HealthRegistry update path is correct, document the per-error-class behavior explicitly, and add missing end-to-end integration tests for DEGRADED/UNAVAILABLE/HALF_OPEN recovery transitions through ToolExecutor.

## Scope

- **In-Scope**:
  - Code verification: `shared/tool_executor.py` and `shared/mcp_config.py` (read-only audit)
  - Doc updates: add error-class classification table to `04_mcp_02_protocol_and_transport.md`
  - Doc updates: add watchdog-HealthRegistry interaction note to `04_mcp_06_configuration_and_operations.md`
  - Test additions: end-to-end ToolExecutor health-state transition tests in `tests/test_tool_executor_routing.py` covering HTTP 4xx, 5xx, timeout, connection refused, malformed response, and tool-level error
- **Out-of-Scope**:
  - Restarting servers on tool-level errors
  - Changing tool validation behavior
  - Any changes to `shared/mcp_config.py` implementation logic

## Assumptions

- The implementation in `tool_executor.py` is already correct: `TransportError` is always raised for transport failures and caught by `_raw_execute()`, which calls `record_failure()`; tool-level errors call `record_success()`.
- The requirement's "Problem" section describes a risk that was resolved (per the doc note "Resolved 2026-06-18"), not a current bug.
- The remaining work is: (a) document the per-error-class classification explicitly, and (b) add integration-level test coverage for the full state-machine (HEALTHY → DEGRADED → UNAVAILABLE → HALF_OPEN → HEALTHY).

## Implementation

### Target file: `scripts/shared/tool_executor.py` (read-only)

#### Procedure

Read-only audit — confirm all six error classes reach HealthRegistry correctly:
1. HTTP 4xx (non-retryable, e.g. 401/403/404) → TransportError → record_failure()
2. HTTP 5xx → TransportError → record_failure()
3. Timeout (httpx.TimeoutException) → TransportError → record_failure()
4. Connection refused (httpx.RequestError) → TransportError → record_failure()
5. DNS/network errors (httpx.RequestError) → TransportError → record_failure()
6. Malformed responses (ValueError from _parse_http_response) → TransportError → record_failure()

### Target file: `scripts/shared/mcp_config.py` (read-only)

#### Procedure

Read-only audit — confirm no logic changes needed.

### Target file: `docs/04_mcp_02_protocol_and_transport.md`

#### Procedure

Add "Error Classification Table" to §Common Error Shape, explicitly listing each error type and mapping each to: `error_type`, `HealthRegistry action`, `request_id`, `is_retryable`.

#### Method

Direct file edit — add new table section.

#### Details

**Add after the existing Common Error Shape section:**
```markdown
### Error Classification Table

| Error Type | HTTP Status | HealthRegistry Action | request_id | is_retryable |
|---|---|---|---|---|
| HTTP 4xx (non-retryable: 401/403/404) | 4xx | `record_failure()` | `""` | No |
| HTTP 5xx (server error) | 5xx | `record_failure()` | `""` | Yes (with backoff) |
| Timeout | N/A | `record_failure()` | `""` | Yes (with backoff) |
| Connection refused | N/A | `record_failure()` | `""` | No |
| DNS/network error | N/A | `record_failure()` | `""` | No |
| Malformed response (non-dict, missing 'result') | 200 | `record_failure()` | `""` | No |

All transport failures set `request_id=""` because the request never completed successfully. Tool-level errors (HTTP 200 with `is_error=True`) use the actual request_id from the server response and call `record_success()`.
```

### Target file: `docs/04_mcp_06_configuration_and_operations.md`

#### Procedure

Add note clarifying that the watchdog's `record_success()`/`record_failure()` calls supplement (not replace) the per-call HealthRegistry updates from `ToolExecutor`.

#### Method

Direct file edit — add new paragraph.

#### Details

**Add in the appropriate section:**
```markdown
**Note:** The watchdog's periodic `record_success()`/`record_failure()` calls supplement (but do not replace) the per-call HealthRegistry updates from `ToolExecutor._raw_execute()`. Each tool call increments its own failure count independently of the watchdog.
```

### Target file: `tests/test_tool_executor_routing.py`

#### Procedure

Add class `TestToolExecutorHealthTransitions` with 5 new test cases for specific error classes at the ToolExecutor level.

#### Method

Direct file edit — add new test class after existing `TestToolExecutorHealthGate` class.

#### Details

**Add after line 874 (after `test_half_open_allows_trial_dispatch`):**
```python
class TestToolExecutorHealthTransitions:
    """End-to-end health-state transitions through ToolExecutor for specific error classes."""

    @pytest.mark.asyncio
    async def test_http_4xx_triggers_record_failure(self) -> None:
        """HTTP 4xx triggers TransportError → record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)

        mock_transport = AsyncMock()
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        resp_obj = httpx.Response(401, request=req)
        mock_transport.call = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "client error", request=req, response=resp_obj
            )
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
        assert "401" in res.output or "client error" in res.output.lower()

    @pytest.mark.asyncio
    async def test_http_5xx_triggers_record_failure(self) -> None:
        """HTTP 5xx triggers TransportError → record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)

        mock_transport = AsyncMock()
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        resp_obj = httpx.Response(500, request=req)
        mock_transport.call = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "server error", request=req, response=resp_obj
            )
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
        assert "500" in res.output or "server error" in res.output.lower()

    @pytest.mark.asyncio
    async def test_timeout_triggers_record_failure(self) -> None:
        """Timeout triggers TransportError → record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)

        mock_transport = AsyncMock()
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        mock_transport.call = AsyncMock(
            side_effect=httpx.TimeoutException("timeout", request=req)
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
        assert "timeout" in res.output.lower()

    @pytest.mark.asyncio
    async def test_connection_refused_triggers_record_failure(self) -> None:
        """Connection refused triggers TransportError → record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)

        mock_transport = AsyncMock()
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        mock_transport.call = AsyncMock(
            side_effect=httpx.ConnectError("refused", request=req)
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
        assert "refused" in res.output.lower()

    @pytest.mark.asyncio
    async def test_malformed_response_triggers_record_failure(self) -> None:
        """Malformed response triggers TransportError → record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)

        mock_transport = AsyncMock()
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        resp_obj = httpx.Response(200, request=req, content=b"not-json")
        mock_transport.call = AsyncMock(return_value=resp_obj)
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED

    @pytest.mark.asyncio
    async def test_tool_error_does_not_trigger_record_failure(self) -> None:
        """Tool-level error (HTTP 200 with is_error=True) calls record_success(), not record_failure()."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="tool error", is_error=True, request_id="req-1", server_key="file_read"
            )
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        # Tool-level error should NOT increment failure count — record_success() is called
        assert registry.get_state("file_read") == McpServerHealthState.HEALTHY
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `shared/tool_executor.py` + `shared/mcp_config.py` | Unit: ToolExecutor._raw_execute + McpServerHealthRegistry state machine | `uv run pytest tests/test_tool_executor_routing.py -v` | All existing tests pass; new tests pass |
| `docs/04_mcp_02_protocol_and_transport.md` | Doc consistency check | `uv run python scripts/check_mcp_docs_consistency.py` (if applicable) | No inconsistencies reported |
| Error classification (4xx/5xx/timeout/connect/dns/malformed) | Unit: HttpTransport isolation tests already in `TestHttpTransportErrors`; add ToolExecutor-level tests | `uv run pytest tests/test_tool_executor_routing.py::TestToolExecutorHealthTransitions -v` | All 5 new tests pass |
| Full test suite regression | All tests | `uv run pytest` | No regressions |
