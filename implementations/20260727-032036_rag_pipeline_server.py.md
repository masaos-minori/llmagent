## Goal

Add missing `schema_version` to rag_pipeline MCP server `/v1/tools` endpoint by replacing manual dict construction with `build_tools_response()`.

## Scope

**In-Scope:**
- Add `from mcp_servers.server import build_tools_response` import to `rag_pipeline_server.py`
- Replace `list_tools()` return statement with `return build_tools_response(TOOL_LIST, "rag_pipeline")`

**Out-of-Scope:**
- Any other changes to the rag_pipeline MCP server beyond this one method

## Assumptions

1. `TOOL_LIST` is already defined in the module and contains the same tool definitions
2. `build_tools_response()` returns a dict with `schema_version` and `tools` keys matching the expected format

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether `build_tools_response` can be safely imported from `mcp_servers.server` without circular dependency | Check if other MCP servers already import from `mcp_servers.server` | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` — add import; replace `list_tools()` return

- **Blast Radius:**
  - Very low churn — single method change only
  - No behavioral change for clients since `schema_version` was previously absent (not a regression)

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `rag_pipeline_server.py`:
```python
# Current (missing schema_version):
async def list_tools() -> dict[str, Any]:
    """List available RAG tools with server_key="rag_pipeline"."""
    return {
        "tools": [{**t, "server_key": "rag_pipeline"} for t in TOOL_LIST],
    }

# Proposed fix:
async def list_tools() -> dict[str, Any]:
    """List available RAG tools with server_key="rag_pipeline"."""
    return build_tools_response(TOOL_LIST, "rag_pipeline")
```

Other MCP servers follow the same pattern (e.g., mdq_server.py, shell_server.py, web_search_server.py).

## Implementation

### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure
1. Open `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
2. Locate existing imports section
3. Add `from mcp_servers.server import build_tools_response` to imports
4. Locate line 163: `async def list_tools() -> dict[str, Any]:`
5. Replace lines 164-167 with `return build_tools_response(TOOL_LIST, "rag_pipeline")`
6. Save the file

### Method
Replace manual dict construction with `build_tools_response()` helper function.

### Details
- Add import: `from mcp_servers.server import build_tools_response`
- Replace `list_tools()` body:
  ```python
  # Before:
  return {
      "tools": [{**t, "server_key": "rag_pipeline"} for t in TOOL_LIST],
  }
  
  # After:
  return build_tools_response(TOOL_LIST, "rag_pipeline")
  ```

## Compatibility considerations

N/A — adds `schema_version` field which was previously missing (non-breaking addition)

## Security considerations

N/A

## Rollback considerations

- Simple revert: restore original `list_tools()` body and remove import

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Verify schema_version present in response | `uv run pytest -k "schema_version" tests/test_mcp_tools_validation.py -v` | Test passes |
| Full test suite | No regressions | `uv run pytest -q` | Pass count unchanged |

## Out of scope

- Any other changes to the rag_pipeline MCP server beyond this one method

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-164032_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-032036
- Related target files: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py, scripts/mcp_servers/server.py
