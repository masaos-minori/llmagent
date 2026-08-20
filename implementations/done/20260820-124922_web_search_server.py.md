# Implementation Procedure: Add availability check and gating to web-search-mcp

## Goal
Add `enabled`/`disabled_reason` fields to every tool in the `GET /v1/tools` response of web-search-mcp and gate `POST /v1/call_tool` so a disabled tool is rejected before dispatch.

## Scope
- Target file: `scripts/mcp_servers/web_search/web_search_server.py`
- Add availability check function `_web_search_tool_availability()`
- Replace `list_tools()` to return hand-built annotated response (bypassing `build_tools_response()`)
- Add server-side gate in `call_tool()` before dispatch

## Assumptions
- Follow the existing pattern from git-mcp (`_git_tool_availability`) and file servers (`availability_flags`)
- `browser_fetch` is gated on `_cfg.browser_allowed_domains` being non-empty
- `search_web` is always enabled `(True, "")`
- Must bypass `build_tools_response()` with default `include_disabled=False` to avoid silently dropping disabled tools
- Place call_tool gate before the existing `try` block to avoid misclassification in audit log

## Design decisions
- Mirror `git_server.py`'s `_git_tool_availability` function signature
- Hand-build the `/v1/tools` response dict with `enabled`/`disabled_reason` for each tool
- Gate in `call_tool()` computes availability and returns `CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)` before dispatch
- Keep `MCP_TOOL_SCHEMA_VERSION` at "1.0" (precedent from git-mcp/file-servers)

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure
1. Add `_web_search_tool_availability(cfg, tool_name)` function after `_cfg` definition (around line 50)
2. Replace `list_tools()` endpoint (lines 172-175) with hand-built annotated response
3. Add disabled-tool gate at the start of `call_tool()` (before line 198's `try` block)

### Method
Direct code modifications using exact line matching

### Details

**1. Add availability function (after line 49, before `app = FastAPI(...)`):**
```python
def _web_search_tool_availability(cfg: WebSearchConfig, tool_name: str) -> tuple[bool, str]:
    """Return (enabled, disabled_reason) for a single web-search tool by name."""
    if tool_name == "browser_fetch" and not cfg.browser_allowed_domains:
        return False, "browser_allowed_domains is empty"
    return True, ""
```

**2. Replace `list_tools()` (lines 172-175):**
```python
@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """Return tool names and descriptions for agent.json definition validation."""
    return {
        "schema_version": MCP_TOOL_SCHEMA_VERSION,
        "tools": [
            {**t, "server_key": "web_search", "enabled": enabled, "disabled_reason": reason}
            for t in TOOL_LIST
            for enabled, reason in [_web_search_tool_availability(_cfg, t["name"])]
        ],
    }
```

**3. Add gate in `call_tool()` (before line 198 `try:`):**
```python
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Execute a web-search-mcp tool (search_web or browser_fetch) by name and
    return the formatted text result.

    `outcome`/`error_type`/`latency_ms` here are for the always-fires audit
    log only — health/metrics recording is owned entirely by
    `service.search_web()`/`service.fetch_browser()` (called via
    `dispatch_web_tool` -> `fdisp_search_web`/`fdisp_browser_fetch`), so this
    function must not call `health.record_*`/`metrics.record_*` itself (that
    would double-count every query).
    """
    # Disabled-tool gate — must come BEFORE the try block so a disabled-tool
    # rejection is not misclassified into the audit log's error-type taxonomy
    enabled, reason = _web_search_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)

    session_id, request_id = extract_request_context(request)
    t0 = time.perf_counter()
    # ... rest of existing function unchanged
```

## Compatibility considerations
- Output format changes: `/v1/tools` now includes `enabled`/`disabled_reason` for every tool
- Disabled tools appear in response with `enabled=false` (not dropped)
- `POST /v1/call_tool` returns `is_error=True` with exact reason string for disabled tools
- No change to `MCP_TOOL_SCHEMA_VERSION` (precedent: git-mcp/file-servers ship these fields at "1.0")

## Security considerations
- Fail-closed: `browser_fetch` disabled when `browser_allowed_domains` is empty
- Gate before audit/log path prevents misclassification

## Rollback considerations
- Git revert of this file if issues arise
- No database schema or config changes

## Validation plan
- Run `uv run pytest tests/mcp_servers/web_search/test_web_search_server.py -v` - no regressions
- Add new test file `tests/mcp_servers/web_search/test_web_search_tools_endpoint.py` (separate procedure)
- Run full validation sequence per rules/toolchain.md

## Out of scope
- Tests (separate procedure)
- shell/cicd/rag_pipeline/mdq servers (explicitly out of scope)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-214118_require.md
- Source plan: plans/20260819-164001_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-124922
- Related target files: scripts/mcp_servers/web_search/web_search_server.py