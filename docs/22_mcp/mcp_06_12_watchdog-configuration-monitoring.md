---
title: "MCP Watchdog — Removed (2026-07-16)"
area: mcp
tags:
  - mcp
  - watchdog
  - monitoring
related:
  - mcp_00_document-guide.md
  - mcp_02_02_startup-modes-and-health.md
  - mcp_06_02_configuration-file-inventory.md
  - mcp_06_09_mcp-failure-diagnosis.md
---
# MCP Watchdog — Removed (2026-07-16)

The MCP watchdog (a background asyncio task that periodically probed every
HTTP MCP server's `/health` endpoint and automatically restarted
subprocess-mode servers on failure) was removed on 2026-07-16. See
`requires/done/20260716_20_require.md` for the removal requirement.

Removed with it:

- `watchdog_loop()` and related helper functions (`agent/repl_health.py`) — removed
- watchdog loop and start/stop functions (`agent/repl.py`)
- `McpServerHealthRegistry.record_restart_exhausted()` (`shared/mcp_health.py`) — removed
- The `mcp_watchdog_interval` / `mcp_watchdog_max_restarts` config keys (`MCPConfig`, `config/agent.toml`, `/reload` diff-apply)
- The `Watchdog` line in `/config` and `/mcp status` output

**Not affected** — these are independent of the watchdog and remain in
place unchanged:

- The `/health` endpoint itself and its response fields (`restart_recommended`, `operator_action_required`, `dependencies`, ...)
- `McpServerHealthRegistry`'s state machine (`HEALTHY`/`DEGRADED`/`UNAVAILABLE`/`HALF_OPEN`) and its `record_success()` / `record_failure()` methods — these are driven by the `ToolExecutor` transport-error path on every real tool dispatch, not by the watchdog

**Dead code left by this removal — since deleted:** `McpServerHealthRegistry.record_degraded()` (its only caller was `_watchdog_check_http()`) and `get_degraded_reason()` (read by the `/mcp status` display) were removed on 2026-08-20 together with the rest of the degraded-reason bookkeeping, so the registry no longer stores or reports a degraded reason.

**Still in place:**

- `McpStatusService.probe_all()` and the `/mcp status` command — still probe every server's `/health` on demand and display the result

## Manual recovery (replaces the automatic restart loop)

Because the watchdog is gone, there is no longer any background process
that notices a crashed MCP server and restarts it. The only remaining
recovery paths are:

1. **On the next tool call** — for `startup_mode="subprocess"` servers, `ensure_ready()` (`agent/factory.py`, invoked from `ToolExecutor._raw_execute()`) still attempts to start the process if it is not running. This is reactive (triggered by the next tool call to that server), not periodic.
2. **Manual process restart** — if a subprocess-mode server keeps crashing, or an externally-managed (`startup_mode="persistent"`) server goes down, an operator must restart it directly (e.g. via the process supervisor managing that server) or restart the agent process itself so MCP server startup runs again. There is no `/mcp restart` slash command; `/mcp status` is read-only and only reports state, it does not trigger a restart.

Use `/mcp status` to check current DEGRADED/UNAVAILABLE state and `health_reason` before deciding whether a manual restart is needed — see [mcp_06_09_mcp-failure-diagnosis.md](mcp_06_09_mcp-failure-diagnosis.md).

## Keywords

watchdog
removed
manual recovery
ensure_ready
mcp status
