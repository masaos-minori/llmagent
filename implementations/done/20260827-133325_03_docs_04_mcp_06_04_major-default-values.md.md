## Goal

Remove the "Tool cache TTL" and "Tool cache max size" rows from
`docs/04_mcp_06_04_major-default-values.md` (REQ-002), per
`plans/20260825-142943_plan.md`.

## Scope

- In scope: the two table rows (verified at lines 7-8 as of 2026-08-27) only.
- Out of scope: any other row of this table.

## Assumptions

- `config/agent.toml::tool_cache_ttl`/`tool_cache_max_size` and
  `ToolConfig.tool_cache_ttl`/`tool_cache_max_size` still exist in source as of
  2026-08-27 (their removal is `plans/20260827-121312_plan.md`'s REQ-001, a
  separate Plan not yet implemented) — but per `ToolExecutor`'s own removal, these
  values have no live effect regardless of whether the fields still exist. This
  Plan's REQ-002 removes the doc rows now since the *behavior* they document
  (tool-result caching) is already gone.

## Design decisions

- Delete both rows outright — per this Plan's own Design section ("configuration
  reference tables lose `tool_cache_ttl`/`tool_cache_max_size` rows").

## Alternatives considered

- Marking the rows "(removed)" instead of deleting was considered and rejected —
  this Plan's Design section explicitly calls for deletion from configuration
  reference tables, consistent with the "removed, not TBD" alternative already
  chosen there.

## Implementation
### Target file
`docs/04_mcp_06_04_major-default-values.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified at lines
   7-8 as of 2026-08-27).
2. Delete both rows.
3. Run `uv run python tools/check_docs_consistency.py --domain mcp`.

### Method
Direct text deletion (Edit tool) — two table rows.

### Details
Current rows (verified 2026-08-27, lines 7-8):
```
| Tool cache TTL | 300s | — | `config/agent.toml::tool_cache_ttl` (Default for `ToolConfig.tool_cache_ttl` is also the same) |
| Tool cache max size | 200 entries | — | `config/agent.toml::tool_cache_max_size` (Default for `ToolConfig.tool_cache_max_size` is also the same) |
```
Delete both rows entirely; leave the surrounding table (Max response bytes,
`call_timeout_sec`, Health registry threshold, etc.) unchanged.

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Two-row revert via `git diff`/`git checkout -- <path>`; independent of the other
  13 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_04_major-default-values.md` | Manual diff | `git diff <path>` | Both rows removed |
| `docs/04_mcp_06_04_major-default-values.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | No new warning/error |

## Completion criteria

- `rg -n "tool_cache_ttl|tool_cache_max_size" docs/04_mcp_06_04_major-default-values.md`
  returns no matches.

## Out of scope

- Any other row of this table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers | Pending | — | — | |
| 2 | Delete both rows | Pending | — | — | |
| 3 | Run `check_docs_consistency.py --domain mcp` | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142943_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure; supersedes the corresponding portion of `implementations/20260825-224356_11_docs_tool_cache_removal.md` (left Blocked, never implemented)
- **Generated at**: 20260827-133325
- **Related target files**: `docs/04_mcp_06_04_major-default-values.md`
