# Implementation procedure: tests/test_web_search_health.py

Source plan: `plans/20260719-193902_plan.md` (Implementation step 6, second
bullet; Design §1)

## Goal

Add a new test file verifying the pure in-memory behavior of the new
`scripts/mcp_servers/web_search/health.py` module: state after a success,
after one failure, after repeated (degraded-threshold) failures, and after
recovery from a degraded state.

## Scope

**In scope:**
- New file `tests/test_web_search_health.py`.
- Direct unit tests against `health.py`'s public functions
  (`record_success`, `record_failure`, `is_degraded`, `health_details`), no
  FastAPI/HTTP involvement.

**Out of scope:**
- Testing `/health`'s HTTP response shape end-to-end (covered by
  `tests/test_web_search_server.py`, already documented by a sibling design
  cycle — that existing doc explicitly scopes out `/health` testing, so any
  `/health`-endpoint-level assertion needed for *this* plan's health/metrics
  wiring should live here or in a follow-up to that doc, decided during
  implementation; this doc covers only the module-level unit tests).
- `metrics.py` (covered by `test_web_search_metrics.py`).

## Assumptions

1. `tests/test_web_search_health.py` does not exist yet.
2. Depends on `scripts/mcp_servers/web_search/health.py` existing first (see
   `implementations/20260720-081456_health.py.md`) — this test file cannot
   be written to pass until that module is implemented; the design procedure
   below assumes the module's final public API is: `record_success()`,
   `record_failure(error_type: str)`, `is_degraded() -> bool`,
   `health_details() -> dict[str, object]`, `reset()` (test helper), and
   `DEGRADED_THRESHOLD: int = 3`.
3. Module state is a singleton (module-level `_health` instance) — tests
   must call `health.reset()` in a fixture (`autouse=True`) before each test
   to avoid cross-test state leakage, since there is no per-instance
   isolation without it.

## Implementation

### Target file

`tests/test_web_search_health.py` (new)

### Procedure

1. Import `mcp_servers.web_search.health as health` (or the equivalent named
   imports: `record_success`, `record_failure`, `is_degraded`,
   `health_details`, `reset`, `DEGRADED_THRESHOLD`).
2. Add an `autouse=True` `pytest.fixture` that calls `health.reset()` before
   each test, so tests don't leak `consecutive_failures` state into each
   other via the module singleton.
3. Write test cases:
   - `test_initial_state_not_degraded`: fresh state → `is_degraded()` is
     `False`; `health_details()["consecutive_failures"] == 0`.
   - `test_record_success_sets_timestamp`: call `record_success()`; assert
     `health_details()["last_success_at"]` is a non-`None` float timestamp
     (e.g. `> 0` or compare against `time.time()` within a tolerance).
   - `test_single_failure_not_yet_degraded`: call `record_failure("timeout")`
     once; assert `is_degraded()` is `False` (below `DEGRADED_THRESHOLD`) and
     `health_details()["last_error_type"] == "timeout"`.
   - `test_repeated_failures_flip_degraded`: call `record_failure(...)`
     `DEGRADED_THRESHOLD` times (3, per Assumption 3 of the `health.py`
     implementation doc / plan's UNK-2 default); assert `is_degraded()` is
     `True` after the threshold-th call, and `False` before it (test the
     boundary at `DEGRADED_THRESHOLD - 1` calls too).
   - `test_success_after_failures_resets_degraded`: call `record_failure(...)`
     `DEGRADED_THRESHOLD` times, then `record_success()`; assert
     `is_degraded()` is `False` again and `consecutive_failures == 0`.
   - `test_health_details_shape`: assert `health_details()` returns a dict
     containing all expected keys (`provider`, `last_success_at`,
     `last_failure_at`, `last_error_type`, `consecutive_failures`,
     `degraded`) with correct types.

### Method

- Pure unit tests, no mocking of external systems needed — `health.py` has
  no I/O.
- Use `pytest`'s plain `assert` statements, matching the style in
  `tests/test_web_search_models.py` (class-per-concern grouping, e.g.
  `class TestProviderHealth:` mirroring that file's `class
  TestWebSearchConfig:` pattern).

### Details

- Import path: `from mcp_servers.web_search import health` or `import
  mcp_servers.web_search.health as health`, matching whichever import style
  the `health.py` implementation doc settles on for
  `web_search_server.py`'s own import (keep both call sites consistent).
- If `health.py` ends up exposing the `ProviderHealth` dataclass directly
  (not just module functions), also add a `test_provider_health_defaults`
  case asserting the dataclass's field defaults, mirroring
  `tests/test_web_search_models.py::TestWebSearchConfig::test_defaults`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Format/lint | `uv run ruff format scripts/ tests/ && uv run ruff check scripts/ tests/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Targeted test | `uv run pytest tests/test_web_search_health.py -v` | all cases pass |
| Full suite | `uv run pytest -v` | no new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥ 90% on changed lines |
