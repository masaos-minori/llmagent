## Goal

Remove the stale "ToolExecutor: tool_cache_ttl" hot-reloadable-scope bullet from
`docs/05_agent_08_01_configuration-loading-agent-config.md` (REQ-002), per
`plans/20260825-142943_plan.md`.

## Scope

- In scope: the single bullet under "Hot-Reloadable Scope" (verified at line 48
  as of 2026-08-27) only.
- Out of scope: the other three bullets in the same list (LLMClient,
  HistoryManager, System Prompt — all still accurate).

## Assumptions

- `tool_cache_ttl` is no longer hot-reloadable via `ToolExecutor` (its only
  consumer was removed) — this Plan's REQ-002 removes it here regardless of
  `plans/20260825-142436_plan.md`'s own status (whether the `_apply_tool_params()`
  diff-apply line has been removed yet), since the underlying `ToolExecutor`
  behavior this bullet describes no longer exists either way.

## Design decisions

- Delete the bullet outright — `ToolExecutor` has no hot-reloadable config
  surface left; do not replace it with an empty placeholder.

## Alternatives considered

- N/A: single-bullet removal.

## Implementation
### Target file
`docs/05_agent_08_01_configuration-loading-agent-config.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 48 as of 2026-08-27).
2. Delete the bullet.
3. Run `uv run python tools/check_docs_consistency.py --domain agent`.

### Method
Direct text deletion (Edit tool) — one bullet.

### Details
Current text (verified 2026-08-27, line 48): `- ToolExecutor: tool_cache_ttl`

Delete this line entirely from the "Hot-Reloadable Scope" list.

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-line revert via `git diff`/`git checkout -- <path>`; independent of the
  other 13 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_08_01_configuration-loading-agent-config.md` | Manual diff | `git diff <path>` | Bullet removed |
| `docs/05_agent_08_01_configuration-loading-agent-config.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain agent` | No new warning/error |

## Completion criteria

- `rg -n "tool_cache_ttl" docs/05_agent_08_01_configuration-loading-agent-config.md`
  returns no matches.

## Out of scope

- The other three bullets in the same list.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Pending | — | — | |
| 2 | Delete the bullet | Pending | — | — | |
| 3 | Run `check_docs_consistency.py --domain agent` | Pending | — | — | |

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
- **Related target files**: `docs/05_agent_08_01_configuration-loading-agent-config.md`
