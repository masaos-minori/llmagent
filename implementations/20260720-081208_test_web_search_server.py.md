# Implementation Procedure: tests/test_web_search_server.py (new file)

Source plan: `plans/20260719-193357_plan.md` (Phase 2, Implementation steps item
"Write `tests/test_web_search_server.py`: `/v1/call_tool` returns a `502` (via
the existing `_handle_web_search_error` handler) for each new exception
subclass, confirming `@app.exception_handler(WebSearchUpstreamError)` actually
fires for each one.").

## Goal

Confirm at the HTTP boundary that `web_search_server.py`'s
`@app.exception_handler(WebSearchUpstreamError)` (registered once, on the base
class) correctly catches every new subclass (`WebSearchTimeoutError`,
`WebSearchNetworkError`, `WebSearchProviderError`, `WebSearchParseError`) raised
from deep inside the dispatch chain, and returns the existing generic
`502 Bad Gateway` JSON response (`{"error": str(exc)}`) for each — verifying
Starlette's inheritance-aware exception middleware works correctly against
this module's own class objects (relevant because the plan's Risk R1 /
Assumption 4 note that this only works reliably once there is a single,
non-orphaned module defining these classes, which is already the case per the
plan's revision note — `web_search_server.py` imports exclusively from
`web_search_models.py`, no duplicate `models.py` exists anymore).

## Scope

**In scope:**
- New test file `tests/test_web_search_server.py`.
- Uses `fastapi.testclient.TestClient(web_search_server.app)` (matching the
  existing pattern in `tests/test_call_tool_validation.py` for other MCP
  servers, e.g. `mcp_servers.file.read_server`).
- Posts to `/v1/call_tool` with `{"name": "search_web", "args": {"query": "..."}}`,
  with `dispatch_web_tool` (or the deeper `search_duckduckgo`) monkeypatched to
  raise each of the four new exception subclasses in turn.
- Asserts HTTP status `502` and `{"error": "<message>"}` JSON shape for each.

**Out of scope:**
- No test of `/health` or `/v1/tools` endpoints (unrelated to this plan's
  scope).
- No test of the actual DuckDuckGo call itself (fully mocked at the dispatch
  boundary).
- Per plan Unknown UNK-02's recorded non-blocking default: this test does NOT
  assert distinct HTTP status codes per exception subclass (e.g. 504 for
  timeout vs 502 for provider failure) — all four subclasses are expected to
  produce the same `502` response via the single generic handler, matching
  current/accepted behavior.

## Assumptions

1. `web_search_server.py` (verified by direct read) registers exactly one
   exception handler, `@app.exception_handler(WebSearchUpstreamError)` →
   `_handle_web_search_error`, returning `JSONResponse(status_code=502,
   content={"error": str(exc)})`. Since the four new classes subclass
   `WebSearchUpstreamError`, Starlette's `ExceptionMiddleware` will match them
   via MRO lookup without any new handler registration.
   **Corrected 2026-07-20:** this assumption originally attributed the four
   subclasses' addition to "the `web_search_models.py` procedure document"
   (i.e. `implementations/20260720-080006_web_search_models.py.md`) — verified
   by reading that document, it does not cover these classes (its scope is
   config validation + query normalization only). They must be added to
   `web_search_models.py` as part of implementing
   `implementations/20260720-081016_search_provider.py.md` (see that
   document's own correction), which must land before this test file.
2. The call chain for `/v1/call_tool` is: `call_tool()` →
   `_dispatch_web_tool()` → `dispatch_web_tool()` (in `formatters.py`) →
   `dispatch_tool(_WEB_DISPATCH, name, args)` → `fdisp_search_web()` →
   `search_web()` → `search_duckduckgo()`. The simplest, most robust
   monkeypatch point for this test is `search_duckduckgo` itself (patched to
   an async function that immediately raises the target exception), rather
   than trying to trigger a real timeout/network condition end-to-end through
   the whole HTTP stack.
3. `TestClient` from `fastapi.testclient` is the established convention in
   this repo for exactly this kind of test (confirmed:
   `tests/test_call_tool_validation.py` uses `TestClient(read_server.app)` /
   `TestClient(write_server.app)` / `TestClient(delete_server.app)` for other
   MCP servers' `/v1/call_tool` endpoints) — `web_search_server.app` should be
   imported and used the same way.
4. Request body shape matches `CallToolRequest` (`mcp_servers.models`): a
   `name` field and an `args` dict field — confirmed by `call_tool()`'s
   signature (`req: CallToolRequest`) and usage (`req.name`, `req.args`).

## Implementation

### Target file

`tests/test_web_search_server.py`

### Procedure

1. Import `TestClient` from `fastapi.testclient`; import
   `mcp_servers.web_search.web_search_server` as the module under test (mirror
   `tests/test_call_tool_validation.py`'s `from mcp_servers.file import
   read_server` style, adapted to `from mcp_servers.web_search import
   web_search_server`).
2. For each of the four new exception classes, write one test that:
   - monkeypatches `mcp_servers.web_search.search_provider.search_duckduckgo`
     (the actual function object referenced by `formatters.py`'s `from
     mcp_servers.web_search.search_provider import search_duckduckgo` import —
     patch at the point it is looked up, i.e.
     `mcp_servers.web_search.formatters.search_duckduckgo`, since Python binds
     the name into `formatters`'s namespace at import time) to an async fake
     that raises the target exception instance.
   - creates `client = TestClient(web_search_server.app)`.
   - posts `client.post("/v1/call_tool", json={"name": "search_web", "args":
     {"query": "test query"}})`.
   - asserts `response.status_code == 502` and
     `response.json() == {"error": "<expected message>"}` (or at least that
     `"error"` key is present and contains the expected substring, to avoid
     over-coupling to exact message text produced deep in `search_provider.py`
     — prefer substring assertion for messages originating in
     `search_provider.py`, exact-match only for a message this test itself
     controls via the fake's raised exception).

### Method

FastAPI `TestClient`-based integration test at the HTTP boundary, following
the exact existing pattern from `tests/test_call_tool_validation.py`. No real
network I/O; `search_duckduckgo` is faked to raise directly, isolating this
test to "does the exception middleware correctly map subclass → 502" rather
than re-testing provider-level classification logic (already covered by
`tests/test_web_search_provider.py`).

### Details

Illustrative skeleton (pseudocode, not production code):

```python
from fastapi.testclient import TestClient
from mcp_servers.web_search import web_search_server
from mcp_servers.web_search.web_search_models import (
    WebSearchTimeoutError,
    WebSearchNetworkError,
    WebSearchProviderError,
    WebSearchParseError,
)

class TestCallToolErrorClassification:
    @pytest.mark.parametrize("exc_cls", [
        WebSearchTimeoutError,
        WebSearchNetworkError,
        WebSearchProviderError,
        WebSearchParseError,
    ])
    def test_exception_subclass_returns_502(self, monkeypatch, exc_cls):
        async def _raise(*args, **kwargs):
            raise exc_cls("boom")

        monkeypatch.setattr(
            "mcp_servers.web_search.formatters.search_duckduckgo", _raise
        )
        client = TestClient(web_search_server.app)
        resp = client.post(
            "/v1/call_tool", json={"name": "search_web", "args": {"query": "q"}}
        )
        assert resp.status_code == 502
        assert resp.json() == {"error": "boom"}
```

Confirm the exact monkeypatch target path by checking how `formatters.py`
imports `search_duckduckgo` (`from mcp_servers.web_search.search_provider
import search_duckduckgo` — this binds the name in `formatters`'s own module
namespace, so patching `mcp_servers.web_search.search_provider.search_duckduckgo`
directly would NOT affect `formatters.py`'s already-bound reference; the patch
target must be `mcp_servers.web_search.formatters.search_duckduckgo`).

## Validation plan

- `uv run pytest tests/test_web_search_server.py -v` — all 4 parametrized cases
  pass with `502` and correct error body.
- `uv run pytest tests/test_web_search_provider.py tests/test_web_search_formatters.py tests/test_web_search_server.py tests/test_web_search_models.py -v`
  — combined run per plan's Validation plan table.
- `uv run ruff check tests/` / `uv run mypy scripts/` — clean.
- `uv run pytest` (full suite) and
  `uv run pytest tests/test_mdq_rag_boundary.py` — no new failures.
- `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` —
  the exception-handler dispatch path is exercised for all four new subclasses.
