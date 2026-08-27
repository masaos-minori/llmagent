## Goal

Remove the stale "TTL cache" component description and "Tool result cache TTL"
constraint row from `docs/05_agent_01_system-overview.md` (REQ-001, REQ-002), per
`plans/20260825-142943_plan.md`.

## Scope

- In scope: the `ToolExecutor` row in the Component Dependencies table (verified
  at line 47 as of 2026-08-27) and the "Tool result cache TTL" row in Key
  Constraints (verified at line 63).
- Out of scope: any other row of either table.

## Assumptions

- `ToolExecutor` no longer has a TTL cache — re-verified 2026-08-27.

## Design decisions

- Change the `ToolExecutor` component row's description from "MCP routing, TTL
  cache" to "MCP routing" (remove only the cache clause, keep the row).
- Delete the "Tool result cache TTL" constraint row outright — this is a
  configuration reference row, not a component description, so removal (matching
  this Plan's Design decision for reference tables) is appropriate rather than
  editing in place.

## Alternatives considered

- N/A: both edits are narrow, single-row corrections following this Plan's
  established pattern.

## Implementation
### Target file
`docs/05_agent_01_system-overview.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified at lines
   47, 63 as of 2026-08-27).
2. Change the `ToolExecutor` row's description.
3. Delete the "Tool result cache TTL" row.
4. Run `uv run python tools/check_docs_consistency.py --domain agent`.

### Method
Direct text edits (Edit tool) — one cell edit, one row deletion.

### Details
Current text (verified 2026-08-27):
- Line 47: `| \`ToolExecutor\` | MCP routing, TTL cache |`
- Line 63: `| Tool result cache TTL | \`tool_cache_ttl\` (default 300 sec) |`

Change line 47 to: `| \`ToolExecutor\` | MCP routing |`

Delete line 63 entirely.

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Two-edit revert via `git diff`/`git checkout -- <path>`; independent of the
  other 13 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_01_system-overview.md` | Manual diff | `git diff <path>` | `ToolExecutor` row says "MCP routing" only; cache TTL constraint row removed |
| `docs/05_agent_01_system-overview.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain agent` | No new warning/error |

## Completion criteria

- `rg -n "TTL cache|tool_cache_ttl" docs/05_agent_01_system-overview.md` returns no
  matches.

## Out of scope

- Any other row of either table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers | Pending | — | — | |
| 2 | Edit `ToolExecutor` row | Pending | — | — | |
| 3 | Delete "Tool result cache TTL" row | Pending | — | — | |
| 4 | Run `check_docs_consistency.py --domain agent` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142943_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure; supersedes the corresponding portion of `implementations/20260825-224356_11_docs_tool_cache_removal.md` (left Blocked, never implemented)
- **Generated at**: 20260827-133325
- **Related target files**: `docs/05_agent_01_system-overview.md`
