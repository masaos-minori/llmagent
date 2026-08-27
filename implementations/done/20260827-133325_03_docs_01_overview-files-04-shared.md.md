## Goal

Remove the stale "TTL cache" mentions from `docs/01_overview-files-04-shared.md`'s
file-inventory descriptions of `tool_executor.py` and `tool_cache.py` (REQ-001),
per `plans/20260825-142943_plan.md`.

## Scope

- In scope: the `tool_executor.py` bullet (verified at line 126 as of
  2026-08-27) and the "Control via Caching and Health Checks" paragraph (verified
  at line 172).
- Out of scope: the `tool_cache.py` bullet (line 131 — already correctly notes
  `ToolResultCache` is a standalone utility not used within `ToolExecutor`; leave
  as-is per this Plan's own note).

## Assumptions

- `tool_executor.py` no longer implements a TTL cache — re-verified 2026-08-27.
- Line 131's existing wording already correctly describes `ToolResultCache` as
  unused by `ToolExecutor` — this remains true and needs no change.

## Design decisions

- Change line 126's description from "ToolExecutor: MCP server routing & TTL
  cache" to "ToolExecutor: MCP server routing" (remove only the cache clause).
- Simplify line 172's paragraph to remove the now-inaccurate framing that implies
  `ToolResultCache` reduces redundant calls (via a hypothetical/potential
  integration), while keeping the accurate standalone-utility note and the health
  check description.

## Alternatives considered

- N/A: narrow, targeted edits.

## Implementation
### Target file
`docs/01_overview-files-04-shared.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified at lines
   126, 172 as of 2026-08-27).
2. Edit line 126.
3. Simplify line 172's paragraph.
4. Run `uv run python tools/check_docs_consistency.py` (correct domain).

### Method
Direct text edits (Edit tool) — one bullet edit, one paragraph simplification.

### Details
Current text (verified 2026-08-27):
- Line 126: `- \`tool_executor.py\` — ToolExecutor: MCP server routing & TTL
  cache`
- Line 172: `\`tool_cache.py\`'s \`ToolResultCache\` reduces redundant upstream
  calls using TTL-based caching, but carries the risk of result staleness.
  Additionally, health checks using \`mcp_health.py\` enable dispatch control
  based on server status (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN). Note that
  \`ToolResultCache\` is a standalone utility and is not currently integrated
  into the internal cache of \`ToolExecutor\`.`

Change line 126 to: `- \`tool_executor.py\` — ToolExecutor: MCP server routing`

Rewrite line 172 to remove the "reduces redundant upstream calls" framing (since
`ToolResultCache` is not actually integrated anywhere, it does not currently
reduce anything) while keeping the health-check description, e.g.: `\`tool_cache.py\`'s \`ToolResultCache\` is a standalone LRU+TTL cache utility, not
currently used anywhere in the codebase. Health checks using \`mcp_health.py\`
enable dispatch control based on server status
(HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN).`

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Text revert via `git diff`/`git checkout -- <path>`; independent of the other
  13 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-04-shared.md` | Manual diff | `git diff <path>` | No "TTL cache" claim for `tool_executor.py`; `ToolResultCache` paragraph no longer implies active integration |
| `docs/01_overview-files-04-shared.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py` (correct domain) | No new warning/error |

## Completion criteria

- `rg -n "TTL cache" docs/01_overview-files-04-shared.md` returns no matches for
  the `tool_executor.py` line.

## Out of scope

- The `tool_cache.py` bullet (line 131, already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers | Pending | — | — | |
| 2 | Edit line 126 | Pending | — | — | |
| 3 | Simplify line 172 | Pending | — | — | |
| 4 | Run `check_docs_consistency.py` (correct domain) | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142943_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure; supersedes the corresponding portion of `implementations/20260825-224356_11_docs_tool_cache_removal.md` (left Blocked, never implemented)
- **Generated at**: 20260827-133325
- **Related target files**: `docs/01_overview-files-04-shared.md`
