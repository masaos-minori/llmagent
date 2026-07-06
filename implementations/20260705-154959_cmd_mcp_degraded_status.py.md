# Implementation: agent/commands/cmd_mcp.py — Expose degraded state in /mcp status

## Goal

Show DEGRADED servers and their reasons in `/mcp status` output, alongside existing status display.

## Scope

**In**: Update the status display section of `cmd_mcp.py` to read degraded state from `McpServerHealthRegistry`.

**Out**: Changes to restart logic, health registry implementation, or other commands.

## Assumptions

1. `/mcp status` command is implemented in `scripts/agent/commands/cmd_mcp.py`.
2. The status output iterates over `ctx.cfg.mcp.mcp_servers` and shows each server's health state.
3. `ctx.services_required.health_registry` provides access to `McpServerHealthRegistry`.
4. `McpServerHealthRegistry.get_state(server_key)` returns current `McpServerHealthState`.
5. `McpServerHealthRegistry.get_degraded_reason(server_key)` returns `str | None` — new method from Plan 14 Phase 1.
6. Output format should show: `[DEGRADED] <server_key>: <reason>` for degraded servers.

## Implementation

### Target file
`scripts/agent/commands/cmd_mcp.py`

### Procedure
1. Locate the status rendering loop in the status handler.
2. After checking `HEALTHY`/`UNAVAILABLE` states, add a branch for `DEGRADED`.
3. Call `get_degraded_reason()` to include reason in output.

### Method

**Status output section (after existing HEALTHY/UNAVAILABLE display):**
```python
from shared.mcp_health import McpServerHealthState

for key, server_cfg in ctx.cfg.mcp.mcp_servers.items():
    registry = ctx.services_required.health_registry
    state = registry.get_state(key) if registry else None

    if state == McpServerHealthState.UNAVAILABLE:
        view.write_line(f"  [UNAVAILABLE] {key}")
    elif state == McpServerHealthState.DEGRADED:
        reason = registry.get_degraded_reason(key)
        reason_str = f": {reason}" if reason else ""
        view.write_line(f"  [DEGRADED] {key}{reason_str}")
    else:
        # HEALTHY or None (unknown)
        status_label = "HEALTHY" if state == McpServerHealthState.HEALTHY else "UNKNOWN"
        view.write_line(f"  [{status_label}] {key}")
```

### Details

- `registry` guard (`if registry`) ensures this works in environments where health registry is disabled.
- Reason is appended as `: <reason>` when present, omitted when `None`.
- No change to existing UNAVAILABLE display logic — DEGRADED is a new branch.

## Validation plan

- `uv run pytest tests/ -v -k "cmd_mcp or mcp_status"` — all pass.
- Verify: degraded server appears as `[DEGRADED] srv: reason` in status output.
- Verify: healthy server still appears as `[HEALTHY]`.
- Verify: `health_registry=None` → shows `[UNKNOWN]` without error.
- `mypy scripts/agent/commands/cmd_mcp.py` — no new errors.
- `ruff check scripts/agent/commands/cmd_mcp.py` — 0 errors.
