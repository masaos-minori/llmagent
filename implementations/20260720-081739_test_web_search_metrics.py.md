# Implementation procedure: tests/test_web_search_metrics.py

Source plan: `plans/20260719-193902_plan.md` (Implementation step 6, third
bullet; Design §2)

## Goal

Add a new test file verifying that `scripts/mcp_servers/web_search/metrics.py`
counters update correctly on success/failure, that `average_latency_ms`
computes correctly (including the zero-queries edge case), and — critically —
that `snapshot()`'s output never contains the literal query text used in the
test, proving the "no full query text stored" requirement holds at the API
boundary.

## Scope

**In scope:**
- New file `tests/test_web_search_metrics.py`.
- Direct unit tests against `metrics.py`'s public functions (`record_query`,
  `snapshot`, `WebSearchMetrics.average_latency_ms`), no FastAPI/HTTP
  involvement.

**Out of scope:**
- Testing `/health`'s response shape (`test_web_search_server.py` / possibly
  extended `test_web_search_health.py` scope).
- `health.py` (covered by `test_web_search_health.py`).

## Assumptions

1. `tests/test_web_search_metrics.py` does not exist yet.
2. Depends on `scripts/mcp_servers/web_search/metrics.py` existing first (see
   `implementations/20260720-081528_metrics.py.md`) — assumes the module's
   final public API is: `record_query(success: bool, latency_ms: float,
   error_type: str = "") -> None`, `snapshot() -> dict[str, object]`,
   `reset()` (test helper).
3. Module state is a singleton — tests must reset it between test cases via
   an `autouse=True` fixture calling `metrics.reset()`.
4. `snapshot()`'s dict never takes a query string as input anywhere in the
   call chain being tested, so the "no query text" assertion is really
   checking that no test-supplied string sneaks into the dict via any other
   field (e.g. `error_type` should never be assigned an actual query value
   by mistake in these tests — keep the test's own `error_type` values
   generic like `"provider_error"`/`"timeout"`, distinct from any sample
   query string used elsewhere in the test, so the assertion is meaningful).

## Implementation

### Target file

`tests/test_web_search_metrics.py` (new)

### Procedure

1. Import `mcp_servers.web_search.metrics as metrics` (or named imports:
   `record_query`, `snapshot`, `reset`, `WebSearchMetrics`).
2. Add an `autouse=True` `pytest.fixture` calling `metrics.reset()` before
   each test.
3. Write test cases:
   - `test_initial_snapshot_all_zero`: fresh state → `snapshot()["queries_total"]
     == 0`, `["queries_succeeded"] == 0`, `["queries_failed"] == 0`,
     `["average_latency_ms"] == 0.0`, `["last_success_at"] is None`,
     `["last_failure_at"] is None`.
   - `test_record_success_updates_counters`: `record_query(success=True,
     latency_ms=120.0)`; assert `queries_total == 1`, `queries_succeeded ==
     1`, `queries_failed == 0`, `average_latency_ms == 120.0`,
     `last_success_at` is a non-`None` timestamp.
   - `test_record_failure_updates_counters`: `record_query(success=False,
     latency_ms=50.0, error_type="provider_error")`; assert `queries_total
     == 1`, `queries_failed == 1`, `last_error_type == "provider_error"`,
     `last_failure_at` is a non-`None` timestamp.
   - `test_average_latency_across_multiple_queries`: record 3 queries with
     known latencies (e.g. 100.0, 200.0, 300.0); assert
     `average_latency_ms == 200.0` (mean).
   - `test_snapshot_never_contains_query_text`: use a distinctive sample
     query string, e.g. `SAMPLE_QUERY = "distinctive_test_query_xyz123"`
     (defined at module scope, never passed into `record_query` — confirming
     by construction that the function signature has no parameter to accept
     it); call `record_query(success=True, latency_ms=10.0)` a few times;
     assert `SAMPLE_QUERY not in str(snapshot())` — this is a belt-and-
     suspenders check since the signature already makes it impossible to
     pass a query string, but it documents the intent directly as an
     executable assertion per the plan's Design §2 requirement.

### Method

- Pure unit tests, no mocking of external systems needed.
- Use `pytest`'s plain `assert` statements; follow
  `tests/test_web_search_models.py`'s class-grouping convention (e.g.
  `class TestWebSearchMetrics:`).

### Details

- Import path: `from mcp_servers.web_search import metrics` or `import
  mcp_servers.web_search.metrics as metrics`, matching whichever style
  `web_search_server.py`'s own import settles on.
- If `WebSearchMetrics` dataclass is exported directly, add a
  `test_metrics_defaults` case asserting field defaults, mirroring
  `tests/test_web_search_models.py::TestWebSearchConfig::test_defaults`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Format/lint | `uv run ruff format scripts/ tests/ && uv run ruff check scripts/ tests/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Targeted test | `uv run pytest tests/test_web_search_metrics.py -v` | all cases pass, including the no-query-text assertion |
| Full suite | `uv run pytest -v` | no new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥ 90% on changed lines |
