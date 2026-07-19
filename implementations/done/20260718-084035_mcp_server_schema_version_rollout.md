# Implementation procedure: schema_version rollout across the 9 MCP servers

Source plan: `plans/20260717-131019_plan.md` ("Add MCP tool schema versioning and validation tests"),
Implementation step 2.

Cross-cutting step (touches 9 separate files, none individually large enough to warrant its own doc; a
descriptive slug is used instead of a single file name, per this workflow's convention for multi-file
steps).

## Goal

Update each of the 9 in-scope MCP servers' `/v1/tools` route handler to call the new
`build_tools_response()` helper (added to `scripts/mcp_servers/server.py` per
`implementations/20260718-084001_mcp_servers_server.py.md`) instead of hand-building
`{"tools": [...]}` inline, so every server's `/v1/tools` response now includes
`"schema_version": "1.0"`.

## Scope

**In scope** — exactly these 9 files (matching the plan's own named list; confirmed each exists at this
path and each currently has the identical inline-dict pattern, verified by direct read):

| # | File | Current route lines | Current server_key literal |
|---|---|---|---|
| 1 | `scripts/mcp_servers/mdq/server.py` | 188-192 | `"mdq"` |
| 2 | `scripts/mcp_servers/cicd/server.py` | 80-84 | `"cicd"` |
| 3 | `scripts/mcp_servers/github/server.py` | 125-130 | `"github"` |
| 4 | `scripts/mcp_servers/git/server.py` | 72-76 | `"git"` |
| 5 | `scripts/mcp_servers/web_search/server.py` | 75-80 | `"web_search"` |
| 6 | `scripts/mcp_servers/shell/server.py` | 115-119 | `"shell"` |
| 7 | `scripts/mcp_servers/file/read_server.py` | 234-238 | `"file_read"` |
| 8 | `scripts/mcp_servers/file/write_server.py` | 144-148 | `"file_write"` |
| 9 | `scripts/mcp_servers/file/delete_server.py` | 106-110 | `"file_delete"` |

**Out of scope**
- `scripts/mcp_servers/rag_pipeline/server.py` — has the identical pattern at lines 155-159 but is not one
  of the plan's named 9 servers; explicitly left unchanged (confirmed not a false-positive: the plan's own
  Scope list names exactly these 9, and rag_pipeline is absent from it).
- Any `tools.py` (`TOOL_LIST`) changes — per plan Scope, `schema_version` is a response-wrapper concern
  only; no structural change to per-tool dicts. Existing optional fields (`status`, `is_write`,
  `requires_serial`) already present in some `TOOL_LIST`s (confirmed via grep: `status` present on every
  tool in `mdq`, `cicd`, `git`, `web_search`, `rag_pipeline`; `is_write`/`requires_serial` present on a
  subset, e.g. `mdq/tools.py:106-107,124-125`) are validated as-is by step 4's test suite, not modified
  here.
- `scripts/mcp_servers/server.py` itself — already covered by
  `implementations/20260718-084001_mcp_servers_server.py.md`.

## Assumptions

1. All 9 route handlers follow the byte-for-byte identical pattern (confirmed by direct read of every
   file): a module-level `@app.get("/v1/tools")` async function named `list_tools()`, returning
   `{"tools": [{**t, "server_key": "<literal>"} for t in TOOL_LIST]}`. None currently call
   `MCPServer.list_tools_with_server_key()` (see
   `implementations/20260718-084001_mcp_servers_server.py.md`'s Assumption 1 for why — no server instance
   is available at module import time under normal ASGI serving).
2. Each of the 9 files already imports `TOOL_LIST` from its sibling `tools.py` at module scope (confirmed,
   e.g. `mdq/server.py:45: from mcp_servers.mdq.mdq_tools import TOOL_LIST`). Each file needs exactly one new
   import line (`from mcp_servers.server import build_tools_response`, or a relative-equivalent import
   consistent with each file's existing `from mcp_servers.server import ...` style — several files already
   import `MCPServer`, `attach_auth_middleware`, etc. from `mcp_servers.server`, so this is typically
   extending an existing import statement, not adding a new one).
3. **`git/server.py`'s route handler has a narrower return-type annotation** than the other 8
   (`dict[str, list[dict[str, object]]]` at line 73, vs. `dict[str, Any]` elsewhere, confirmed by direct
   read) — this must widen to `dict[str, Any]` (matching `build_tools_response()`'s own return type) since
   the response will now also contain a top-level `"schema_version": str` key, which does not fit
   `list[dict[str, object]]`. This is the one file requiring a type-annotation edit beyond the route body
   itself.

## Implementation

### Target file

9 files, listed in Scope above.

### Procedure

For each of the 9 files, apply the identical transformation:

1. Add/extend the import from `mcp_servers.server` to include `build_tools_response`.
2. Replace the route handler body:
   - Before (e.g. `mdq/server.py:188-192`):
     ```
     @app.get("/v1/tools")
     async def list_tools() -> dict[str, Any]:
         return {
             "tools": [{**t, "server_key": "mdq"} for t in TOOL_LIST],
         }
     ```
   - After:
     ```
     @app.get("/v1/tools")
     async def list_tools() -> dict[str, Any]:
         return build_tools_response(TOOL_LIST, "mdq")
     ```
   Substitute the file's own existing literal server_key string (from the Scope table) — do not change
   the literal value, only the construction mechanism.
3. For `git/server.py` only: also widen the route function's return-type annotation from
   `dict[str, list[dict[str, object]]]` to `dict[str, Any]` (per Assumption 3).
4. Leave every other part of each file untouched (docstrings on `list_tools()` in `github/server.py` and
   `web_search/server.py` — lines 127 and 77 respectively — are preserved as-is above the new one-line
   body).

### Method

Mechanical, identical edit applied 9 times. No new classes/protocols. No change to `TOOL_LIST` contents,
`dispatch()` methods, or any other route in these files (e.g. `/v1/dispatch`, `/health` are untouched).

### Details

No production code blocks beyond the before/after illustration above (already pseudocode-level, showing
only the route body transformation, not full files).

Net effect per server: `/v1/tools` response body changes from
`{"tools": [{"name": ..., ..., "server_key": "mdq"}, ...]}` to
`{"schema_version": "1.0", "tools": [{"name": ..., ..., "server_key": "mdq"}, ...]}` — additive top-level
key only; existing `tools` array shape is byte-for-byte unchanged, so no consumer that only reads
`response["tools"]` is affected.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/mcp_servers/ && uv run ruff check scripts/mcp_servers/` | 0 errors across all 9 files |
| Type check | `uv run mypy scripts/mcp_servers/` | 0 errors (confirms `git/server.py`'s widened return type is consistent) |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (all imports stay within `mcp_servers` package) |
| Security | `uv run bandit -r scripts/mcp_servers/ -c pyproject.toml` | 0 high/medium |
| Existing server tests | `uv run pytest tests/test_mcp_server_base.py -v` | all pass, including `TestAppModuleImportability` (confirms all 9 `app_module` targets still import cleanly) |
| Per-server manual spot check | `rg -n 'schema_version' scripts/mcp_servers/*/server.py scripts/mcp_servers/file/*.py` | exactly 9 files match (the in-scope set), `rag_pipeline/server.py` does NOT match |
| New schema/validation test suite | `uv run pytest tests/test_mcp_tool_discovery.py -v` | see `implementations/20260718-084145_test_mcp_tool_discovery.py.md` — asserts `schema_version` present per server |
