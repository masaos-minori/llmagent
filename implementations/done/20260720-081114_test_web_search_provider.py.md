# Implementation Procedure: tests/test_web_search_provider.py (new file)

Source plan: `plans/20260719-193357_plan.md` (Phase 2, Implementation steps item
"Write `tests/test_web_search_provider.py`: one result, empty list (no
exception, returns `[]`), timeout (patch `asyncio.wait_for` or use a slow fake
`_sync_search` with a tiny configured timeout), runtime/network error,
malformed result object.").

## Goal

Unit-test `search_duckduckgo()` (in `scripts/mcp_servers/web_search/search_provider.py`,
once updated per its own procedure document) against every new code path: a
normal single-result search, an empty-result search (must return `[]`, must NOT
raise), a timeout, a network/runtime failure, and a malformed (non-dict) raw
result item.

## Scope

**In scope:**
- New test file `tests/test_web_search_provider.py`.
- Tests exercise `search_duckduckgo()` directly (not through the FastAPI layer —
  that is covered by `tests/test_web_search_server.py`).
- `DDGS` (the underlying `duckduckgo_search` client) is monkeypatched/faked in
  every test — no real network calls.

**Out of scope:**
- No test of `formatters.py`'s `search_web()`/`fdisp_search_web()` (covered by
  `tests/test_web_search_formatters.py`).
- No test of the FastAPI `/v1/call_tool` HTTP boundary (covered by
  `tests/test_web_search_server.py`).
- No test of `WebSearchConfig` parsing/validation itself (covered by
  `tests/test_web_search_models.py`, already existing).

## Assumptions

1. `search_duckduckgo()`'s updated signature (per the `search_provider.py`
   procedure document) is
   `async def search_duckduckgo(query: str, max_results: int, search_timeout_sec: float) -> list[SearchResult]`.
2. Existing test-suite conventions (verified in `tests/test_web_search_models.py`):
   plain `pytest` classes grouped by behavior (`class TestXxx:`), `from __future__
   import annotations` at top, imports from `mcp_servers.web_search.web_search_models`
   directly (module path is `web_search_models`, not `models`).
3. `DDGS` is used as a context manager (`with DDGS() as ddgs: ddgs.text(...)`)
   inside `_sync_search` (a closure, not directly testable/importable) — tests
   must patch `duckduckgo_search.DDGS` itself (e.g.
   `monkeypatch.setattr("mcp_servers.web_search.search_provider.DDGS", FakeDDGS)`)
   rather than trying to reach into the closure.
4. Timeout test: rather than patching `asyncio.wait_for` (fragile, changes
   library-internal call semantics), use a fake `DDGS` whose `.text()` sleeps
   longer than a small configured `search_timeout_sec` (e.g. `time.sleep(0.2)`
   inside the sync fake, with `search_timeout_sec=0.01`), so the real
   `asyncio.wait_for` timeout path fires — this matches the plan's suggested
   "slow fake `_sync_search`" approach and avoids depending on
   `asyncio.wait_for`'s internal implementation.
5. Malformed-result test constructs a fake `DDGS.text()` return value containing
   a non-`dict` item (e.g. `[{"title": "ok", ...}, "not-a-dict"]`) and asserts
   `WebSearchParseError` is raised.

## Implementation

### Target file

`tests/test_web_search_provider.py`

### Procedure

1. Import `search_duckduckgo` and the exception classes
   (`WebSearchTimeoutError`, `WebSearchNetworkError`, `WebSearchProviderError`,
   `WebSearchParseError`) from `mcp_servers.web_search.search_provider` /
   `mcp_servers.web_search.web_search_models` respectively.
2. Define a small fake `DDGS`-like class/context-manager per test (or one
   parametrized fixture) with a `.text(query, max_results=...)` method whose
   return value or side effect varies per test case.
3. Use `monkeypatch.setattr` to replace `mcp_servers.web_search.search_provider.DDGS`
   with the fake for the duration of each test.
4. Use `pytest.mark.asyncio` (or the repo's existing async-test convention —
   check `pyproject.toml`/`conftest.py` for `asyncio_mode`) to run `await
   search_duckduckgo(...)` inside each test.
5. Assertions:
   - one-result case: returned list has length 1, fields map correctly
     (`title`/`href→url`/`body`/`provider="duckduckgo"`).
   - empty-list case: returns `[]`; no exception raised.
   - timeout case: `pytest.raises(WebSearchTimeoutError)`.
   - runtime/network error case: fake `.text()` raises `RuntimeError` or
     `OSError`; `pytest.raises(WebSearchNetworkError)`.
   - malformed-result case: fake `.text()` returns a list containing a
     non-`dict` item; `pytest.raises(WebSearchParseError)`.

### Method

Standalone `pytest` test module using `monkeypatch` + async test functions
(no `TestClient`/HTTP layer involved — this is a pure unit test of the
provider function). No fixtures shared with other test files needed beyond
what `conftest.py` already provides (if anything relevant exists there —
check before assuming none).

### Details

Illustrative skeleton (pseudocode, not production code):

```python
class TestSearchDuckDuckGo:
    async def test_one_result(self, monkeypatch): ...
        # fake DDGS.text -> [{"title": "t", "href": "u", "body": "b"}]
        # assert len(result) == 1, result[0].url == "u", ...

    async def test_empty_results_no_exception(self, monkeypatch): ...
        # fake DDGS.text -> []
        # assert await search_duckduckgo(...) == []

    async def test_timeout_raises_timeout_error(self, monkeypatch): ...
        # fake DDGS.text sleeps longer than search_timeout_sec
        # with pytest.raises(WebSearchTimeoutError): await search_duckduckgo(..., search_timeout_sec=0.01)

    async def test_runtime_error_raises_network_error(self, monkeypatch): ...
        # fake DDGS.text raises RuntimeError("boom")
        # with pytest.raises(WebSearchNetworkError): ...

    async def test_malformed_item_raises_parse_error(self, monkeypatch): ...
        # fake DDGS.text -> [{"title": "ok"}, "not-a-dict"]
        # with pytest.raises(WebSearchParseError): ...
```

Check the repo's async-test runner setup (`pyproject.toml` `[tool.pytest.ini_options]`
`asyncio_mode`, or explicit `@pytest.mark.asyncio` decorators used elsewhere,
e.g. in other MCP server test files) before finalizing the async test
mechanism, to match existing convention exactly.

## Validation plan

- `uv run pytest tests/test_web_search_provider.py -v` — all 5+ cases pass.
- `uv run ruff check tests/` / `uv run mypy scripts/` (per `rules/coding.md`,
  `tests/` is covered by pre-commit's mypy run) — clean.
- `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` —
  new `search_provider.py` branches (timeout/network/provider/parse) covered.
- `uv run pytest` (full suite) — no new failures.
