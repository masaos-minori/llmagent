## Goal

Make `record_degraded()` on `McpServerHealthRegistry` (in `scripts/shared/mcp_health.py`) refuse to
overwrite `UNAVAILABLE` or `HALF_OPEN` state, so a periodic "reachable but degraded" watchdog probe
can never silently clear the circuit-breaker state that dispatch gating (`is_unavailable()`) and the
single-trial `HALF_OPEN` window depend on. Also expand the docstrings of `record_degraded()`,
`record_success()`, and `is_unavailable()` to explicitly document this guard and the state-mutating
side effect of `is_unavailable()`.

## Scope

**In scope:**
- `scripts/shared/mcp_health.py`: add a state guard at the top of `record_degraded()` that no-ops
  (with a debug log) when the current state is `UNAVAILABLE` or `HALF_OPEN`.
- Expand docstrings for `record_degraded()`, `record_success()`, `is_unavailable()`.

**Out of scope:**
- `record_failure()` logic/thresholds/cooldown constants — unchanged.
- `ToolExecutor` / `HttpTransport` retry logic — unchanged.
- Watchdog probe parsing (`_watchdog_check_http()`) — unchanged, handled separately.
- Any test or doc file — covered by separate implementation docs (Phase 2 and Phase 3).

## Assumptions

1. `record_degraded()` is called only from `agent/repl_health.py::_watchdog_check_http()`
   (reachable-but-not-restart-recommended branch); no other caller exists today.
2. Dispatch gating is enforced exclusively via `is_unavailable()`
   (`shared/tool_executor.py:229`, `shared/tool_transport_invoker.py:123`). `DEGRADED` does not
   block dispatch; only `UNAVAILABLE` does.
3. `record_degraded()` must NOT be allowed to overwrite `UNAVAILABLE`: doing so would let a
   watchdog "degraded but reachable" probe silently reset a circuit-broken server back to
   `DEGRADED`, making `is_unavailable()` return `False` and routing dispatch to a server the
   breaker just opened against — a direct violation of the requirement's acceptance criteria.
4. `HALF_OPEN` must receive the same guard as `UNAVAILABLE` (generalization beyond the literal
   requirement wording): `HALF_OPEN` is a single-trial dispatch window consumed once by
   `is_unavailable()`'s callers; a watchdog probe landing mid-window must not downgrade it to
   `DEGRADED` (which does not gate dispatch), or the single-trial semantics break the same way.
5. `record_failure()`, `is_unavailable()`, and `get_state()` keep their current logic; only
   docstrings change for `record_success()` and `is_unavailable()`.
6. Suppressing the `DEGRADED` transition while `UNAVAILABLE`/`HALF_OPEN` (rather than still
   recording the reason for operator visibility) is accepted: no degraded-reason UI path exists
   for `UNAVAILABLE` today, so no regression in operator visibility.

## Implementation

### Target file

`scripts/shared/mcp_health.py`

### Procedure

1. Locate `record_degraded()` on `McpServerHealthRegistry`.
2. At the top of the method body, read the current state via `self.get_state(server_key)`.
3. If the current state is `McpServerHealthState.UNAVAILABLE` or `McpServerHealthState.HALF_OPEN`,
   log at `debug` level that the degraded probe was ignored (include `server_key` and the current
   state value) and return without mutating `_states` or `_degraded_reasons`.
4. Otherwise, keep the existing behavior unchanged: set `_states[server_key] = DEGRADED`, set
   `_degraded_reasons[server_key] = reason` if `reason is not None`, and log a `warning`.
5. Expand the docstring of `record_degraded()` to state explicitly that it will not downgrade
   `UNAVAILABLE` or `HALF_OPEN`, and why (circuit-breaker/dispatch-gating preservation).
6. Expand the docstring of `record_success()` to state it clears `_failure_counts` and
   `_unavailable_since`/cooldown bookkeeping in addition to setting `HEALTHY`, so a later
   `record_failure()` does not jump straight back to `UNAVAILABLE`.
7. Expand the docstring of `is_unavailable()` to explicitly call out that it is not a pure getter:
   it has the side effect of transitioning `UNAVAILABLE` to `HALF_OPEN` once the cooldown has
   elapsed.

### Method

Guard clause pattern (illustrative signature/pseudocode only, per python-design skill rules —
do not treat as final production code):

```python
def record_degraded(self, server_key: str, reason: str | None = None) -> None:
    """... expanded docstring per Procedure step 5 ..."""
    current = self.get_state(server_key)
    if current in (McpServerHealthState.UNAVAILABLE, McpServerHealthState.HALF_OPEN):
        logger.debug("... ignored degraded probe, current=%s ...", current.value)
        return
    # existing DEGRADED-setting logic unchanged
    ...
```

### Details

- No new imports, no new module, no config key, no DB schema change.
- `record_degraded()`'s public signature and return type (`None`) do not change — callers in
  `agent/repl_health.py` are unaffected.
- Keep the guard check as the very first statement in the method body so the no-op path is cheap
  and easy to see in a diff.
- Use the existing `logger` instance already defined in `scripts/shared/mcp_health.py`; do not
  introduce a new logger.
- English-only log messages and docstrings per `rules/coding.md`.

## Validation plan

Checks from the plan's Validation plan table that are relevant to this target file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/mcp_health.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/mcp_health.py` | No new errors (baseline: 0 today) |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Security | `uv run bandit -r scripts/shared/mcp_health.py -c pyproject.toml` | 0 findings (baseline: 0 today) |
| Coverage | `uv run coverage run -m pytest tests/test_mcp_health_degraded.py && uv run coverage report --include="*/mcp_health.py"` | New guard branch covered by Phase 2's tests |
