## Goal

Update `_watchdog_check_http()` in `agent/repl_health.py` to use `_probe_mcp_health_detail()` and gate restart decisions on `restart_recommended`, logging a warning for `operator_action_required=True` without restarting.

## Scope

- In-Scope:
  - Replace `probe_mcp_health()` call in `_watchdog_check_http()` with `_probe_mcp_health_detail()`
  - Change restart logic: restart only when `reachable=False` or `restart_recommended=True`
  - Add `operator_action_required=True` log path (WARNING level, no restart)
  - Reset `restart_counts[key] = 0` and record success when `reachable=True` and `restart_recommended=False`
- Out-of-Scope:
  - Changes to `watchdog_loop()` (covered in Step 6)
  - Changes to `probe_mcp_health()` (covered in Step 4)
  - Changes to the lifecycle manager or health registry

## Assumptions

1. `_probe_mcp_health_detail` is available after Step 4 is complete.
2. A server that is `reachable=True` but `status_code=503` and `restart_recommended=False` should NOT be restarted — the body classification overrides the HTTP status code.
3. A server that is `reachable=True` and `status_code=200` is always considered healthy (same as current behavior), regardless of body fields.
4. The `restart_counts[key] = 0` reset should happen when the server is reachable AND `restart_recommended=False`; this covers both HTTP 200 (healthy) and HTTP 503 + `restart_recommended=False` (degraded but not restartable).
5. The `health_registry.record_success(key)` call should only happen on clean HTTP 200 (truly healthy), not on reachable + degraded.

## Implementation

### Target file

`/home/masaos/llmagent/scripts/agent/repl_health.py`

### Procedure

1. Open `/home/masaos/llmagent/scripts/agent/repl_health.py`.
2. Locate `_watchdog_check_http()` (lines 289-343).
3. Replace the call and the simple `if ok:` branch with the new structured decision logic:

Current code (lines 306-344):
```python
ok = await probe_mcp_health(ctx.services_required.http, srv_cfg.url)
if ok:
    restart_counts[key] = 0
    if ctx.services_required.health_registry:
        ctx.services_required.health_registry.record_success(key)
    return
count = restart_counts.get(key, 0)
if count >= max_restarts:
    logger.warning(...)
    return
logger.warning(...)
# Delegate restart to lifecycle manager
if (
    srv_cfg.startup_mode == "subprocess"
    and ctx.services_required.lifecycle is not None
):
    try:
        await ctx.services_required.lifecycle.restart(key)
        restart_counts[key] = count + 1
    except (OSError, RuntimeError) as e:
        logger.error(...)
else:
    logger.warning(...)
if ctx.services_required.health_registry:
    ctx.services_required.health_registry.record_failure(key)
```

Replace with:
```python
probe = await _probe_mcp_health_detail(ctx.services_required.http, srv_cfg.url)

if probe.reachable and probe.status_code == HTTPStatus.OK:
    # Fully healthy
    restart_counts[key] = 0
    if ctx.services_required.health_registry:
        ctx.services_required.health_registry.record_success(key)
    return

if probe.reachable and not probe.restart_recommended:
    # Reachable but degraded; restart will not help
    restart_counts[key] = 0
    if probe.operator_action_required:
        logger.warning(
            "Watchdog: %r requires operator action — not restarting (operator_action_required=True)",
            key,
        )
    return

# Either unreachable (probe.reachable=False) or restart_recommended=True
count = restart_counts.get(key, 0)
if count >= max_restarts:
    logger.warning(
        "Watchdog: %r unreachable; restart limit reached (%s)",
        key,
        max_restarts,
    )
    return
logger.warning(
    "Watchdog: %r health check failed, restarting (attempt %s/%s)",
    key,
    count + 1,
    max_restarts,
)
# Delegate restart to lifecycle manager
if (
    srv_cfg.startup_mode == "subprocess"
    and ctx.services_required.lifecycle is not None
):
    try:
        await ctx.services_required.lifecycle.restart(key)
        restart_counts[key] = count + 1
    except (OSError, RuntimeError) as e:
        logger.error("Watchdog: failed to restart %r: %s", key, e)
else:
    logger.warning(
        "Watchdog: %r is not a subprocess-mode server;"
        " manual intervention required",
        key,
    )
if ctx.services_required.health_registry:
    ctx.services_required.health_registry.record_failure(key)
```

4. Update the docstring of `_watchdog_check_http()` to document the new restart gating logic:
   - `probe.reachable=False` or `probe.restart_recommended=True` → attempt restart if under limit
   - `probe.reachable=True` and `probe.restart_recommended=False` → no restart; log if `operator_action_required=True`

### Method

- `_probe_mcp_health_detail` is an `async def` — `await` is required.
- `HTTPStatus.OK` is already imported (line 11: `from http import HTTPStatus`).
- The three-branch structure follows the plan exactly:
  1. Fully healthy (200) → reset count, record success, return
  2. Reachable + not restart_recommended → reset count, log if operator action needed, return
  3. Unreachable or restart_recommended → attempt restart (existing logic unchanged)
- Keeping `restart_counts[key] = 0` in branch 2 means we don't accumulate stale restart counts for servers that are persistently degraded but non-restartable.

### Details

- Function signature stays unchanged: `async def _watchdog_check_http(ctx, key, srv_cfg, restart_counts, max_restarts) -> None`
- The `ctx.services_required.http is None` guard at lines 302-303 stays in place before the probe call.
- The `not srv_cfg.url` guard at lines 304-305 stays in place.
- Log message for operator action: `"Watchdog: %r requires operator action — not restarting (operator_action_required=True)"` uses `logger.warning` consistent with other watchdog log lines in this function.

## Validation plan

```bash
# Run test_repl_health to confirm probe_mcp_health still works
uv run pytest tests/test_repl_health.py -v

# After Step 7, also run:
uv run pytest tests/test_watchdog.py -v

# Type check
uv run mypy scripts/agent/repl_health.py

# Lint
uv run ruff check scripts/agent/repl_health.py
```

Expected outcomes:
- `test_repl_health.py` passes without regression.
- `_watchdog_check_http` unit tests in `test_watchdog.py` (Step 7) pass with the new logic.
- No new mypy or ruff errors.
