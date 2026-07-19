---
title: "MCP Watchdog — Removed (2026-07-16)"
category: mcp
tags:
  - mcp
  - watchdog
  - removed-feature
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_02_02_startup-modes-and-health.md
  - 04_mcp_06_02_configuration-file-inventory.md
  - 04_mcp_06_09_mcp-failure-diagnosis.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# MCP Watchdog — Removed (2026-07-16)

The MCP watchdog (a background asyncio task that periodically probed every
HTTP MCP server's `/health` endpoint and automatically restarted
subprocess-mode servers on failure) was removed on 2026-07-16. See
`requires/done/20260716_20_require.md` for the removal requirement.

Removed with it:

- `watchdog_loop()` および関連ヘルパー関数
  (`agent/repl_health.py`)
- ウォッチドッグループおよび起動/停止関数
  (`agent/repl.py`)
- `McpServerHealthRegistry.record_restart_exhausted()`
  (`shared/mcp_health.py`)
- The `mcp_watchdog_interval` / `mcp_watchdog_max_restarts` config keys
  (`MCPConfig`, `config/agent.toml`, `/reload` diff-apply)
- The `Watchdog` line in `/config` and `/mcp status` output

**Not affected** — these are independent of the watchdog and remain in
place unchanged:

- The `/health` endpoint itself and its response fields
  (`restart_recommended`, `operator_action_required`, `dependencies`, ...)
- `McpServerHealthRegistry`'s state machine
  (`HEALTHY`/`DEGRADED`/`UNAVAILABLE`/`HALF_OPEN`) and its
  `record_success()` / `record_failure()` methods — these are driven by
  the `ToolExecutor` transport-error path on every real tool dispatch,
  not by the watchdog

**Now dead code as a side effect of this removal** — kept in place
per this change's scope (no production-code deletion beyond the watchdog
itself), but no longer reachable:

- `McpServerHealthRegistry.record_degraded()` — `_watchdog_check_http()`
  was its only caller; nothing else in `scripts/` calls it after this
  removal
- `get_degraded_reason()` (`cmd_mcp.py`'s `/mcp status` display) — still
  called, but since `record_degraded()` is never invoked, it will always
  return `None` going forward
- `McpStatusService.probe_all()` and the `/mcp status` command — still
  probe every server's `/health` on demand and display the result

## Manual recovery (replaces the automatic restart loop)

Because the watchdog is gone, there is no longer any background process
that notices a crashed MCP server and restarts it. The only remaining
recovery paths are:

1. **On the next tool call** — for `startup_mode="subprocess"` servers,
   `ensure_ready()` (`agent/factory.py`, invoked from
   `ToolExecutor._raw_execute()`) still attempts to start the process if
   it is not running. This is reactive (triggered by the next tool call
   to that server), not periodic.
2. **Manual process restart** — if a subprocess-mode server keeps
   crashing, or an externally-managed (`startup_mode="persistent"`)
   server goes down, an operator must restart it directly (e.g. via the
   process supervisor managing that server) or restart the agent process
   itself so MCP server startup runs again. There is no `/mcp restart`
   slash command; `/mcp status` is read-only and only reports state, it
   does not trigger a restart.

Use `/mcp status` to check current DEGRADED/UNAVAILABLE state and
`health_reason` before deciding whether a manual restart is needed — see
[04_mcp_06_09_mcp-failure-diagnosis.md](04_mcp_06_09_mcp-failure-diagnosis.md).

## Related Documents

- [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md)
- [04_mcp_02_02_startup-modes-and-health.md](04_mcp_02_02_startup-modes-and-health.md)
- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)
- [04_mcp_06_09_mcp-failure-diagnosis.md](04_mcp_06_09_mcp-failure-diagnosis.md)

## Keywords

watchdog
removed
manual recovery
ensure_ready
mcp status
