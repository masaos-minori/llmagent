# Implementation procedure: tests/test_web_search_audit.py

Source plan: `plans/20260719-193902_plan.md` (Implementation step 6, first
bullet)

## Goal

Add a new test file verifying that `web_search_server.py::call_tool()`
unconditionally emits a classified audit record for every outcome: success,
zero-result, validation error, unknown tool, and provider timeout — matching
the requirement's acceptance criterion that audit logging happens on every
path, not just the happy path (the gap identified in the current code, where
`_audit_log(...)` at `web_search_server.py:96-104` is only reached after a
successful, non-raising `_dispatch_web_tool` call).

## Scope

**In scope:**
- New file `tests/test_web_search_audit.py`.
- Tests exercise `call_tool()` (via FastAPI `TestClient` against
  `web_search_server.app`, matching the existing pattern in
  `tests/test_call_tool_validation.py` for other MCP servers) and assert on
  captured audit log records (via `caplog` or a monkeypatched `_audit_log`/
  logger, whichever proves cleaner — decide during implementation).
- Cases: success (mocked `search_duckduckgo` returns results), zero-result
  (mocked to raise `WebSearchUpstreamError("No results returned from
  DuckDuckGo")`, which is what `formatters.py::search_web` raises today when
  `results` is empty — confirmed at `formatters.py:52-55`), validation error
  (missing/invalid `query` triggering Pydantic validation before reaching
  the handler, or a `ValueError` path if applicable), unknown tool name,
  provider timeout (mocked `search_duckduckgo` to raise
  `WebSearchUpstreamError("DuckDuckGo search failed: ...timeout...")`).

**Out of scope:**
- Testing `health.py`/`metrics.py` internals directly (covered by their own
  test files, `test_web_search_health.py`/`test_web_search_metrics.py`).
- Testing HTTP status codes in detail (covered by `test_web_search_server.py`,
  which already exists per a sibling design cycle covering `/v1/call_tool`
  502 behavior).

## Assumptions

1. `tests/test_web_search_audit.py` does not exist yet (confirmed: only
   `tests/test_web_search_models.py` exists under `tests/` for this module
   today).
2. `_audit_log` (`scripts/mcp_servers/audit.py:16-42`) emits one
   `logger.info(json.dumps(record, ...))` call per invocation — the test can
   capture this via `caplog.at_level(logging.INFO, logger="mcp_servers.web_search.web_search_server")`
   and parse the JSON record from `caplog.records[i].message`, OR by
   monkeypatching `mcp_servers.web_search.web_search_server._audit_log` with
   a stub that records call kwargs — the latter is more direct and avoids
   JSON-parsing brittleness; prefer it, matching how
   `tests/test_web_search_models.py` favors direct, explicit assertions over
   log-scraping.
3. Depends on the `web_search_server.py` refactor (separate implementation
   doc, `implementations/20260720-081553_web_search_server.py.md`) being
   applied first — these tests characterize the *target* behavior (audit
   always fires), which does not hold on the current, unrefactored code for
   the zero-result/timeout/unexpected-error paths.

## Implementation

### Target file

`tests/test_web_search_audit.py` (new)

### Procedure

1. Import `TestClient` from `fastapi.testclient`, `web_search_server.app`
   from `mcp_servers.web_search.web_search_server`, and `pytest`.
2. Use `monkeypatch` to patch
   `mcp_servers.web_search.web_search_server._audit_log` with a recording
   stub (a simple list-appending closure or `unittest.mock.MagicMock`)
   before each test, so assertions can inspect `outcome`/`error_type`/
   `server_key`/`detail` kwargs without depending on log formatting.
3. Use `monkeypatch` to patch
   `mcp_servers.web_search.search_provider.search_duckduckgo` (the actual
   network-calling function, confirmed at `search_provider.py:22`) to return
   canned results or raise canned exceptions per test case — this is the
   narrowest patch point that avoids real network calls while still
   exercising the real `formatters.py::search_web`/`fdisp_search_web` logic.
4. Write one test per case:
   - `test_audit_emitted_on_success`: patch `search_duckduckgo` to return a
     non-empty list of `SearchResult`; POST `/v1/call_tool` with
     `{"name": "search_web", "args": {"query": "python"}}`; assert the audit
     stub was called once with `outcome="ok"` and `error_type=""`.
   - `test_audit_emitted_on_zero_result`: patch `search_duckduckgo` to
     return `[]`, which causes `formatters.py::search_web` to raise
     `WebSearchUpstreamError("No results returned from DuckDuckGo")`
     (`formatters.py:52-55`); assert the audit stub still fires with
     `outcome="error"` (before the refactor this assertion fails — that is
     exactly the bug this plan fixes).
   - `test_audit_emitted_on_validation_error`: POST with an invalid payload
     (e.g. empty `query`, violating `SearchRequest`'s `min_length=1`); assert
     audit fires with `outcome="error"` and an `error_type` indicating
     validation.
   - `test_audit_emitted_on_unknown_tool`: POST with `{"name":
     "not_a_real_tool", "args": {}}`; assert audit fires with `outcome="error"`.
   - `test_audit_emitted_on_timeout`: patch `search_duckduckgo` to raise
     `WebSearchUpstreamError("DuckDuckGo search failed: Timeout")`; assert
     audit fires with `outcome="error"` and `error_type == "timeout"` (per
     the UNK-1 substring-classification default in the `web_search_server.py`
     refactor doc).
5. Each test should assert the audit stub was called **exactly once** (not
   zero, not more than once) to directly verify "unconditionally emits...for
   every tool call" — this is the core acceptance criterion.

### Method

- Use `pytest.fixture` for a shared `TestClient(app)` instance if multiple
  tests need it, following existing conventions in
  `tests/test_call_tool_validation.py` (reference for other MCP servers'
  `/v1/call_tool` test style).
- Prefer `monkeypatch.setattr` over `unittest.mock.patch` context managers,
  matching the plan's own phrasing ("assert via caplog / a fake logger,
  matching the existing test style in `tests/test_web_search_models.py`") —
  but since `test_web_search_models.py` doesn't itself test logging, use
  `monkeypatch` as the closest idiomatic choice for this codebase's pytest
  usage.

### Details

- Import path for the app under test: `from
  mcp_servers.web_search.web_search_server import app`.
- Import path for the patch target: `mcp_servers.web_search.search_provider.search_duckduckgo`
  — patch at the point of use inside `formatters.py`'s module namespace if
  `formatters.py` imports it by name (confirmed: `formatters.py:23` does
  `from mcp_servers.web_search.search_provider import search_duckduckgo`),
  so the correct monkeypatch target is
  `mcp_servers.web_search.formatters.search_duckduckgo`, not the
  `search_provider` module attribute (Python name-binding: patch where the
  name is looked up, not where it's defined).
- No real network access must occur in this test file — confirm no test
  reaches `duckduckgo_search.DDGS` for real.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Format/lint | `uv run ruff format scripts/ tests/ && uv run ruff check scripts/ tests/` | 0 errors |
| Type check | `uv run mypy scripts/` (tests/ covered by pre-commit's mypy run per `rules/coding.md`) | no new errors |
| Targeted test | `uv run pytest tests/test_web_search_audit.py -v` | all 5 cases pass, audit called exactly once per case |
| Full suite | `uv run pytest -v` | no new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥ 90% on changed lines |
