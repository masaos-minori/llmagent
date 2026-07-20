# Implementation Procedure: tests/test_web_search_formatters.py (new file)

Source plan: `plans/20260719-193357_plan.md` (Phase 2, Implementation steps item
"Write `tests/test_web_search_formatters.py`: `fdisp_search_web()` returns 'No
search results found.' for zero results; normal-results formatting unchanged
(snapshot existing behavior).").

## Goal

Verify that `fdisp_search_web()` (in `scripts/mcp_servers/web_search/formatters.py`)
formats a zero-result search as the plain-text string `"No search results
found."` with no exception raised (post-fix behavior, once the
`search_web()` raise-on-empty branch is removed per its own procedure
document), and that normal (non-empty) result formatting is unchanged from
today.

## Scope

**In scope:**
- New test file `tests/test_web_search_formatters.py`.
- Tests exercise `search_web()` and `fdisp_search_web()` directly, with
  `search_duckduckgo` monkeypatched (no real network / no dependency on
  `search_provider.py`'s internals — this is a formatter-layer test).
- `fmt_search_result()` formatting output covered incidentally via the
  normal-results test (existing single-item format string:
  `"[{i}] {title}\nURL: {url}\nProvider: {provider}\n{snippet}"`).

**Out of scope:**
- No test of `search_duckduckgo()`'s internal exception classification
  (covered by `tests/test_web_search_provider.py`).
- No test of the FastAPI HTTP layer (covered by `tests/test_web_search_server.py`).
- No test of the `_WEB_DISPATCH` table / `dispatch_web_tool()` routing itself
  (implicitly exercised, but not the focus).

## Assumptions

1. Post-fix `search_web()` no longer raises `WebSearchUpstreamError` for empty
   results; it returns `SearchResponse(query=..., results=[], provider="duckduckgo")`.
   `fdisp_search_web()`'s existing `if not result.results: return "No search
   results found."` branch (unchanged by this plan) is what tests must exercise
   — verified by direct read of the current file, this branch already exists
   today and needs no code change, only test coverage.
2. `search_web()`'s updated call to `search_duckduckgo(...)` requires a third
   `search_timeout_sec` argument (per the `search_provider.py`/`formatters.py`
   procedure documents) — the monkeypatched fake must accept whatever
   signature `search_duckduckgo` ends up with (accept `*args`/`**kwargs` in the
   fake to stay robust to the exact parameter name/order, or match it exactly
   once implementation confirms it).
3. Normal-results "snapshot" means: construct a fake `search_duckduckgo` that
   returns a fixed list of `SearchResult` objects, then assert the exact
   formatted string from `fdisp_search_web()` matches what today's
   `fmt_search_result()` + header logic already produces — i.e. this is a
   regression/characterization test of existing, unchanged formatting logic,
   not new behavior.

## Implementation

### Target file

`tests/test_web_search_formatters.py`

### Procedure

1. Import `fdisp_search_web`, `search_web` from
   `mcp_servers.web_search.formatters`; `SearchResult` from
   `mcp_servers.web_search.web_search_models`.
2. Monkeypatch `mcp_servers.web_search.formatters.search_duckduckgo` (the name
   imported into the `formatters` module namespace, per its `from
   mcp_servers.web_search.search_provider import search_duckduckgo` import) to
   an async fake returning a controlled list of `SearchResult`s or `[]`.
3. Async test functions (matching the repo's existing async-test convention —
   check `pyproject.toml`/`conftest.py`).
4. Assertions:
   - zero-results case: `await fdisp_search_web({"query": "x"})` == `"No search
     results found."`; and calling `search_web()` directly does not raise.
   - normal-results case: construct e.g. 2 fake `SearchResult`s; assert the
     returned string starts with the expected header
     (`"[Search: 2 results via duckduckgo]\n\n"`) and contains each result's
     formatted block in order.

### Method

Pure `pytest` + `monkeypatch` unit tests against the formatter functions; no
FastAPI `TestClient`, no real `DDGS`/network dependency — the provider layer is
faked out entirely at the `search_duckduckgo` import-site level.

### Details

Illustrative skeleton (pseudocode, not production code):

```python
class TestSearchWebEmptyResults:
    async def test_search_web_no_raise_on_empty(self, monkeypatch):
        # monkeypatch search_duckduckgo -> async fake returning []
        # resp = await search_web({"query": "x"})
        # assert resp.results == []

    async def test_fdisp_search_web_empty_message(self, monkeypatch):
        # same fake
        # assert await fdisp_search_web({"query": "x"}) == "No search results found."


class TestFdispSearchWebNormalResults:
    async def test_formats_results_unchanged(self, monkeypatch):
        # monkeypatch search_duckduckgo -> async fake returning
        # [SearchResult(title="A", url="u1", body="b1", provider="duckduckgo"),
        #  SearchResult(title="B", url="u2", body="b2", provider="duckduckgo")]
        # out = await fdisp_search_web({"query": "x"})
        # assert out.startswith("[Search: 2 results via duckduckgo]\n\n")
        # assert "[1] A" in out and "[2] B" in out
```

## Validation plan

- `uv run pytest tests/test_web_search_formatters.py -v` — both cases pass.
- `uv run pytest tests/test_web_search_provider.py tests/test_web_search_formatters.py tests/test_web_search_server.py tests/test_web_search_models.py -v`
  — combined run per plan's Validation plan table, no regressions.
- `uv run ruff check tests/` / `uv run mypy scripts/` — clean.
- `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` —
  the deleted-branch removal in `formatters.py` and the retained
  `fdisp_search_web` empty-branch are both covered.
- `uv run pytest` (full suite) — no new failures.
