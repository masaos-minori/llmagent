# Implementation Doc: `record_restart_exhausted()` on `McpServerHealthRegistry`

## Goal

Give the watchdog a way to record that it has exhausted its restart attempts for
an MCP server, so operators can distinguish "still cycling through restarts"
from "watchdog gave up; needs manual intervention" via `/mcp` status — without
touching the server's health state (`_states`).

## Scope

**In scope:**
- Add a new public method `record_restart_exhausted(server_key: str) -> None` to
  `McpServerHealthRegistry` in `scripts/shared/mcp_health.py`.

**Out of scope:**
- `record_degraded()`'s `UNAVAILABLE`/`HALF_OPEN` guard (sibling plan
  `plans/20260711-134244_plan.md` — coordinate/land first per plan Assumption 6).
- Any change to `_states`, `record_failure()`, or `record_success()`.
- Callers of this method (covered by the Phase 2 doc for `repl_health.py`).

## Assumptions

- `_degraded_reasons` is a plain, state-independent `dict[str, str]` field on
  `McpServerHealthRegistry` (confirmed by plan Assumption 5) — writing to it
  directly requires no change to `get_degraded_reason()`.
- The server is expected to already be `UNAVAILABLE` by the time restart
  attempts are exhausted (prior `record_failure()` calls from preceding restart
  attempts have almost always already crossed `failure_threshold`) — so this
  method deliberately does **not** call `record_failure()` and does **not**
  gate on current state (plan Assumption 3).
- This method must land after (or together with, coordinated) the sibling
  plan's `record_degraded()` guard change, since both touch the same file
  (plan Assumption 6).

## Implementation

### Target file

`scripts/shared/mcp_health.py`

### Procedure

1. Locate the `McpServerHealthRegistry` class definition and its existing
   methods (`record_failure`, `record_success`, `record_degraded`,
   `get_degraded_reason`, `get_state`) to place the new method in a
   consistent location (near `record_degraded()`).
2. Add the new method with the signature and docstring below.
3. Confirm `logger` is already defined at module scope (it is used elsewhere
   in this file); reuse it — do not create a new logger instance.

### Method

```python
def record_restart_exhausted(self, server_key: str) -> None:
    """Record that the watchdog exhausted its restart attempts for server_key.

    Does not change state (the server is expected to already be UNAVAILABLE
    from the record_failure() calls made during the preceding restart
    attempts) — only tags the reason so operators can distinguish "still
    cycling" from "watchdog gave up; needs manual intervention" in /mcp
    status.
    """
    self._degraded_reasons[server_key] = "restart_limit_reached"
    logger.warning(
        "Health: %r restart limit reached — manual intervention required", server_key
    )
```

### Details

- Do **not** call `record_failure(server_key)` from within this method (plan
  Assumption 3 — would grow an already-saturated failure counter with no new
  information).
- Do **not** gate this write on `get_state(server_key)` — unlike
  `record_degraded()`, this method always overwrites `_degraded_reasons`
  unconditionally when called, since it represents a more operationally
  relevant signal than any prior reason (plan Risks table, row 1: accepted).
  The `record_degraded()` guard is being tracked and implemented by the
  sibling plan; do not add similar guard logic here.
- Keep the log level at `warning` (matches existing style for
  operator-actionable conditions elsewhere in this file).
- Type signature: `server_key: str`, return type `None` — matches the style
  of sibling methods (`record_failure`, `record_success`).
- Do not add a new import; `logger` and `self._degraded_reasons` are already
  available in the class.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/mcp_health.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/mcp_health.py` | No new errors |
| Manual | `uv run python -c "..."` — build a registry, call `record_restart_exhausted`, confirm `get_state()` unchanged and `get_degraded_reason()` returns `"restart_limit_reached"` | Matches Design |
| Tests | `uv run pytest tests/test_mcp_health_degraded.py -v` | All pass (no regression from adding this method) |
