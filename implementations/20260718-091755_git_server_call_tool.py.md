# Implementation: scripts/mcp_servers/git/server.py — disabled-tool gate + validate_args() on /v1/call_tool

Source plan: `plans/20260717-174848_plan.md` ("Reject disabled tools before dispatch in
/v1/call_tool and clarify validation policy")

Note on filename disambiguation: an existing doc `20260718-090710_git_server.py.md`
matches `git_server.py` by substring, but its Goal is scoped to `GET /v1/tools`
merging `enabled`/`disabled_reason` (requirement 15, `plans/20260717-174024_plan.md`).
Its own Scope explicitly lists "any other endpoint in this file (e.g. `call_tool`,
`health`)" as **out of scope**, and its precedence logic is inlined directly inside
`list_tools()`'s loop body — no reusable `_git_tool_availability()` function is defined
there. So it does NOT cover this plan's `call_tool()` feature; a new function is needed.
This doc uses the disambiguated slug `git_server_call_tool.py`.

## Goal

Make `POST /v1/call_tool` on the git server (port 8014) reject disabled tools before
dispatch — returning `CallToolResponse(result="Tool disabled: <reason>", is_error=True)`
per the same two-tier precedence rule already specified for `/v1/tools`
(`allowed_repo_paths` empty disables everything; otherwise `read_only=true` disables only
the 5 `GIT_WRITE_TOOLS`) — and call `req.validate_args()` before dispatch, converting any
raised `ValueError` into `CallToolResponse(result=f"Validation error: {e}", is_error=True)`.
Preserve the existing request-timing/audit-logging behavior around the dispatch call.

## Scope

**In scope**: the `call_tool()` handler (currently lines 79-98) in
`scripts/mcp_servers/git/server.py`, plus a new private helper
`_git_tool_availability(cfg: GitConfig, tool_name: str) -> tuple[bool, str]` in the same
file.

**Out of scope**: `list_tools()` (covered by sibling doc
`20260718-090710_git_server.py.md` for requirement 15 — unaffected here; that doc inlines
an equivalent precedence check directly in `list_tools()`'s loop rather than calling this
new helper, since it was written before this plan's helper existed — a future cleanup
could have `list_tools()` call `_git_tool_availability()` per tool instead of duplicating
the precedence branches, but that refactor is not part of either plan's scope),
`_dispatch_git_tool()` (no change), `git/models.py` (no schema change), `git/tools.py`
(`TOOL_LIST` stays static), `health()` (no change).

**Depends on**: `GIT_WRITE_TOOLS` (`scripts/shared/tool_constants.py:98-106`, a
`frozenset[str]` of `{"git_add", "git_commit", "git_checkout", "git_pull", "git_push"}`)
— already present, no change needed. `mcp_servers -> shared` is an allowed import edge
per `.importlinter`.

## Assumptions

- Current handler (verified exact content, lines 79-98):
  ```
  @app.post("/v1/call_tool", response_model=CallToolResponse)
  async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
      t0 = time.perf_counter()
      session_id = request.headers.get("x-session-id", "")
      request_id = getattr(
          request.state, "request_id", request.headers.get("x-request-id", "")
      )
      r = await _dispatch_git_tool(req.name, req.args)
      ms = (time.perf_counter() - t0) * 1000
      logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
      _audit_log(
          logger,
          session_id=session_id,
          request_id=request_id,
          action=req.name,
          target=req.args.get("repo", ""),
          outcome=r.outcome,
          server_key="git",
      )
      return _to_call_tool_response(r)
  ```
- Current top-level imports (lines 20-37) already include
  `from mcp_servers.git.models import GitConfig, GitServiceError` (line 32) and
  `from mcp_servers.models import CallToolRequest, CallToolResponse` (line 36); no new
  import of these two names is needed. A new import line
  `from shared.tool_constants import GIT_WRITE_TOOLS` must be added (alphabetically
  ordered per `ruff check --fix`, after the `mcp_servers.*` imports since `shared` sorts
  after `mcp_servers`).
- `_cfg = GitConfig.load()` already exists at module level (line 41); `GitConfig.
  allowed_repo_paths: list[str]` and `GitConfig.read_only: bool` (confirmed
  `git/models.py:27-28`).
- `req.validate_args()` (`scripts/mcp_servers/models.py:30-37`) already exists, raises
  `ValueError` on invalid args (e.g. blank `git_commit` message — already exercised by
  `tests/test_mcp_tool_validators.py`), no-op when no validator registered. No changes
  needed to `models.py` or `tool_validators.py`.
- The `t0`/timing/`_audit_log(...)` block must be preserved exactly as-is for the
  non-disabled, non-validation-error path — this plan does not change observability
  behavior for successful or dispatch-level-failed calls, only adds an early return for
  the disabled case and a validation-error branch before the existing timing starts (or,
  alternatively, before the dispatch call but inside the timing window — see Details for
  the chosen placement).

## Implementation

### Target file

`/home/sugimoto/llmagent/scripts/mcp_servers/git/server.py`

### Procedure

1. Add `from shared.tool_constants import GIT_WRITE_TOOLS` to the import block (near
   lines 30-37; final ordering verified by `ruff check --fix`, not hand-placed).
2. Add a new private function `_git_tool_availability(cfg: GitConfig, tool_name: str) ->
   tuple[bool, str]` near `_dispatch_git_tool()` (around line 63), implementing the same
   precedence rule as requirement 15's `list_tools()` logic:
   - `not cfg.allowed_repo_paths` → `(False, "allowed_repo_paths is empty")` (checked
     first, unconditionally).
   - `cfg.read_only and tool_name in GIT_WRITE_TOOLS` → `(False, "read_only=true")`.
   - else → `(True, "")`.
3. Update `call_tool()` (lines 79-98):
   - Immediately after the function signature (before `t0 = time.perf_counter()`),
     compute `enabled, reason = _git_tool_availability(_cfg, req.name)`.
   - If not enabled, return `CallToolResponse(result=f"Tool disabled: {reason}",
     is_error=True)` immediately — skip timing/audit-logging for disabled calls (they
     never reach the dispatch table, so there is nothing meaningful to time/audit as a
     dispatch outcome; this matches the plan's Scope: "Do not call the service dispatch
     table for disabled tools").
   - If enabled, call `req.validate_args()` in `try/except ValueError as e` before
     `t0 = time.perf_counter()`; on exception return
     `CallToolResponse(result=f"Validation error: {e}", is_error=True)` immediately
     (also skipping timing/audit — no dispatch occurred).
   - Otherwise, proceed with the existing `t0`/dispatch/timing/audit-log block, unchanged.

### Method

Pseudocode (no production code blocks per design-doc convention):

```
def _git_tool_availability(cfg: GitConfig, tool_name: str) -> tuple[bool, str]:
    docstring: "Return (enabled, disabled_reason) for a single git tool by name."
    if not cfg.allowed_repo_paths:
        return False, "allowed_repo_paths is empty"
    if cfg.read_only and tool_name in GIT_WRITE_TOOLS:
        return False, "read_only=true"
    return True, ""


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    enabled, reason = _git_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    try:
        req.validate_args()
    except ValueError as e:
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    t0 = time.perf_counter()
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    r = await _dispatch_git_tool(req.name, req.args)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=req.args.get("repo", ""),
        outcome=r.outcome,
        server_key="git",
    )
    return _to_call_tool_response(r)
```

### Details

- Precedence order is load-bearing, identical risk to requirement 15's sibling logic:
  `allowed_repo_paths` empty MUST be checked before `read_only`, so that when both
  `allowed_repo_paths=[]` and `read_only=False` hold, the tool is still disabled with
  `"allowed_repo_paths is empty"`. New tests (see `test_call_tool_validation.py` doc)
  must pin this order.
- `_git_tool_availability()` is a per-tool-name check (unlike the file servers' uniform
  `availability_flags()`), because git tools differ between read and write per
  `GIT_WRITE_TOOLS` membership.
- Timing (`t0`)/audit-logging only wraps the actual dispatch attempt, consistent with
  existing behavior for genuine dispatch outcomes; disabled/validation-rejected calls
  never reach `_dispatch_git_tool()` so recording a dispatch timing/audit entry for them
  would misrepresent what happened. This is a deliberate design choice for this doc —
  flag for reviewer if audit trail for rejected calls is later desired (not requested by
  the plan).
- Exact literal strings `"Tool disabled: {reason}"` / `"Validation error: {e}"`, matching
  `dispatch_tool()`'s existing internal format.
- No change to `_dispatch_git_tool()`, `list_tools()`, `health()`, or the
  `GitMCPServer.dispatch()` method (line 129-130) — those are unaffected.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format scripts/mcp_servers/git/server.py` | clean |
| Lint | `uv run ruff check scripts/mcp_servers/git/server.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/git/server.py` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (`mcp_servers -> shared` for `GIT_WRITE_TOOLS` is an allowed edge) |
| Tests | new cases in `tests/test_call_tool_validation.py` covering `allowed_repo_paths=[]` (all disabled regardless of `read_only`), `read_only=True` with non-empty `allowed_repo_paths` (only the 5 write tools disabled), and a validate_args-triggering call (e.g. blank `git_commit` message) | pass |

Full cross-file validation is covered by the cross-cutting doc
`full_validation_pass_call_tool_disabled_gate.md` (not the sibling requirement 15's
`full_validation_pass_tools_enabled_disabled_reason.md`, which covers a different
feature).
