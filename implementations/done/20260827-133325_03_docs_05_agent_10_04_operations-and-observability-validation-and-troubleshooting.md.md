## Goal

Remove the `Cache hits` statistic from `/stats` interpretation in
`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
(REQ-003), per `plans/20260825-142943_plan.md`.

## Scope

- In scope: the `Cache hits` token in the `/stats` example output (verified at
  line 167 as of 2026-08-27) and the "Cache hits" description bullet (verified at
  line 174).
- Out of scope: the rest of the `/stats` example output and description bullets
  (Partial completions, HB timeouts, Approval pending — all still accurate);
  "Semantic cache hits" (an unrelated RAG statistic, not this Plan's concern).

## Assumptions

- `ToolExecutor.stat_cache_hits` and `StatsViewModel.cache_hits`/`cmd_config_stats.py`'s
  `Cache hits` render line were already removed from production code in this same
  plan-to-implementation-procedure session (`plans/20260827-121312_plan.md`'s
  REQ-004, applied and verified 2026-08-27) — this doc update makes the example
  output match that already-shipped behavior. `rg -n "cache_hits"
  scripts/agent/commands/cmd_config_stats.py scripts/agent/commands/models.py`
  confirms only unrelated `semantic_cache_hits` remains.

## Design decisions

- Remove `Cache hits: 3 | ` from the example output line, keeping `Compress: 1 |
  Semantic cache hits: 0` intact.
- Remove the "Cache hits" description bullet entirely.

## Alternatives considered

- N/A: single-line example edit + single-bullet removal, directly matching
  already-shipped code behavior.

## Implementation
### Target file
`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified at lines
   167, 174 as of 2026-08-27).
2. Remove `Cache hits: 3 | ` from the example output.
3. Remove the "Cache hits" description bullet.
4. Run `uv run python tools/check_docs_consistency.py --domain agent`.

### Method
Direct text edits (Edit tool) — one example-output token removal, one bullet
removal.

### Details
Current text (verified 2026-08-27):
- Line 167: `Cache hits: 3 | Compress: 1 | Semantic cache hits: 0`
- Line 174: `- **Cache hits:** Number of tool result cache hits.`

Change line 167 to: `Compress: 1 | Semantic cache hits: 0`

Delete line 174 entirely.

## Compatibility considerations

- Documentation-only; matches already-shipped code behavior (this Plan's REQ-004
  companion Plan already removed the field from production).

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Two-edit revert via `git diff`/`git checkout -- <path>`; independent of the
  other 13 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md` | Manual diff | `git diff <path>` | `Cache hits` removed from example output and description |
| `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain agent` | No new warning/error |

## Completion criteria

- `rg -n "Cache hits" docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
  returns no matches (excluding "Semantic cache hits", an unrelated statistic).

## Out of scope

- The rest of the `/stats` example output and description bullets.
- "Semantic cache hits".

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers | Pending | — | — | |
| 2 | Remove `Cache hits` from example output | Pending | — | — | |
| 3 | Remove "Cache hits" description bullet | Pending | — | — | |
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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142943_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure; supersedes the corresponding portion of `implementations/20260825-224356_11_docs_tool_cache_removal.md` (left Blocked, never implemented)
- **Generated at**: 20260827-133325
- **Related target files**: `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
