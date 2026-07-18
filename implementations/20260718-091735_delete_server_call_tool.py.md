# Implementation: scripts/mcp_servers/file/delete_server.py — disabled-tool gate + validate_args() on /v1/call_tool

Source plan: `plans/20260717-174848_plan.md` ("Reject disabled tools before dispatch in
/v1/call_tool and clarify validation policy")

Note on filename disambiguation: an existing doc `20260718-090653_delete_server.py.md`
matches `delete_server.py` by substring, but its Goal is scoped to `GET /v1/tools`
merging `enabled`/`disabled_reason` (requirement 15, `plans/20260717-174024_plan.md`),
explicitly excluding "any other endpoint in this file". Does not cover this plan's
`call_tool()` feature. This doc uses the disambiguated slug `delete_server_call_tool.py`.

## Goal

Make `POST /v1/call_tool` on the file-delete server (port 8008) reject disabled tools
before dispatch — returning `CallToolResponse(result="Tool disabled: <reason>",
is_error=True)` when `_cfg.allowed_dirs` is empty — and call `req.validate_args()`
before dispatch, converting any raised `ValueError` into
`CallToolResponse(result=f"Validation error: {e}", is_error=True)`.

## Scope

**In scope**: the `call_tool()` handler (currently lines 113-116) in
`scripts/mcp_servers/file/delete_server.py` only.

**Out of scope**: `list_tools()` (covered by sibling doc
`20260718-090653_delete_server.py.md` for requirement 15 — unaffected here),
`_dispatch_delete_tool()` (no change), `delete_models.py` (no schema change),
`delete_tools.py` (`TOOL_LIST` stays static).

**Depends on**: `availability_flags(allowed_dirs: list[str]) -> tuple[bool, str]` in
`scripts/mcp_servers/file/common.py` (see `20260718-090551_common.py.md`) — apply that
change first, or confirm via
`grep -n "def availability_flags" scripts/mcp_servers/file/common.py` that it already
landed.

## Assumptions

- Current handler (verified exact content, lines 113-116):
  ```
  @app.post("/v1/call_tool", response_model=CallToolResponse)
  async def call_tool(req: CallToolRequest) -> CallToolResponse:
      r = await _dispatch_delete_tool(req.name, req.args)
      return _to_call_tool_response(r)
  ```
- `CallToolRequest` / `CallToolResponse` already imported (line 42:
  `from mcp_servers.models import CallToolRequest, CallToolResponse`).
- `_cfg = FileDeleteConfig.load()` already exists at module level (line 47);
  `FileDeleteConfig.allowed_dirs: list[str]` (confirmed `delete_models.py:27`).
- `req.validate_args()` (`scripts/mcp_servers/models.py:30-37`) already exists, raises
  `ValueError` on invalid args, no-op when no validator registered. No changes needed to
  `models.py` or `tool_validators.py`.
- All tools in this server share one enabled/disabled state (uniform
  `availability_flags(_cfg.allowed_dirs)` check, no per-tool-name branch), same as
  `read_server.py`/`write_server.py`.

## Implementation

### Target file

`/home/sugimoto/llmagent/scripts/mcp_servers/file/delete_server.py`

### Procedure

1. Add `availability_flags` to the existing
   `from mcp_servers.file.common import (...)` block (lines 24-31).
2. Rewrite the `call_tool()` handler body (lines 114-116):
   - Compute `enabled, reason = availability_flags(_cfg.allowed_dirs)` first.
   - If not enabled, return `CallToolResponse(result=f"Tool disabled: {reason}",
     is_error=True)` immediately.
   - Otherwise, call `req.validate_args()` in `try/except ValueError as e`; on exception
     return `CallToolResponse(result=f"Validation error: {e}", is_error=True)`.
   - Otherwise, proceed with the existing `_dispatch_delete_tool(req.name, req.args)`
     call and `_to_call_tool_response(r)` return, unchanged.
3. No change to the decorator or function signature.

### Method

Pseudocode (no production code blocks per design-doc convention):

```
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    enabled, reason = availability_flags(_cfg.allowed_dirs)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    try:
        req.validate_args()
    except ValueError as e:
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    r = await _dispatch_delete_tool(req.name, req.args)
    return _to_call_tool_response(r)
```

### Details

- Ordering: disabled-tool check, then `validate_args()`, then dispatch — matches the
  plan's Design section.
- Exact literal strings `"Tool disabled: {reason}"` / `"Validation error: {e}"`,
  matching the format `dispatch_tool()` already uses internally.
- This server is audit-logged to `/opt/llm/logs/delete_audit.log` per its module
  docstring; this change does not touch that audit logging path (unaffected), it only
  gates whether `_dispatch_delete_tool()` is reached at all.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format scripts/mcp_servers/file/delete_server.py` | clean |
| Lint | `uv run ruff check scripts/mcp_servers/file/delete_server.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/file/delete_server.py` | no new errors |
| Tests | new cases in `tests/test_call_tool_validation.py` covering `allowed_dirs=[]` (disabled) and a validate_args-triggering call | pass |

Full cross-file validation is covered by the cross-cutting doc
`full_validation_pass_call_tool_disabled_gate.md` (not the sibling requirement 15's
`full_validation_pass_tools_enabled_disabled_reason.md`, which covers a different
feature).
