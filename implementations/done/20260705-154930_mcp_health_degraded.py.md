# Implementation: shared/mcp_health.py — Add record_degraded() to McpServerHealthRegistry

## Goal

Add `record_degraded()` and `get_degraded_reason()` to `McpServerHealthRegistry`, and update `record_success()` to clear degraded state.

## Scope

**In**: `McpServerHealthRegistry.__init__`, `record_degraded()`, `get_degraded_reason()`, `record_success()`.

**Out**: Changes to `record_failure()`, `is_unavailable()`, or watchdog callers.

## Assumptions

1. `McpServerHealthState.DEGRADED` enum value exists at `shared/mcp_health.py`.
2. `McpServerHealthRegistry.__init__` currently does NOT have `_degraded_reasons` dict.
3. `record_success()` currently restores `_states[server_key] = McpServerHealthState.HEALTHY`.
4. `is_unavailable()` checks only for `McpServerHealthState.UNAVAILABLE` — must NOT include `DEGRADED`.

## Implementation

### Target file
`scripts/shared/mcp_health.py`

### Procedure
1. Add `self._degraded_reasons: dict[str, str] = {}` to `__init__`.
2. Add `record_degraded()` method.
3. Add `get_degraded_reason()` method.
4. Update `record_success()` to clear degraded reason.

### Method

**Updated `__init__`:**
```python
def __init__(self) -> None:
    self._states: dict[str, McpServerHealthState] = {}
    self._failure_counts: dict[str, int] = {}
    self._degraded_reasons: dict[str, str] = {}
```

**New `record_degraded()`:**
```python
def record_degraded(self, server_key: str, reason: str | None = None) -> None:
    """Record a reachable-but-degraded server without triggering UNAVAILABLE."""
    self._states[server_key] = McpServerHealthState.DEGRADED
    if reason is not None:
        self._degraded_reasons[server_key] = reason
    logger.warning("Health: %r is DEGRADED (reason=%s)", server_key, reason or "unknown")
```

**New `get_degraded_reason()`:**
```python
def get_degraded_reason(self, server_key: str) -> str | None:
    return self._degraded_reasons.get(server_key)
```

**Updated `record_success()`:**
```python
def record_success(self, server_key: str) -> None:
    if self._states.get(server_key) != McpServerHealthState.HEALTHY:
        logger.info("Health: %r recovered to HEALTHY", server_key)
    self._states[server_key] = McpServerHealthState.HEALTHY
    self._failure_counts.pop(server_key, None)
    self._degraded_reasons.pop(server_key, None)  # NEW
```

### Details

- `DEGRADED` state is informational only — `is_unavailable()` must remain unchanged (returns True only for UNAVAILABLE).
- `record_degraded()` is idempotent: multiple calls overwrite with latest reason.
- `reason` is cast to `str` by callers before passing; this method accepts `str | None`.

## Validation plan

- `uv run pytest tests/ -v -k "mcp_health"` — all pass.
- Verify: `record_degraded()` sets state to `DEGRADED`.
- Verify: `record_success()` after degraded → HEALTHY, reason cleared.
- Verify: `is_unavailable()` returns `False` for DEGRADED servers.
- `mypy scripts/shared/mcp_health.py` — no new errors.
- `ruff check scripts/shared/mcp_health.py` — 0 errors.
