# Implementation: M-2/M-5/L-2 — docs/05_agent_07_cli-and-commands.md consolidated fixes

Source plans: `plans/20260709-100635_plan.md` (M-2, step 4 items 6-7,
expanded for L-2), `plans/20260709-101110_plan.md` (M-5, step 2),
`plans/20260709-102027_plan.md` (L-2, verification only).

## Goal

Replace the stale `[DEFER] - mcp/server2.auth_token` example with 3
restart-required examples, fix the `Skipped` row in the classification
summary table, and state that `/mcp` / `/mcp status` reflects running
config only, never pending `/reload` changes.

## Scope

**Target**: `docs/05_agent_07_cli-and-commands.md` — 3 edits:
1. Lines 98-99 (`/mcp` / `/mcp status` command table rows) — M-5.
2. Lines 246-259 (example `/reload` output block) — M-2/L-2.
3. Line 273 (classification summary table, `Skipped` row) — M-2.

## Assumptions

1. All 3 edit points were located by reading
   `docs/05_agent_07_cli-and-commands.md:90-280` in full while planning
   M-2/M-5 — no other section mentions MCP deferred/skip semantics.
2. `_MCP_SERVER_FIELDS` iteration order in
   `implementations/20260709-103709_config_reload.py.md` is
   `transport, url, startup_mode, ...` — the example output's field order
   in edit 2 below follows that same order (`url`, `startup_mode`,
   `auth_token`) for consistency with real rendered output, per the
   ordering risk noted in L-2's plan.

## Implementation

### Target file

`docs/05_agent_07_cli-and-commands.md`

### Procedure

#### Step 1: Fix the `/mcp` / `/mcp status` rows (M-5)

Current (lines 98-99):
```markdown
| `/mcp` | HTTP probe to all MCP servers | Displays health table |
| `/mcp status` | HTTP probe to all MCP servers | Displays health table |
```
→
```markdown
| `/mcp` | HTTP probe to all MCP servers | Displays health table (running config only) |
| `/mcp status` | HTTP probe to all MCP servers | Displays health table (running config only) |
```

Add a clarifying paragraph immediately after this command table (or at the
start of the "Hot-Reload Scope" section, whichever reads better in context):
```markdown
`/mcp` / `/mcp status` is a health view of the **currently running** MCP
server configuration — it is not a preview of pending `/reload` changes.
After `/reload` reports `[RESTART]` items, `/mcp` continues to show the
pre-reload servers, URLs, and auth state until the agent is actually
restarted.
```

#### Step 2: Replace the example `/reload` output (M-2/L-2)

Current (lines 246-259):
```
Config reloaded — some changes require restart
WARNING: Some settings require restart to take effect.
Restart required: [1 items]
  [RESTART] - server1
Applied (runtime): [3 items]
  [OK] - llm
  [OK] - hist_mgr
  [OK] - tools
Deferred (next connection): [1 items]
  [DEFER] - mcp/server2.auth_token
Startup-only (ignored): [1 items]
  [STARTUP-ONLY] - use_memory_layer
```
→
```
Config reloaded — some changes require restart
WARNING: Some settings require restart to take effect.
Restart required: [4 items]
  [RESTART] - server1
  [RESTART] - mcp/server.url
  [RESTART] - mcp/server.startup_mode
  [RESTART] - mcp/server2.auth_token
Applied (runtime): [3 items]
  [OK] - llm
  [OK] - hist_mgr
  [OK] - tools
Startup-only (ignored): [1 items]
  [STARTUP-ONLY] - use_memory_layer
```
(The `Deferred (next connection)` block is removed entirely — no field
produces `[DEFER]` after this batch.)

#### Step 3: Fix the `Skipped` row (M-2)

Current (line 273):
```markdown
| Skipped | `[SKIP]` | New MCP server — restart required |
```
→
```markdown
| Skipped | `[SKIP]` | Changes intentionally ignored, not MCP server definitions — see Restart-required |
```

### Method

- Apply all 3 steps in one pass — Steps 2 and 3 both touch the same
  "Hot-Reload Scope" section and are easiest to review together.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No deferred MCP example | `grep -n "\[DEFER\] - mcp" docs/05_agent_07_cli-and-commands.md` | no matches |
| Restart-required examples present | `grep -n "\[RESTART\] - mcp" docs/05_agent_07_cli-and-commands.md` | ≥ 3 matches |
| `/mcp` running-config note present | `grep -n "running config only\|not a preview of pending" docs/05_agent_07_cli-and-commands.md` | ≥ 1 match |
| Skipped row fixed | `grep -n "New MCP server — restart required" docs/05_agent_07_cli-and-commands.md` | no matches |
| MCP docs consistency | `uv run check-mcp-docs` | pass |
