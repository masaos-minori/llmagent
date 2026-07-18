# Implementation: scripts/mcp_servers/file/read_server.py — disabled-tool gate + validate_args() on /v1/call_tool

Source plan: `plans/20260717-174848_plan.md` ("Reject disabled tools before dispatch in
/v1/call_tool and clarify validation policy")

Note on filename disambiguation: an existing doc `20260718-090617_read_server.py.md`
matches `read_server.py` by substring, but its Goal is "Make `GET /v1/tools` on the
file-read server ... merge `enabled`/`disabled_reason` into every returned tool dict" —
that covers the `list_tools()` handler only, for the sibling requirement 15
(`plans/20260717-174024_plan.md`). Its own Scope section explicitly lists "any other
endpoint in this file" as out of scope, which includes `call_tool()`. So it does NOT
cover this plan's feature. This doc uses the disambiguated slug `read_server_call_tool.py`
so future filename searches do not conflate the two.

## Goal

Make `POST /v1/call_tool` on the file-read server (port 8005) reject disabled tools
before dispatch — returning `CallToolResponse(result="Tool disabled: <reason>",
is_error=True)` when `_cfg.allowed_dirs` is empty — and call `req.validate_args()`
before dispatch, converting any raised `ValueError` into
`CallToolResponse(result=f"Validation error: {e}", is_error=True)`.

## Scope

**In scope**: the `call_tool()` handler (currently lines 241-244) in
`scripts/mcp_servers/file/read_server.py` only.

**Out of scope**: `list_tools()` (covered by sibling doc `20260718-090617_read_server.py.md`
for requirement 15 — unaffected by this plan), `_dispatch_read_tool()` (no change),
`read_models.py` (no schema change), `read_tools.py` (`TOOL_LIST` stays static).

**Depends on**: `availability_flags(allowed_dirs: list[str]) -> tuple[bool, str]` must
exist in `scripts/mcp_servers/file/common.py`. Per this plan's own Design ("SHARED WITH"
note), this helper is shared with requirement 15's plan; doc
`20260718-090551_common.py.md` already specifies adding it there with the exact same
signature and semantics this plan needs — apply that change first (or confirm it has
already landed via `grep -n "def availability_flags" scripts/mcp_servers/file/common.py`
before writing this file's change).

## Assumptions

- Current handler (verified exact content, lines 241-244):
  ```
  @app.post("/v1/call_tool", response_model=CallToolResponse)
  async def call_tool(req: CallToolRequest) -> CallToolResponse:
      r = await _dispatch_read_tool(req.name, req.args)
      return _to_call_tool_response(r)
  ```
- `CallToolRequest` / `CallToolResponse` are already imported (line 61:
  `from mcp_servers.models import CallToolRequest, CallToolResponse`) — no new import
  needed for those two names.
- `_cfg = FileReadConfig.load()` already exists at module level (line 66);
  `FileReadConfig.allowed_dirs: list[str]` (confirmed `read_models.py:28`).
- `req.validate_args()` (`scripts/mcp_servers/models.py:30-37`) already exists and calls
  `validate_tool_args(self.name, self.args)`; it raises `ValueError` on invalid args and
  is a no-op when no validator is registered for the tool
  (`scripts/mcp_servers/tool_validators.py: validate_tool_args`). No changes needed to
  `models.py` or `tool_validators.py`.
- All tools in this server share one enabled/disabled state (file servers have no
  per-tool distinction, matching the plan's Design note and the existing
  `list_tools()`-side `availability_flags()` usage) — so the check is
  `availability_flags(_cfg.allowed_dirs)`, not per-tool-name.

## Implementation

### Target file

`/home/sugimoto/llmagent/scripts/mcp_servers/file/read_server.py`

### Procedure

1. Add `availability_flags` to the existing
   `from mcp_servers.file.common import (...)` block (lines 32-39) — reuse the same
   import name/module that `list_tools()` will use (or already uses, if requirement 15
   landed first); do not re-derive the check.
2. Rewrite the `call_tool()` handler body (lines 242-244):
   - Compute `enabled, reason = availability_flags(_cfg.allowed_dirs)` first.
   - If not enabled, return `CallToolResponse(result=f"Tool disabled: {reason}",
     is_error=True)` immediately — before touching `req.validate_args()` or
     `_dispatch_read_tool()`.
   - Otherwise, call `req.validate_args()` inside `try/except ValueError as e`; on
     exception return `CallToolResponse(result=f"Validation error: {e}", is_error=True)`.
   - Otherwise, proceed with the existing `_dispatch_read_tool(req.name, req.args)` call
     and `_to_call_tool_response(r)` return, unchanged.
3. No change to the `@app.post(...)` decorator or the function signature
   `async def call_tool(req: CallToolRequest) -> CallToolResponse`.

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
    r = await _dispatch_read_tool(req.name, req.args)
    return _to_call_tool_response(r)
```

### Details

- Ordering is load-bearing: disabled-tool check first, then `validate_args()`, then
  dispatch — matches the plan's Design/"Ordering of checks" section (avoids validating
  arguments for a tool that is disabled anyway).
- `"Tool disabled: {reason}"` and `"Validation error: {e}"` are the exact literal
  formats specified by the plan (the latter matches `dispatch_tool()`'s existing
  internal format at `scripts/mcp_servers/dispatch.py:68-71`, so callers see one
  consistent error shape regardless of which stage rejects the call).
- No new exception types are introduced; `ValueError` is the only exception
  `validate_args()` raises (per `tool_validators.py`).
- `_cfg.allowed_dirs` is read fresh on every request (module-level global, not cached),
  consistent with how `list_tools()` reads it.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format scripts/mcp_servers/file/read_server.py` | clean |
| Lint | `uv run ruff check scripts/mcp_servers/file/read_server.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/file/read_server.py` | no new errors |
| Tests | new cases in `tests/test_call_tool_validation.py` (see that doc) covering `allowed_dirs=[]` (disabled) and a validate_args-triggering call | pass |

Full cross-file validation (mypy repo-wide, lint-imports, ast-grep, bandit, full pytest,
diff-cover, pre-commit, residual grep) is covered by the cross-cutting doc
`full_validation_pass_call_tool_disabled_gate.md` (this plan's own validation doc — do
NOT reuse `full_validation_pass_tools_enabled_disabled_reason.md`, which is scoped to the
unrelated sibling requirement 15 `/v1/tools` feature).
