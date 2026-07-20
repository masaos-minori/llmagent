# Implementation procedure: web_search_server.py call_tool()/health refactor

Source plan: `plans/20260719-193902_plan.md` (Implementation steps 4-5,
Design §3-§4). Note: per the plan's 2026-07-20 revision note, "server.py" in
the original requirement text refers to this file,
`scripts/mcp_servers/web_search/web_search_server.py` — the bare
`scripts/mcp_servers/web_search/server.py` was deleted by commit `abcf0820`
and no longer exists. No import-path fix is needed; this doc covers only the
`call_tool()` try/except/finally refactor and `/health` wiring, which are
still live work.

## Goal

Refactor `web_search_server.py::call_tool()` so an audit record is
unconditionally emitted for every outcome (success, zero-result, validation
error, unknown tool, timeout, provider/network/parse error, unexpected
error), and record each call's outcome into the new `health.py`/`metrics.py`
modules, without changing the existing HTTP/MCP error behavior (502 on
`WebSearchUpstreamError`, existing status codes for validation/unknown-tool
errors). Also wire `/health` to surface `health.health_details()` and flip to
degraded (503) via `is_degraded()`.

## Scope

**In scope:**
- `call_tool()` (currently lines 88-105 of
  `scripts/mcp_servers/web_search/web_search_server.py`): wrap the dispatch
  call in try/except/finally; classify outcome/error_type; call
  `metrics.record_query(...)` and `health.record_success()` /
  `health.record_failure(...)`; extend the `_audit_log(...)` call site with
  `error_type` and the additional fields listed in Design §4 (requested
  `max_results`, result count, latency ms, query preview, optional query
  hash).
- `health()` endpoint (currently lines 57-63): fold
  `health.health_details()` into `details["provider"]` and add to `deps` when
  `health.is_degraded()` is true, so `make_health_response` returns 503.
- New imports: `mcp_servers.web_search.health as health`,
  `mcp_servers.web_search.metrics as metrics`, `time`, `hashlib`.

**Out of scope:**
- Any change to `formatters.py`/`search_provider.py` (plan's recommended
  default: measure latency directly in `call_tool()` around
  `_dispatch_web_tool`, not by plumbing new fields through `DispatchResult`;
  re-verify during implementation whether this holds).
- Any change to `mcp_servers/dispatch.py` or `mcp_servers/models.py` (shared
  base modules, not in this plan's target-file list).
- Adding a distinct `WebSearchTimeoutError` subclass to `web_search_models.py`
  (flagged in the plan's UNK-1 as a possible follow-up, not required now).

## Assumptions

1. `web_search_server.py` (the sole remaining server file after commit
   `abcf0820`) already imports `WebSearchConfig`/`WebSearchUpstreamError`
   from `web_search_models` (confirmed: `web_search_server.py:27-30`) and
   `TOOL_LIST` from `web_search_tools` (confirmed: `web_search_server.py:31`)
   — no import fix needed, matching the plan's revision note.
2. Current `call_tool()` body (confirmed by reading the file, lines 88-105):
   ```
   async def call_tool(req, request):
       session_id = request.headers.get("x-session-id", "")
       request_id = getattr(request.state, "request_id", request.headers.get("x-request-id", ""))
       r = await _dispatch_web_tool(req.name, req.args)
       _audit_log(logger, session_id=..., request_id=..., action=req.name,
                  target=req.args.get("query", ""), outcome=r.outcome, server_key="web_search")
       return _to_call_tool_response(r)
   ```
   `_audit_log` is only reached on the happy path today — if
   `_dispatch_web_tool` raises (e.g. `WebSearchUpstreamError` from
   `search_provider.py` via `formatters.py::search_web`), the audit call is
   skipped entirely and the exception propagates straight to
   `_handle_web_search_error` (the `@app.exception_handler(WebSearchUpstreamError)`
   at line 43-51, which returns 502). This is exactly the gap the plan's
   Design §3 closes.
3. `_audit_log` (`scripts/mcp_servers/audit.py:16-42`) already accepts
   `error_type: str = ""` and `detail: str = ""` as keyword parameters with
   defaults — confirmed by reading `audit.py`. No signature change is
   required to pass `error_type`; only the call site in `call_tool()` needs
   to supply it. `detail` is available as a free-text field for the extra
   Design §4 fields (max_results, result count, latency, query preview,
   query hash) if packed as a compact string.
4. `DispatchResult` (`scripts/mcp_servers/dispatch.py:23-33`) has an
   `outcome` property (`"error"` if `is_error` else `"ok"`) but no
   `error_type`/latency/result-count fields — these are not surfaced by
   `dispatch_tool()` today, so `call_tool()` must derive/measure them itself
   (latency via its own `time.perf_counter()`, error_type via inspecting
   `r.output`/exception, result count is not directly available from
   `DispatchResult.output` since it's already formatted text — plan accepts
   this as an acceptable simplification, see Design §5 discussion; result
   count may be omitted from the audit detail if not cheaply available
   without touching `formatters.py`).
5. `search_provider.py::search_duckduckgo` wraps both `RuntimeError` and
   `TimeoutError` into a single `WebSearchUpstreamError(f"DuckDuckGo search
   failed: {e}")` (confirmed: `search_provider.py:30-33`) — there is no
   discriminating attribute, so timeout classification (UNK-1) is a
   best-effort substring match on `str(exc)` for `"timeout"` (case-
   insensitive), which will find the substring when the wrapped
   `TimeoutError`'s message or the word "Timeout" from a library exception
   appears in the formatted message. This is fragile by design (see plan's
   Risks table) and must be pinned by a characterization test.
6. `make_health_response(deps, details)` (`scripts/mcp_servers/health_response.py:24-49`)
   returns 200 when `deps` is empty, 503 when non-empty — confirmed by
   reading the function body. Wiring degraded health means adding an entry
   to `deps` (e.g. `deps["web_search_provider"] = "degraded: N consecutive
   failures"`) only when `health.is_degraded()` is true.

## Implementation

### Target file

`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure

1. Add imports: `import hashlib`, `import time`, `from
   mcp_servers.web_search import health, metrics` (or `import
   mcp_servers.web_search.health as health` /
   `... .metrics as metrics`, matching existing style preference — check
   `ruff`'s import-order rules apply either way).
2. Add a small module-level helper `_classify_dispatch_error(output: str) ->
   str` for in-`try`-block (non-raised) errors surfaced via
   `DispatchResult(is_error=True, output=...)` — e.g. distinguishing
   `"Validation error: ..."` (from `dispatch_tool`'s `ValueError` branch,
   `dispatch.py:60-62`) vs `"Unknown tool: ..."` (from `dispatch.py:53-55`)
   vs `"Tool name must be a non-empty string"` (`dispatch.py:47-49`) by
   prefix/substring match on `output`.
3. Add a small module-level helper `_classify_upstream_error(exc:
   WebSearchUpstreamError) -> str` implementing the UNK-1 default: return
   `"timeout"` if `"timeout"` appears in `str(exc).lower()`, else
   `"provider_error"`.
4. Rewrite `call_tool()` per Design §3's pseudocode:
   ```
   t0 = time.perf_counter()
   error_type = ""
   outcome = "ok"
   try:
       r = await _dispatch_web_tool(req.name, req.args)
       outcome = r.outcome
       latency_ms = (time.perf_counter() - t0) * 1000
       if outcome == "error":
           error_type = _classify_dispatch_error(r.output)
           metrics.record_query(success=False, latency_ms=latency_ms, error_type=error_type)
       else:
           metrics.record_query(success=True, latency_ms=latency_ms)
           health.record_success()
       return _to_call_tool_response(r)
   except WebSearchUpstreamError as e:
       outcome = "error"
       error_type = _classify_upstream_error(e)
       latency_ms = (time.perf_counter() - t0) * 1000
       metrics.record_query(success=False, latency_ms=latency_ms, error_type=error_type)
       health.record_failure(error_type)
       raise
   except Exception:
       outcome = "error"
       error_type = "unexpected_error"
       latency_ms = (time.perf_counter() - t0) * 1000
       metrics.record_query(success=False, latency_ms=latency_ms, error_type=error_type)
       raise
   finally:
       query = req.args.get("query", "")
       detail = (
           f"max_results={req.args.get('max_results', '')} "
           f"latency_ms={latency_ms:.0f} "
           f"query_preview={query[:80]!r} "
           f"query_hash={hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]}"
       )
       _audit_log(
           logger, session_id=session_id, request_id=request_id, action=req.name,
           target=query, outcome=outcome, error_type=error_type,
           server_key="web_search", detail=detail,
       )
   ```
   Note: `latency_ms` must be defined before the `finally` block runs on
   every path (including the `except Exception` catch-all) — either
   initialize `latency_ms = 0.0` at the top alongside `error_type`/`outcome`,
   or compute it identically in each branch as shown above. Confirm during
   implementation which is cleaner and keeps `radon cc` grade low (plan's
   Validation plan requires `call_tool` stay below grade C; extract
   `_classify_*` helpers as shown specifically to keep this function small).
5. `health.record_success()` is only called on a true dispatch success
   (`outcome == "ok"`), not on dispatch-layer errors that don't raise — this
   matches Design §3, since a validation/unknown-tool error is a client
   mistake, not a provider health signal.
6. Update `health()` (the `/health` endpoint):
   ```
   @app.get("/health")
   async def health_endpoint() -> JSONResponse:
       deps: dict[str, str] = {}
       details: dict[str, object] = {"service": "web-search-mcp"}
       details["provider"] = health.health_details()
       details["metrics"] = metrics.snapshot()
       if health.is_degraded():
           deps["web_search_provider"] = "degraded: repeated provider failures"
       return make_health_response(deps, details)
   ```
   Rename the local function if it shadows the `health` module import (the
   existing function is named `health()` at line 58, which collides with the
   new `import ... as health` module alias) — rename the endpoint function
   to `health_endpoint()` or similar, keeping the route path `@app.get("/health")`
   unchanged (FastAPI routes by decorator argument, not function name, so
   this is a safe rename with no external behavior change).

### Method

- Keep the `try/except WebSearchUpstreamError/except
  Exception/finally` structure exactly as in Design §3 so the existing
  `@app.exception_handler(WebSearchUpstreamError)` (line 43-51, unchanged)
  still fires after `raise` re-propagates the exception — FastAPI's
  exception-handler mechanism operates above the route function, so
  re-raising from inside `call_tool()` preserves the existing 502 behavior.
- Do not catch and swallow any exception — every `except` branch ends in
  `raise` (or falls through in the non-raising `try` branch), preserving
  "no behavior change" from the plan's acceptance criteria.
- Use the existing `logger = logging.getLogger(__name__)` (line 33) as the
  first positional arg to `_audit_log`, matching current usage.

### Details

- The rename of the `/health` function from `health` to `health_endpoint` is
  necessary once `mcp_servers.web_search.health` is imported as `health` —
  confirm no other code references `web_search_server.health` (the function)
  by name; `grep -rn "web_search_server.health\b" scripts/ tests/` before
  applying, to catch any external caller depending on the old function
  identity (unlikely, since FastAPI dispatches by route, but check).
- `req.args.get("query", "")` is already the pattern used today (line 101)
  for the audit `target` field — reuse it for both `target` and the new
  `detail` string's query preview/hash, not a second independent lookup.
- Per `rules/coding.md`, comments/log content must stay English-only; the
  `detail` string built above is plain ASCII/English already.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Format/lint | `uv run ruff format scripts/ && uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` (cross-check `uv run pyright scripts/`) | no new errors |
| Import boundary | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| No bare except | `ast-grep --pattern 'except: $$$' --lang python scripts/mcp_servers/web_search/web_search_server.py` | no matches |
| Complexity | `uv run radon cc scripts/mcp_servers/web_search/web_search_server.py -s -n C` | `call_tool` stays below grade C; extract more helpers if it regresses |
| Characterization test (before refactor) | `uv run pytest tests/test_web_search_server.py -v` | pins current 502-on-upstream-error and other status codes, run once before and once after the refactor per `rules/toolchain.md` |
| Targeted tests | `uv run pytest tests/test_web_search_audit.py tests/test_web_search_health.py tests/test_web_search_metrics.py tests/test_web_search_server.py -v` | all pass |
| Full suite | `uv run pytest -v` | no new failures |
| Security | `uv run bandit -r scripts/ -c pyproject.toml` | no new HIGH/MEDIUM |
| MCP doc consistency | `uv run check-mcp-docs` | passes |
