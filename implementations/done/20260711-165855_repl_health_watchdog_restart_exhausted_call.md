# Implementation Doc: Watchdog Calls `record_restart_exhausted()` on Restart-Limit Exhaustion

## Goal

Wire `_watchdog_check_http()`'s existing restart-limit-reached branch to call
the new `McpServerHealthRegistry.record_restart_exhausted()` method, so
restart exhaustion leaves a deterministic, operator-visible trace instead of
only a log line.

## Scope

**In scope:**
- `scripts/agent/repl_health.py`: in `_watchdog_check_http()`, the branch that
  currently logs a warning and returns early when
  `restart_counts[key] >= max_restarts` must also call
  `health_registry.record_restart_exhausted(key)` before returning.

**Out of scope:**
- The `record_restart_exhausted()` method itself (Phase 1 —
  `scripts/shared/mcp_health.py`, documented separately).
- Watchdog probe classification/logging changes (sibling plan
  `plans/20260711-134610_plan.md`).
- Any change to `max_restarts` default or `mcp_watchdog_max_restarts` config
  semantics.

## Assumptions

- `_watchdog_check_http()` already has an early `return` in the
  "unreachable or restart_recommended" branch when
  `count >= max_restarts`, placed **before** the `record_failure(key)` call
  at the bottom of the function (plan Assumption 2, confirmed by direct
  read) — today this leaves no trace in `HealthRegistry` beyond whatever
  state prior restart attempts already produced.
- `ctx.services_required.health_registry` is the same `McpServerHealthRegistry`
  instance shared with `ToolExecutor` (plan Assumption 1) — no new wiring is
  needed to obtain the registry reference; the existing code path already
  accesses it (used for `record_failure` elsewhere in this function).
- The registry access must remain guarded (`if ctx.services_required.health_registry:`)
  consistent with existing null-checks in this function, since
  `health_registry` may be `None` in some configurations/tests.

## Implementation

### Target file

`scripts/agent/repl_health.py`

### Procedure

1. Locate `_watchdog_check_http()` and find the `if count >= max_restarts:`
   branch (the restart-limit-reached early-return path).
2. Immediately after the existing `logger.warning(...)` call in that branch,
   add a guarded call to `health_registry.record_restart_exhausted(key)`.
3. Keep the existing `return` as the last statement in the branch — do not
   reorder relative to the warning log.
4. Do not modify the `record_failure(key)` call at the bottom of the function
   (that remains reachable only for the non-exhausted-restart code paths, per
   Assumption 2 / plan Design).

### Method

```python
if count >= max_restarts:
    logger.warning(
        "Watchdog: %r unreachable; restart limit reached (%s)", key, max_restarts,
    )
    if ctx.services_required.health_registry:
        ctx.services_required.health_registry.record_restart_exhausted(key)
    return
```

### Details

- Re-read the actual surrounding code at implementation time to confirm exact
  variable names (`key`, `count`, `max_restarts`, `ctx`) match current source
  — the plan explicitly flags this branch may have drifted since being
  written (plan Design section note).
- This call must be placed inside the existing `count >= max_restarts`
  branch only — do not add it to any other branch of
  `_watchdog_check_http()`.
- No new imports required; `McpServerHealthRegistry` is already referenced
  in this module via `ctx.services_required.health_registry`.
- This change depends on Phase 1 (`record_restart_exhausted()` existing on
  `McpServerHealthRegistry`) having landed first.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/repl_health.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/repl_health.py` | No new errors |
| Tests | `uv run pytest tests/test_watchdog.py -v` | All pass, including the 2 new tests added in Phase 5 (`test_restart_limit_reached_does_not_call_lifecycle_restart_again`, `test_restart_limit_reached_calls_record_restart_exhausted`) |
| Regression | `uv run pytest tests/test_tool_executor.py tests/test_agent_factory.py -q` | No new failures (confirms shared-registry wiring unaffected) |
