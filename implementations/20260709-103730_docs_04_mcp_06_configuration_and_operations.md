# Implementation: L-3 — docs/04_mcp_06_configuration_and_operations.md reload vs restart note

Source plan: `plans/20260709-102157_plan.md` (L-3, Implementation step 3).

## Goal

Add the missing distinction between `/reload`, watchdog restart, and full
agent restart to the MCP operations doc, which currently never mentions
`/reload` at all.

## Scope

**Target**: `docs/04_mcp_06_configuration_and_operations.md`, after line 32
(the `mcp_watchdog_max_restarts` row).

## Assumptions

1. This file contains zero occurrences of `/reload` — verified by
   `grep -c "reload" docs/04_mcp_06_configuration_and_operations.md` → `0`
   while planning L-3. It documents watchdog restart behavior extensively
   (lines 31-32, 538-568) but never relates it to config reload.

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`

### Procedure

#### Step 1: Insert the note after line 32

Current context (lines 28-32):
```markdown
| `config/agent.toml` → `[mcp_servers.*]` | All server transport settings (`McpServerConfig`) — エージェントが MCP サーバーへの接続を管理するために使用 |
...
| `config/agent.toml` → `mcp_watchdog_interval` | Watchdog poll interval (0 = disabled) |
| `config/agent.toml` → `mcp_watchdog_max_restarts` | Watchdog max restart count |
```

Insert immediately after:
```markdown

**Reload vs. restart:** `/reload` never modifies `[mcp_servers.*]` at
runtime — MCP server definition changes (URL, auth token, startup mode,
transport, command, environment) are always reported as restart-required
and require a full agent restart to take effect. The watchdog
(`mcp_watchdog_interval`, `mcp_watchdog_max_restarts` above) restarts a
*failed* subprocess using its existing startup config; it does not read or
apply any pending `/reload` config change. See
[Agent Operations: MCP restart requirement](05_agent_10_operations-and-observability.md)
for the full explanation.
```

### Method

- One paragraph insertion; no existing content modified.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Note present | `grep -n "Reload vs. restart" docs/04_mcp_06_configuration_and_operations.md` | 1 match |
| MCP docs consistency | `uv run check-mcp-docs` | pass |
