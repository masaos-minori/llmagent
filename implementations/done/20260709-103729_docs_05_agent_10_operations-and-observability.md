# Implementation: L-3 — docs/05_agent_10_operations-and-observability.md MCP restart notes

Source plan: `plans/20260709-102157_plan.md` (L-3, Implementation steps 1-2).

## Goal

Fix a troubleshooting row that misleadingly suggests `/reload` as a remedy
for an unavailable MCP server, and add an operations note distinguishing
`/reload`, watchdog restart, and full agent restart for MCP server
definitions.

## Scope

**Target**: `docs/05_agent_10_operations-and-observability.md` — 2 edits:
1. Troubleshooting table row, line 476.
2. New note after the existing `workflow_mode` note, line 405.

## Assumptions

1. Line 476 currently reads
   `| \`/mcp\` shows UNAVAILABLE server | Health registry marked server unavailable | Restart the MCP server; \`/reload\` |`
   — listing `/reload` as a possible remedy is misleading after this batch
   (verified while planning L-3).
2. Lines 404-405 already contain a precedent note pattern
   (`**Note:** \`workflow_mode\` is a startup-only setting — it cannot be
   changed via \`/reload\`. Any change requires a full agent restart.`) that
   the new MCP note follows stylistically.

## Implementation

### Target file

`docs/05_agent_10_operations-and-observability.md`

### Procedure

#### Step 1: Fix the troubleshooting row (line 476)

Current:
```markdown
| `/mcp` shows UNAVAILABLE server | Health registry marked server unavailable | Restart the MCP server; `/reload` |
```
→
```markdown
| `/mcp` shows UNAVAILABLE server | Health registry marked server unavailable | Check watchdog logs for auto-restart attempts; if the server *definition* (URL, auth, transport, etc.) changed, a full agent restart is required — `/reload` does not apply MCP config changes |
```

#### Step 2: Add the operations note (after line 405)

Current context (lines 404-406):
```markdown
**Note:** `workflow_mode` is a startup-only setting — it cannot be changed via `/reload`.
Any change requires a full agent restart.

---
```

Insert before the `---`:
```markdown
**Note:** MCP server definitions (`transport`, `url`, `startup_mode`,
`healthcheck_mode`, `call_timeout_sec`, `startup_timeout_sec`, `tool_names`,
`auth_token`, `role`, `cmd`, `env`) are restart-time snapshots. `/reload`
detects changes to `[mcp_servers.*]` and reports them as restart-required
(`[RESTART] - mcp/<server>.<field>`), but never applies them to the running
process. `/mcp` / `/mcp status` always reflects the running (pre-restart)
server config, not pending `/reload` changes. Watchdog-triggered restarts
(`watchdog_loop()`) restart a failed subprocess using its *current* startup
config — this is health-driven recovery, not config reload, and does not
apply pending MCP server definition changes either. Only a full agent
restart applies a changed MCP server definition.
```

### Method

- Two independent edits in the same file; apply in either order.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Troubleshooting row fixed | `grep -n "Restart the MCP server; \`/reload\`" docs/05_agent_10_operations-and-observability.md` | no matches |
| New note present | `grep -n "restart-time snapshots" docs/05_agent_10_operations-and-observability.md` | ≥ 1 match |
| MCP docs consistency | `uv run check-mcp-docs` | pass |
