# Implementation: H-10/M-2/L-1 — docs/05_agent_08_configuration.md consolidated fixes

Source plans: `plans/20260709-100244_plan.md` (H-10, step 6),
`plans/20260709-100635_plan.md` (M-2, step 4, items 1-5, expanded for L-1's
concrete examples), `plans/20260709-101720_plan.md` (L-1, verification only).

## Goal

Remove the `github_server_url` config row, replace every "hot-reloadable" /
"deferred" claim about MCP URL/auth_token/startup_mode with
"restart-required" (with concrete `mcp/<server>.<field>` examples), and fix
the `skipped` field's stale example.

## Scope

**Target**: `docs/05_agent_08_configuration.md`, 5 distinct edits within
lines 60-128 (the "Config file ownership and hot-reload eligibility"
section and the `ConfigReloadOutcome` fields table).

This consolidates 3 plans because they all edit overlapping line ranges in
the same section; applying them independently in plan order would produce
conflicting diffs on the same lines.

## Assumptions

1. All 5 edit points were located by reading
   `docs/05_agent_08_configuration.md:40-134` in full while planning M-2 —
   no other section of this file mentions MCP hot-reload/deferred/
   `github_server_url` (confirmed by the grep sweep in L-1's plan).

## Implementation

### Target file

`docs/05_agent_08_configuration.md`

### Procedure

#### Step 1: Fix the `config/security.toml` row (line 70)

Current:
```markdown
| `config/security.toml` | Approval and security defaults | Hot-reloadable (most); `auth_token`, `startup_mode` per server are deferred |
```
→
```markdown
| `config/security.toml` | Approval and security defaults | Hot-reloadable (most); `auth_token`, `startup_mode` per server are restart-required |
```

#### Step 2: Rewrite the `config/*_mcp_server.toml` row (line 72)

Current:
```markdown
| `config/*_mcp_server.toml` | MCP server transport/URL config (via `[mcp_servers.<key>]`) | HTTP URL: hot-reloadable; `auth_token`, `startup_mode`: deferred; new servers / transport change: restart-required |
```
→
```markdown
| `config/*_mcp_server.toml` | MCP server transport/URL config (via `[mcp_servers.<key>]`) | Restart-required: every field (`transport`, `url`, `startup_mode`, `healthcheck_mode`, `call_timeout_sec`, `startup_timeout_sec`, `tool_names`, `auth_token`, `role`, `cmd`, `env`), plus server add/remove/rename |
```
Remove the `github_server_url` row entirely if a separate row for it exists
elsewhere in this table (verify with
`grep -n "github_server_url" docs/05_agent_08_configuration.md` — if the
match is this same table, fold the removal into this step).

#### Step 3: Fix the classification definitions prose (lines 78-85)

No change needed to the "Hot-reloadable" / "Deferred" / "Restart-required" /
"Startup-only" definitions themselves (they remain valid generic
categories) — only the examples that follow (Steps 4-5) need to change.

#### Step 4: Fix the **Deferred settings** and **Restart-required settings** lists (lines 87-92)

Current:
```markdown
**Deferred settings** (`deferred` in `ConfigReloadOutcome`):
- `auth_token` per MCP server (stored in cfg; takes effect on next connection)
- `startup_mode` per MCP server (stored in cfg; takes effect on next subprocess start)

**Restart-required settings** (`needs_restart` in `ConfigReloadOutcome`):
- New MCP servers added to `*_mcp_server.toml`
```
→
```markdown
**Deferred settings** (`deferred` in `ConfigReloadOutcome`):
- None currently. (No field is deferred as of this writing — see
  [MCP known issues: BUG-01](04_mcp_90_inconsistencies_and_known_issues.md)
  while the restart-required migration is in progress.)

**Restart-required settings** (`needs_restart` in `ConfigReloadOutcome`):
- Any `McpServerConfig` field change, new servers, removed servers, and
  renames (remove-old + add-new). Example entries:
  `mcp/<server>.url`, `mcp/<server>.auth_token`, `mcp/<server>.startup_mode`,
  `mcp/<server>.cmd`, `mcp/<server>.env`.
```

#### Step 5: Fix the `skipped` field table row (line 126)

Current:
```markdown
| `skipped` | `list[str]` | Changes skipped (e.g. new MCP server added) |
```
→
```markdown
| `skipped` | `list[str]` | Changes intentionally ignored, not MCP server definitions — see `needs_restart` |
```

#### Step 6: Remove the `github_server_url` reference (H-10)

Confirm via `grep -n "github_server_url" docs/05_agent_08_configuration.md`
whether the removal is already covered by Step 2 (if it was a value in the
same table row) or is a separate row/mention elsewhere in the file; delete
whichever remains. Confirm `mcp_servers.github.url` is named somewhere in
this file as the canonical GitHub MCP endpoint — add one sentence if not
already present, e.g. under Step 2's row or as a footnote.

### Method

- Apply all 6 steps in one pass since they're all in the same file and
  several are adjacent/overlapping line ranges — doing them as separate
  commits risks an inconsistent intermediate state (e.g. Step 4's "None
  currently" claim would be false until Steps 1-2 also land).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No stale hot-reload/deferred wording | `grep -n "hot-reloadable" docs/05_agent_08_configuration.md \| grep -i "mcp\|auth_token\|startup_mode"` | no matches |
| No stale deferred wording | `grep -n "deferred" docs/05_agent_08_configuration.md \| grep -iE "auth_token\|startup_mode"` | no matches |
| github_server_url removed | `grep -n "github_server_url" docs/05_agent_08_configuration.md` | no matches |
| Canonical endpoint documented | `grep -n "mcp_servers.github.url" docs/05_agent_08_configuration.md` | ≥ 1 match |
| Restart-required examples present | `grep -n "mcp/<server>\." docs/05_agent_08_configuration.md` | ≥ 5 matches |
| MCP docs consistency | `uv run check-mcp-docs` | pass |
