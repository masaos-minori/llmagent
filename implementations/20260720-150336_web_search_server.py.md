# Implementation procedure: `scripts/mcp_servers/web_search/web_search_server.py` (merge browser routes)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 7; resolves UNK-02 (auth
middleware wiring for `browser_auth_token`).

The two prior docs for this filename,
`implementations/done/20260720-081208_test_web_search_server.py.md` and
`implementations/done/20260720-081553_web_search_server.py.md`, belong to today's earlier
requirement batch (audit-log `detail` field / `_classify_dispatch_error` wiring for `search_web`
only) — read in full, no mention of `browser`, `attach_auth_middleware`, or `BrowserAuthorizationError`.
No overlap. New document.

## Goal

Merge `scripts/mcp_servers/browser/browser_server.py`'s (150 lines, read in full) exception
handlers and auth-middleware wiring into `web_search_server.py`, so one FastAPI app on port 8004
serves both `search_web` and `browser_fetch` with each tool's original error-handling/security
behavior preserved.

## Scope

**In scope**: `scripts/mcp_servers/web_search/web_search_server.py` (current: 203 lines) — new
exception handlers, `attach_auth_middleware` call, `/health` endpoint extension, `_audit_log` target
extraction for `url` vs `query`, `server_version` bump.
**Out of scope**: `_classify_dispatch_error`/`_classify_upstream_error` — untouched (search-specific,
already correct). `browser_server.py`'s own `BrowserMCPServer` class / `http_port = 8016` /
`__main__` block — retired entirely (browser directory deletion, separate doc), not merged.

## Assumptions

1. `attach_auth_middleware(app, token)` (from `mcp_servers.server`, already imported by
   `browser_server.py` at line 42) is currently **not** imported or called anywhere in
   `web_search_server.py` — per UNK-02's resolution, add the call for `browser_auth_token` only;
   `search_web`'s own `auth_token` field in `agent.toml` stays as today's no-auth-middleware status
   quo (plan: "leaving search_web's current no-auth-middleware status as-is unless product intent
   says otherwise" — this doc does not add middleware for `search_web`'s token).
2. `web_search_server.py`'s `app = FastAPI(...)` (line 46) has no `attach_auth_middleware` call
   today — adding one changes request-handling behavior only when `browser_auth_token` is
   non-empty (currently `""` in both configs per plan Assumption 6), so this is a no-op today and a
   forward-looking regression guard, exactly as UNK-02 states.
3. `browser_server.py`'s `/v1/call_tool`'s audit-log `target` extraction (line 121:
   `req.args.get("url", "")[:80]`) differs from `web_search_server.py`'s current
   `query = str(req.args.get("query", ""))` (line 163) — the merged endpoint must extract whichever
   key is present (`url` for `browser_fetch`, `query` for `search_web`), since both tools now share
   one `call_tool` handler.
4. `browser_server.py`'s `/v1/tools` endpoint (lines 97-102) manually tags `server_key="browser"`
   on each tool dict — this whole endpoint is retired; `web_search_server.py`'s existing
   `build_tools_response(TOOL_LIST, "web_search")` (line 120, from `mcp_servers.server`) already
   tags every entry in `TOOL_LIST` with `server_key="web_search"` generically, and `TOOL_LIST` now
   contains `browser_fetch` too (per the `web_search_tools.py` doc) — no server.py-side change
   needed beyond the `TOOL_LIST` data addition already covered by that doc.
5. `browser_server.py` has its own separate `/health` endpoint (lines 89-94, static
   `{"service": "browser-mcp"}`, no degradation probing) — this is retired; the merged `/health`
   (already present in `web_search_server.py`) is extended to report both tools' health/metrics
   (per the `health.py`/`metrics.py` docs' `browser_health_details()`/`browser_snapshot()`).

## Implementation

### Target file

`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure

1. Extend imports:
   - `from mcp_servers.server import MCPServer, attach_auth_middleware, build_tools_response`
     (add `attach_auth_middleware` to the existing import line 24-27).
   - `from mcp_servers.web_search.web_search_models import (..., BrowserAuthorizationError,
     BrowserValidationError, WebSearchConfig, ...)` (extend the existing import block, lines 30-36).
2. After `_cfg: WebSearchConfig = WebSearchConfig.load()` (line 44) and `app = FastAPI(...)` (line
   46), add: `attach_auth_middleware(app, _cfg.browser_auth_token or "")`. Place this immediately
   after `app` is constructed, before any `@app.exception_handler`/`@app.get`/`@app.post`
   decorators, mirroring `browser_server.py`'s own ordering (source line 55, right after `app =
   FastAPI(...)`).
3. Add two new exception handlers, directly after the existing
   `_handle_web_search_error` (`WebSearchUpstreamError` → 502, lines 49-57):
   ```
   @app.exception_handler(BrowserAuthorizationError)
   async def _on_browser_auth_error(_req: Any, exc: BrowserAuthorizationError) -> JSONResponse:
       return JSONResponse({"detail": str(exc)}, status_code=403)

   @app.exception_handler(BrowserValidationError)
   async def _on_browser_validation_error(_req: Any, exc: BrowserValidationError) -> JSONResponse:
       return JSONResponse({"detail": str(exc)}, status_code=422)
   ```
   (Ported verbatim from `browser_server.py` lines 58-71, adapting the `Request` type-hint style to
   match this file's existing `_req: Any` convention at line 51.)
4. Extend the `/health` endpoint (lines 63-73): add
   `details["browser_provider"] = health.browser_health_details()` and
   `details["browser_metrics"] = metrics.browser_snapshot()`; extend the degradation check to
   `if health.is_degraded(): deps["web_search_provider"] = "degraded: ..."` (existing) **and**
   `if health.is_browser_degraded(): deps["browser_fetch_provider"] = "degraded: repeated fetch
   failures"` (new, separate `deps` key so an operator can distinguish which tool is unhealthy —
   per the `health.py` doc's Details section).
5. In `call_tool()` (lines 127-181), update the audit-log `target`/`detail` construction in the
   `finally` block: extract `target = str(req.args.get("query") or req.args.get("url") or "")`
   (covers both tools; `query` takes precedence only because it's checked first, but the two keys
   are mutually exclusive per each tool's own schema, so order does not matter functionally). Adjust
   `detail`'s f-string to only include `max_results=...` when the tool is `search_web` — or,
   simpler, always build `detail` generically as `f"latency_ms={latency_ms:.0f}
   target_preview={target[:80]!r}"` without the search-specific `max_results`/`query_hash` fields,
   moving those into a `search_web`-specific branch if per-tool detail formatting is wanted. Prefer
   the simplest option that keeps `search_web`'s existing audit fields unchanged: branch on
   `req.name == "search_web"` to build the existing detailed string, else (i.e. `browser_fetch`)
   build a `url`-based equivalent (`url_preview={target[:80]!r}`, no query-hash since URLs are not
   the same privacy-sensitive free-text a search query is).
6. Bump `server_version`/`FastAPI(... version=...)` from `"3.0.0"` to `"4.0.0"` (line 46's
   `version="3.0.0"` and line 190's `server_version = "3.0.0"`) — signals the merged server's new
   scope. Update the `FastAPI(title=..., description=...)` if a description field is added
   (optional; not currently present on this app, unlike `browser_server.py`'s app which has one —
   adding a merged description mentioning both tools is a nice-to-have, not required).
7. `WebSearchMCPServer.mcp_tools = TOOL_LIST` (line 194) — no change needed; `TOOL_LIST` already
   includes `browser_fetch` once the `web_search_tools.py` doc lands.

### Method

Additive handler/middleware registration plus one conditional branch in the existing audit-log
`finally` block. `_dispatch_web_tool`/`dispatch_web_tool` (already generic over `_WEB_DISPATCH`'s
keys, per the `formatters.py` doc) requires no change here — the server-level dispatch function is
already tool-agnostic.

### Details

- Both `WebSearchUpstreamError` (502) and the two new browser handlers (403/422) coexist as
  separate `@app.exception_handler` registrations on the same `app` object — per plan Assumption 2 /
  Design section, they are NOT collapsed into one hierarchy.
- `health`/`metrics` module imports (line 28: `from mcp_servers.web_search import health,
  metrics`) need no import-line change — the new `browser_health_details`/`browser_snapshot`
  functions live in the same already-imported modules.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/mcp_servers/web_search/web_search_server.py && uv run ruff check scripts/mcp_servers/web_search/web_search_server.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/web_search/web_search_server.py` | no new errors |
| Unit tests | `uv run pytest tests/test_web_search_server.py -v` (add: 403 on non-allowlisted domain, 422 on bad scheme, `/health` includes `browser_provider`/`browser_metrics` keys, auth middleware rejects unauthenticated calls when `browser_auth_token` is set) | passes |
| Full suite | `uv run pytest -v` | no new failures |
| Manual/integration | `curl :8004/health` post-deploy | 200 OK; both `provider`/`metrics` (search) and `browser_provider`/`browser_metrics` keys present |
| Manual/integration | `curl :8004/v1/tools` post-deploy | lists both tools, `server_key="web_search"` |
