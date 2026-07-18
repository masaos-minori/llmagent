# Implementation: scripts/mcp_servers/file/write_server.py — disabled-tool gate + validate_args() on /v1/call_tool

Source plan: `plans/20260717-174848_plan.md` ("Reject disabled tools before dispatch in
/v1/call_tool and clarify validation policy")

Note on filename disambiguation: an existing doc `20260718-090638_write_server.py.md`
matches `write_server.py` by substring, but its Goal is scoped to `GET /v1/tools`
merging `enabled`/`disabled_reason` (requirement 15, `plans/20260717-174024_plan.md`),
explicitly excluding "any other endpoint in this file". Does not cover this plan's
`call_tool()` feature. This doc uses the disambiguated slug `write_server_call_tool.py`.

## Goal

Make `POST /v1/call_tool` on the file-write server (port 8007) reject disabled tools
before dispatch — returning `CallToolResponse(result="Tool disabled: <reason>",
is_error=True)` when `_cfg.allowed_dirs` is empty — and call `req.validate_args()`
before dispatch, converting any raised `ValueError` into
`CallToolResponse(result=f"Validation error: {e}", is_error=True)`.

## Scope

**In scope**: the `call_tool()` handler (currently lines 151-154) in
`scripts/mcp_servers/file/write_server.py` only.

**Out of scope**: `list_tools()` (covered by sibling doc
`20260718-090638_write_server.py.md` for requirement 15 — unaffected here),
`_dispatch_write_tool()` (no change), `write_models.py` (no schema change),
`write_tools.py` (`TOOL_LIST` stays static).

**Depends on**: `availability_flags(allowed_dirs: list[str]) -> tuple[bool, str]` in
`scripts/mcp_servers/file/common.py` (see `20260718-090551_common.py.md`) — apply that
change first, or confirm via
`grep -n "def availability_flags" scripts/mcp_servers/file/common.py` that it already
landed.

## Assumptions

- Current handler (verified exact content, lines 151-154):
  ```
  @app.post("/v1/call_tool", response_model=CallToolResponse)
  async def call_tool(req: CallToolRequest) -> CallToolResponse:
      r = await _dispatch_write_tool(req.name, req.args)
      return _to_call_tool_response(r)
  ```
- `CallToolRequest` / `CallToolResponse` already imported (line 48:
  `from mcp_servers.models import CallToolRequest, CallToolResponse`).
- `_cfg = FileWriteConfig.load()` already exists at module level (line 53);
  `FileWriteConfig.allowed_dirs: list[str]` (confirmed `write_models.py:28`).
- `req.validate_args()` (`scripts/mcp_servers/models.py:30-37`) already exists, raises
  `ValueError` on invalid args, no-op when no validator registered. No changes needed to
  `models.py` or `tool_validators.py`.
- All tools in this server share one enabled/disabled state (uniform
  `availability_flags(_cfg.allowed_dirs)` check, no per-tool-name branch), same as
  `read_server.py`/`delete_server.py`.

## Implementation

### Target file

`/home/sugimoto/llmagent/scripts/mcp_servers/file/write_server.py`

### Procedure

1. Add `availability_flags` to the existing
   `from mcp_servers.file.common import (...)` block (lines 26-33).
2. Rewrite the `call_tool()` handler body (lines 152-154):
   - Compute `enabled, reason = availability_flags(_cfg.allowed_dirs)` first.
   - If not enabled, return `CallToolResponse(result=f"Tool disabled: {reason}",
     is_error=True)` immediately.
   - Otherwise, call `req.validate_args()` in `try/except ValueError as e`; on exception
     return `CallToolResponse(result=f"Validation error: {e}", is_error=True)`.
   - Otherwise, proceed with the existing `_dispatch_write_tool(req.name, req.args)` call
     and `_to_call_tool_response(r)` return, unchanged.
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
    r = await _dispatch_write_tool(req.name, req.args)
    return _to_call_tool_response(r)
```

### Details

- Ordering: disabled-tool check, then `validate_args()`, then dispatch — matches the
  plan's Design section.
- Exact literal strings `"Tool disabled: {reason}"` / `"Validation error: {e}"`,
  matching the format `dispatch_tool()` already uses internally.
- `write_server.py` has `edit_file`/`move_file`/`create_directory` tools with existing
  registered validators in `tool_validators.py` — this change makes `validate_args()`
  actually run for them via `/v1/call_tool`; no change to the validators themselves.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format scripts/mcp_servers/file/write_server.py` | clean |
| Lint | `uv run ruff check scripts/mcp_servers/file/write_server.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/file/write_server.py` | no new errors |
| Tests | new cases in `tests/test_call_tool_validation.py` covering `allowed_dirs=[]` (disabled) and a validate_args-triggering call | pass |

Full cross-file validation is covered by the cross-cutting doc
`full_validation_pass_call_tool_disabled_gate.md` (not the sibling requirement 15's
`full_validation_pass_tools_enabled_disabled_reason.md`, which covers a different
feature).
