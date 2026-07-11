# Implementation Doc: Tests for Restart-Limit-Reached Behavior

## Goal

Add test coverage for the `count >= max_restarts` branch of
`_watchdog_check_http()`, which is not currently covered — verifying both
that no further restart is attempted and that
`record_restart_exhausted()` is called, then run the full validation plan
for this change set.

## Scope

**In scope:**
- `tests/test_watchdog.py`: add two new tests to `TestWatchdogCheckHttp` (or
  the equivalent existing test class) exercising the restart-limit-reached
  branch.
- Run the complete validation plan (lint, type check, architecture, tests,
  regression, manual check, docs consistency) across all files touched by
  this plan.

**Out of scope:**
- Any production code change — this phase is test-only plus verification.
- New test files for `mcp_health.py` or `cmd_mcp.py` beyond what's specified
  (existing `tests/test_mcp_health_degraded.py`, `tests/test_cmd_mcp.py` are
  reused as-is per the plan's Validation plan table).

## Assumptions

- None of the 3 existing tests in `TestWatchdogCheckHttp` pre-populate
  `restart_counts` at or above `max_restarts` (plan Affected-areas table,
  confirmed by reading all 3 existing tests) — this is a genuine coverage
  gap, not a duplicate.
- Test fixtures for `_watchdog_check_http()` already provide a mockable
  `lifecycle.restart` and a `health_registry` (or equivalent) fixture,
  reusable for both new tests — confirm by reading existing test setup in
  this file before writing the new tests.
- This phase depends on Phase 1 and Phase 2 (the method and its call site)
  having landed, since the new tests assert on `record_restart_exhausted()`'s
  effect.

## Implementation

### Target file

`tests/test_watchdog.py`

### Procedure

1. Read the existing `TestWatchdogCheckHttp` test class in full to identify
   the fixture/mock setup pattern used for `lifecycle`, `health_registry`,
   `restart_counts`, and `max_restarts`.
2. Add `test_restart_limit_reached_does_not_call_lifecycle_restart_again`:
   - Pre-populate `restart_counts = {"test-server": 3}` with
     `max_restarts=3`.
   - Invoke `_watchdog_check_http()` (or the relevant unit under test) for
     `"test-server"`.
   - Assert `lifecycle.restart` is **not** called (confirms the early-return
     guard fires before any restart attempt).
3. Add `test_restart_limit_reached_calls_record_restart_exhausted`:
   - Same setup (`restart_counts = {"test-server": 3}`, `max_restarts=3`).
   - Invoke the same code path.
   - Assert `health_registry.get_degraded_reason("test-server") ==
     "restart_limit_reached"`.
4. Follow existing naming/parametrization conventions in this file (e.g. if
   other tests use `pytest.mark.parametrize` or shared fixtures, match that
   style rather than introducing a new pattern).

### Method

Pseudocode sketch (adapt to the file's actual fixture/mocking style —
confirm exact fixture names by reading the file first):

```python
def test_restart_limit_reached_does_not_call_lifecycle_restart_again(...):
    # arrange: restart_counts = {"test-server": 3}, max_restarts = 3
    # act: call _watchdog_check_http(...) for "test-server"
    # assert: lifecycle.restart.assert_not_called()
    ...

def test_restart_limit_reached_calls_record_restart_exhausted(...):
    # arrange: restart_counts = {"test-server": 3}, max_restarts = 3
    # act: call _watchdog_check_http(...) for "test-server"
    # assert: health_registry.get_degraded_reason("test-server") == "restart_limit_reached"
    ...
```

### Details

- Do not modify or remove any of the 3 existing tests in this class.
- Ensure both new tests are independent (no shared mutable state leaking
  between them) — use fresh fixture instances per test, matching existing
  patterns in the file.
- After adding the tests, run the full validation plan below across all
  files this plan touched (`mcp_health.py`, `repl_health.py`, `cmd_mcp.py`,
  the two docs files, and this test file) to confirm the whole change set is
  consistent.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/mcp_health.py scripts/agent/repl_health.py scripts/agent/commands/cmd_mcp.py tests/test_watchdog.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/mcp_health.py scripts/agent/repl_health.py scripts/agent/commands/cmd_mcp.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest tests/test_watchdog.py tests/test_mcp_health_degraded.py -v` | All pass, including the 2 new tests |
| Regression | `uv run pytest tests/test_tool_executor.py tests/test_agent_factory.py -q` | No new failures (confirms shared-registry wiring in `factory.py` is unchanged, only documented) |
| Manual | `uv run python -c "..."` build a registry, call `record_restart_exhausted`, confirm `get_state()` unchanged and `get_degraded_reason()` returns `"restart_limit_reached"` | Matches Design |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
