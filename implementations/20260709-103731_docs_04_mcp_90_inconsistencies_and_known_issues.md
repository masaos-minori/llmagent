# Implementation: L-4 — docs/04_mcp_90_inconsistencies_and_known_issues.md BUG-01 entry

Source plan: `plans/20260709-102404_plan.md` (L-4, Implementation step 1).

## Goal

Replace the "no active issues" placeholder with a tracked entry describing
the current MCP reload mutation bug and the approved fix, so this file no
longer falsely claims nothing is unresolved while H-1..L-3 are pending.

## Scope

**Target**: `docs/04_mcp_90_inconsistencies_and_known_issues.md`, lines
18-21 (the entire "Active Issues" section).

**Note**: this doc should be implemented *before* or *alongside* the code
changes it references (H-1..L-3), not after — its purpose is to track the
gap while it exists. If this doc is implemented last (after H-1..L-3's code
already landed), skip it and instead go straight to marking it Resolved, or
omit entirely if the docs it cross-references have already been fixed by
then.

## Assumptions

1. Line 20 currently reads `*(現在アクティブな問題はありません)*` — verified
   by reading the file while planning L-4.
2. This file has no existing ID prefix convention (zero entries) — this doc
   introduces `BUG-01` as the first.

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure

#### Step 1: Replace the placeholder

Current:
```markdown
## Active Issues

*(現在アクティブな問題はありません)*

---
```

Replace with:
```markdown
## Active Issues

### BUG-01: MCP reload mutates running config; restart-required fix approved but not yet implemented

- **Type:** Implementation bug
- **Impact scope:** `agent/services/config_reload.py`, `agent/config_dataclasses.py`,
  `agent/config_builders.py`, `agent/commands/cmd_config_display.py`, plus
  related docs and tests.
- **Statement A:** The current implementation applies MCP HTTP URL changes
  at runtime via `/reload` and stores `auth_token`/`startup_mode` changes as
  "deferred," and `docs/05_agent_08_configuration.md` documents this as
  intentional.
- **Statement B:** This is unsafe — `ToolExecutor` and `HttpTransport` build
  their state from MCP server config once at startup and never re-read it,
  so reload-time mutation desyncs the live transport/executor from
  `ctx.cfg.mcp.mcp_servers`. Requirements H-1 through L-3
  (`requires/done/20260708_23_require.md` through
  `requires/done/20260708_41_require.md`) have approved plans (see `plans/`)
  to replace this with restart-required-only classification
  (`mcp/<server>.<field>` entries in `needs_restart`, never mutated), and to
  remove the legacy `github_server_url` duplicate key in favor of
  `mcp_servers.github.url`.
- **Current safe interpretation:** Until H-1 through L-3 are implemented,
  the code still behaves per Statement A. Do not build new MCP hot-reload
  features on the current deferred/apply mechanism — any new MCP reload
  work should target the restart-required-only design in the linked plans.
- **Recommended action:** Implement the plans for H-1 through L-3 (in
  `plans/`, cross-referenced from `requires/done/20260708_23_require.md`
  through `requires/done/20260708_41_require.md`), update the docs each
  plan specifies, then remove this entry or mark it Resolved with the
  implementing commit reference.
- **Notes for AI reference:** If asked to add MCP server hot-reload support,
  point to this entry and the linked requirements instead — restart-required
  classification for all MCP server definition fields is the decided
  direction, not an open question.

---
```

### Method

- Single block replacement; no other section of this file is touched.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Placeholder gone | `grep -n "現在アクティブな問題はありません" docs/04_mcp_90_inconsistencies_and_known_issues.md` | no matches |
| New entry present | `grep -n "BUG-01" docs/04_mcp_90_inconsistencies_and_known_issues.md` | 1 match |
| MCP docs consistency | `uv run check-mcp-docs` | pass |
