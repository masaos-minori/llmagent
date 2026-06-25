# tests/integration/test_agent_mcp_integration.py — Agent Loop <-> MCP Servers integration tests

**Plan:** `plans/20260625-095157_plan.md` (req #71)
**Target:** `tests/integration/test_agent_mcp_integration.py` (new file)

## Priority: P1 (Critical)

## Test cases to implement

- **TC-A01**: HTTP tool call succeeds — POST returns `{"result": "ok", "is_error": false}`
- **TC-A02**: HTTP 504 gateway timeout — `TransportError`; `error_type="transport"`
- **TC-A03**: HTTP timeout (`httpx.TimeoutException`) — same as TC-A02; no retry
- **TC-A04**: HTTP 503 → retry → success — success on 3rd attempt; stat not incremented
- **TC-A05**: HTTP tool error (`is_error=True`) — `error_type="tool"`; `record_success()` called
- **TC-A06**: stdio pipe closes during call — `TransportError`; `error_type="transport"`
- **TC-A07**: stdio response timeout — `TransportError("stdio server timeout")`
- **TC-A08**: stdio malformed JSON — `TransportError` from `orjson.JSONDecodeError`
- **TC-A09**: Response ID mismatch (stdio) — `TransportError("Response ID mismatch")`
- **TC-A10**: Health check fails → call rejected — no transport call made
- **TC-A11**: Plugin tool write error — `ToolCallResult(is_error=True)` without propagation
- **TC-A12**: Concurrent HTTP calls — all 5 complete; semaphore limits concurrency

## Key fixtures needed

- `server_cfg`: `McpServerConfig` with `transport="stdio"` or `transport="http"`
- `stdio_echo_proc`: minimal subprocess (see plan §1b for script)
- `executor_with_stdio`: `ToolExecutor` wired to stdio echo proc

## Mocking approach

- HTTP: `respx` or `httpx.MockTransport`; see plan §1a
- stdio: subprocess with inline Python script; see plan §1b
- Transport errors: `side_effect=httpx.ConnectError` / `httpx.TimeoutException`

## Full example skeleton

See plan §4 for the complete test skeleton including TC-A01, TC-A06, TC-A09, TC-B04, TC-C04.

## Validation

```
uv run pytest tests/integration/test_agent_mcp_integration.py -v --timeout=30
```
