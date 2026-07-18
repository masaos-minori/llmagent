# Implementation procedure: `scripts/mcp_servers/server.py` (schema_version constant + response helper)

Source plan: `plans/20260717-131019_plan.md` ("Add MCP tool schema versioning and validation tests"),
Implementation step 1.

## Goal

Add a shared `MCP_TOOL_SCHEMA_VERSION` constant and a shared response-building function to
`scripts/mcp_servers/server.py` (the base `MCPServer` class module), so every MCP server's `/v1/tools`
route handler can produce a response of the shape `{"schema_version": "1.0", "tools": [...]}` from one
single source of truth, instead of each server hand-building `{"tools": [...]}` independently. This is the
foundation step for plan step 2 (rollout to the 9 servers).

## Scope

**In scope**
- `scripts/mcp_servers/server.py`: add `MCP_TOOL_SCHEMA_VERSION: str = "1.0"` module-level constant.
- `scripts/mcp_servers/server.py`: add a new plain function (NOT an instance method — see Assumptions for
  why) that wraps a tool list and a server_key into the full `/v1/tools` response dict, including
  `schema_version`.

**Out of scope**
- Updating the 9 individual servers to call this new function — tracked separately in
  `implementations/20260718-084500_mcp_server_schema_version_rollout.md` (plan step 2).
- Any change to `MCPServer.list_tools_with_server_key()` (lines 128-136) itself — it is left untouched;
  the new function is additive, not a replacement of that method (see Assumptions).
- `rag_pipeline/server.py` — has an identical `/v1/tools` route pattern (confirmed by direct read,
  `rag_pipeline/server.py:155-159`) but is **not** one of the plan's named 9 servers and is explicitly out
  of scope for this whole plan; it will not gain `schema_version` under this change.

## Assumptions

1. **`list_tools_with_server_key()` (lines 128-136, confirmed by direct read) is currently uncalled by any
   of the 9 in-scope servers' actual `/v1/tools` route handlers.** Investigation (direct grep + read of
   all 9 servers, e.g. `mdq/server.py:188-192`, `git/server.py:72-76`) shows every server's `list_tools()`
   route function is a **module-level** function attached to a module-level `app = FastAPI(...)` object,
   defined and used entirely independently of any `MCPServer` subclass instance. Each one inlines
   `[{**t, "server_key": "<literal>"} for t in TOOL_LIST]` directly rather than calling
   `self.list_tools_with_server_key()`. This matters because **the plan's own Assumption 1 and Design text
   propose an instance method** (`list_tools_response()` on `MCPServer`, called via `self...`) — but no
   `self` (`MCPServer` subclass instance) is available in the module-level route function under normal
   ASGI serving. Confirmed via `mdq/server.py:312-314`: the only place a server instance is constructed
   (`server = MdqMCPServer()`) is inside `if __name__ == "__main__":`, which does **not** run when uvicorn
   imports the module by `app_module` string (e.g. `"mcp_servers.mdq.server:app"`, the actual production
   launch path per `MdqMCPServer.app_module` at `mdq/server.py:300`). An instance method design would
   therefore be uncallable from the real route handlers without constructing a throwaway instance per
   request (wasteful and pointless, since the method reads only class attributes).
   **Resolution (deviates from the plan's literal Design wording, but implements its intent):** define the
   new response-builder as a **plain module-level function** in `scripts/mcp_servers/server.py`, taking
   `tools` and `server_key` as parameters, so it is trivially importable and callable from each server's
   existing module-level route function with no instance required. This is flagged explicitly per this
   workflow's convention for plan-vs-reality drift — the plan's acceptance criteria (a `schema_version` key
   in the response, single point of truth) are still fully satisfied; only the exact code shape changes.
2. `MCP_TOOL_SCHEMA_VERSION = "1.0"` matches the plan's own Unknown resolution (a shared constant, not 9
   independent literals) — confirmed no existing `schema_version` constant or literal exists anywhere
   under `scripts/mcp_servers/` today (grep returned zero hits).

## Implementation

### Target file

`scripts/mcp_servers/server.py`

### Procedure

1. Add near the top of the file, alongside the existing `MCP_MAX_RESPONSE_BYTES` constant (line 32):
   ```
   # Schema version advertised in each server's /v1/tools response; bump when the tool-schema
   # shape changes in a way that matters to Agent-side discovery/validation.
   MCP_TOOL_SCHEMA_VERSION: str = "1.0"
   ```
2. Add a new plain function after `list_tools_with_server_key()` (after line 136), at module scope (not a
   method — see Assumption 1):
   ```
   def build_tools_response(tools: list[dict[str, Any]], server_key: str) -> dict[str, Any]:
       """Build the /v1/tools response dict: schema_version + per-tool server_key tagging.

       Callable directly from each server's module-level FastAPI route handler (no MCPServer
       instance required) — see docstring on MCP_TOOL_SCHEMA_VERSION for the versioning contract.
       """
       ...
   ```
3. Do **not** modify `list_tools_with_server_key()` itself — it remains as-is (used elsewhere, e.g.
   potentially by future startup tool discovery per its own docstring at lines 129-132); `build_tools_response`
   is a new, additive, free function with a different call signature (explicit `tools`/`server_key` params
   rather than reading `self.mcp_tools`/`self.server_key`), suited to being called from a module-level
   route with only `TOOL_LIST` and a literal server_key string in scope.

### Method

Plain function, no `Protocol`/`ABC`/dataclass. Pure, side-effect-free, synchronous — matches the style of
the existing `list_tools_with_server_key()` and `_truncate_with_meta()` in the same file.

### Details

Pseudocode / signature only (no production code):

```
MCP_TOOL_SCHEMA_VERSION: str = "1.0"


def build_tools_response(tools: list[dict[str, Any]], server_key: str) -> dict[str, Any]: ...
    # return {
    #     "schema_version": MCP_TOOL_SCHEMA_VERSION,
    #     "tools": [{**t, "server_key": server_key} for t in tools],
    # }
```

Type: `tools: list[dict[str, Any]]` (the server's `TOOL_LIST`), `server_key: str` (the literal key each
server currently hardcodes inline, e.g. `"mdq"`, `"git"`). Return type `dict[str, Any]` — matches the
existing route handlers' own return annotations (`dict[str, Any]` in 8 of 9 files; `git/server.py:73` uses
`dict[str, list[dict[str, object]]]` today, which will need to widen to `dict[str, Any]` once it returns a
dict with a `schema_version: str` key alongside `tools: list[...]` — flagged for the rollout doc since it
touches that file, not this one).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/mcp_servers/server.py && uv run ruff check scripts/mcp_servers/server.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/server.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no new imports added) |
| Security | `uv run bandit -r scripts/mcp_servers/server.py -c pyproject.toml` | 0 high/medium |
| Existing base tests | `uv run pytest tests/test_mcp_server_base.py -v` | all pass, no regressions (new function is additive; `list_tools()`/`list_tools_with_server_key()` unchanged) |
| No accidental instance-method coupling | `rg -n "def build_tools_response" scripts/mcp_servers/server.py` | confirms it is defined at module scope, not inside `class MCPServer:` |
