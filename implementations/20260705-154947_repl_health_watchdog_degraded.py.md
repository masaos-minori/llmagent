# Implementation: agent/repl_health.py — Call record_degraded() from _watchdog_check_http()

## Goal

When `_watchdog_check_http()` finds a reachable server with non-200 status and `restart_recommended=False`, call `record_degraded()` on the health registry.

## Scope

**In**: Update `_watchdog_check_http()` branch at line ~464.

**Out**: Changes to restart policy, `record_failure()` callers, or other watchdog functions.

## Assumptions

1. Branch at line ~464: `if probe.reachable and not probe.restart_recommended:` — currently resets `restart_counts[key] = 0` then returns.
2. `ctx.services_required.health_registry` may be `None` if not configured — must guard with `if`.
3. `probe.body` is a `dict | None` — the plan's design shows `probe.body.get("reason")`.
4. Reason is extracted from `probe.body.get("reason")` or `probe.body.get("message")`.
5. When `probe.reachable=True` and `probe.operator_action_required=True`, the existing warning log is already present — no change needed to that path.

## Implementation

### Target file
`scripts/agent/repl_health.py`

### Procedure
1. Locate `_watchdog_check_http()` branch for `probe.reachable and not probe.restart_recommended`.
2. Add `record_degraded()` call after resetting `restart_counts`.

### Method

**Updated branch (replaces lines ~464-468):**
```python
if probe.reachable and not probe.restart_recommended:
    restart_counts[key] = 0
    if probe.operator_action_required:
        logger.warning(
            "Watchdog: %r requires operator action: %s",
            key,
            probe.body,
        )
    if ctx.services_required.health_registry is not None:
        body: dict = probe.body or {}
        reason_raw = body.get("reason") or body.get("message")
        reason = str(reason_raw) if reason_raw is not None else None
        ctx.services_required.health_registry.record_degraded(key, reason=reason)
    return
```

### Details

- `probe.body or {}` guards against `None` body.
- `str(reason_raw)` handles non-string values in the body dict.
- `record_degraded()` call is guarded by `health_registry is not None` to avoid AttributeError in test stubs.
- Reachable + `restart_recommended=True` branch is unchanged — still triggers restart.
- Unreachable branch is unchanged — still calls `record_failure()`.

## Validation plan

- `uv run pytest tests/ -v -k "watchdog_degraded or health_degraded"` — all pass.
- Verify: `reachable=True, restart_recommended=False` → `record_degraded()` called.
- Verify: `reachable=True, restart_recommended=True` → restart attempted, no `record_degraded()`.
- Verify: `reachable=False` → `record_failure()` called, no `record_degraded()`.
- `mypy scripts/agent/repl_health.py` — no new errors.
- `ruff check scripts/agent/repl_health.py` — 0 errors.
