# Implementation procedure: tests/test_web_search_service.py

Source plan: `plans/done/20260719-195330_plan.md` (Phase 2 test checklist,
Validation plan).

## Goal

Add `tests/test_web_search_service.py`, a unit-test module covering
`scripts/mcp_servers/web_search/service.py::search_web()` in isolation: success
path, zero-result path, provider-timeout path, provider-error path, and the
health.py/metrics.py update side effects on each path.

## Scope

**In scope:**
- New file `tests/test_web_search_service.py`.
- Mocking `mcp_servers.web_search.search_provider.search_duckduckgo` (the only
  external/network-touching dependency of `service.search_web`) via
  `unittest.mock.patch` or a `pytest` fixture — no real DuckDuckGo network
  calls in tests.
- Asserting `health.py`/`metrics.py` module state transitions (via their
  public read accessors, e.g. `health.is_degraded()` /
  `health.health_details()` and `metrics.snapshot()`) after calling
  `service.search_web(...)`, resetting module-level singleton state between
  tests (see Assumptions #2).

**Out of scope:**
- Testing `search_provider.py`'s own DuckDuckGo-call logic (covered by
  `tests/test_web_search_provider.py`, already documented in
  `implementations/20260720-081114_test_web_search_provider.py.md`).
- Testing `formatters.py`'s text-formatting output (covered by
  `tests/test_web_search_formatters.py`, already documented in
  `implementations/20260720-081144_test_web_search_formatters.py.md`).
- Testing `web_search_server.py`'s HTTP layer (covered by
  `tests/test_web_search_server.py`).

## Assumptions

1. `service.search_web()` has the signature and behavior described in
   `implementations/20260720-083212_service.py.md`: `async def
   search_web(args: dict[str, Any]) -> SearchResponse`, raising
   `WebSearchUpstreamError` on provider failure, and — until Issue 2 lands —
   also raising `WebSearchUpstreamError` on zero results (post-Issue-2:
   returns `SearchResponse(results=[])`). Tests must be written against
   whichever behavior is actually landed at implementation time; if written
   before Issue 2 lands, include a `pytest.mark.xfail` or a clearly-named
   `test_zero_results_raises_pre_issue_2` that will need updating once Issue 2
   ships (do not silently assume the future behavior).
2. `health.py`/`metrics.py` hold process-global module-level singleton state
   (confirmed by their implementation docs: `implementations/20260720-081456_health.py.md`,
   `implementations/20260720-081528_metrics.py.md`). Each test must reset
   this state (e.g. a `pytest` fixture calling an internal reset helper, or
   `importlib.reload`, or monkeypatching the module's private counters back
   to zero in a fixture teardown) to avoid cross-test pollution — check
   whether `health.py`/`metrics.py`'s implementation exposes a test-only reset
   function; if not, flag this as a gap for whoever implements those modules
   (a `_reset_for_tests()` helper is a common, low-risk addition).
3. `pytest-asyncio` (or the repo's existing async test pattern — check
   `tests/test_web_search_provider.py`'s existing style once it exists, or any
   other `async def test_...` in `tests/` for the project's convention) is
   available for testing the `async def search_web` function.

## Implementation

### Target file

`tests/test_web_search_service.py` (new)

### Procedure

1. `test_search_web_success` — mock `search_duckduckgo` to return a
   non-empty `list[SearchResult]`; call `service.search_web({"query": "x",
   "max_results": 5})`; assert the returned `SearchResponse.results` matches,
   `provider == "duckduckgo"`; assert `metrics.snapshot()` reflects one
   successful query and `health.is_degraded()` is `False`
   (or `health.health_details()` shows a recent success).
2. `test_search_web_zero_results` — mock `search_duckduckgo` to return `[]`;
   assert behavior matches whichever of raise/empty-success is landed (see
   Assumptions #1); if it raises, assert metrics/health record a failure with
   an appropriate `error_type` (or, if the design intends zero-results-as-
   success to NOT count as a health/metrics failure, assert that explicitly —
   confirm at implementation time which the landed `_handle_empty_results`
   Design intends and pin that decision with a test).
3. `test_search_web_provider_timeout` — mock `search_duckduckgo` to raise
   `WebSearchUpstreamError("DuckDuckGo search failed: ...timeout...")`; assert
   `service.search_web(...)` propagates the same exception (no swallowing);
   assert `metrics.snapshot()` shows one failed query and
   `health.record_failure` was invoked (assert via `health.health_details()`
   surfacing a `last_error_type`/similar field, per that module's actual API).
4. `test_search_web_provider_error` — same as #3 but with a
   `WebSearchUpstreamError` whose message does not contain "timeout"; assert
   `error_type` classification differs from the timeout case if `service.py`
   or `web_search_server.py` classifies error types (cross-check against
   `implementations/20260720-081553_web_search_server.py.md`'s
   `_classify_upstream_error` helper — if that classification lives in
   `web_search_server.py` rather than `service.py`, this test should assert
   only that `health.record_failure()` was called with *some* reason string,
   not a specific classified value, to avoid over-specifying a boundary this
   file does not own).
5. Use `unittest.mock.patch("mcp_servers.web_search.service.search_duckduckgo",
   ...)` (patch at the point of use inside `service.py`, not at
   `search_provider.py`'s definition site) so the mock intercepts the actual
   call `service.py` makes.

### Method

Standard `pytest` unit tests with `unittest.mock.patch` for the provider
boundary; no real network I/O; no DB; module-level singleton state in
`health.py`/`metrics.py` reset per test via a fixture.

### Details

Illustrative shape (pseudocode, not production code):

```python
import pytest
from unittest.mock import patch
from mcp_servers.web_search import service, health, metrics
from mcp_servers.web_search.web_search_models import WebSearchUpstreamError, SearchResult


@pytest.fixture(autouse=True)
def _reset_state():
    health._reset_for_tests()   # exact name TBD per health.py's actual API
    metrics._reset_for_tests()  # exact name TBD per metrics.py's actual API
    yield


@pytest.mark.asyncio
async def test_search_web_success():
    fake_results = [SearchResult(title="t", url="u", body="b", provider="duckduckgo")]
    with patch("mcp_servers.web_search.service.search_duckduckgo", return_value=fake_results):
        resp = await service.search_web({"query": "hello", "max_results": 5})
    assert resp.results == fake_results
    assert metrics.snapshot()["queries_succeeded"] == 1


@pytest.mark.asyncio
async def test_search_web_provider_error():
    with patch(
        "mcp_servers.web_search.service.search_duckduckgo",
        side_effect=WebSearchUpstreamError("DuckDuckGo search failed: boom"),
    ):
        with pytest.raises(WebSearchUpstreamError):
            await service.search_web({"query": "hello", "max_results": 5})
    assert metrics.snapshot()["queries_failed"] == 1
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Targeted test run | `uv run pytest tests/test_web_search_service.py -v` | all cases pass |
| Type check | `uv run mypy scripts/` (tests covered by pre-commit's mypy run per `rules/coding.md`) | no new errors |
| Full suite | `uv run pytest -v` | no new failures |
| Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | >= 90% on changed lines, including `service.py` |
