## Goal

Correct the stale "ToolExecutor cache" attribution for `CacheEntry` in
`docs/90_shared_02_01_types_and_protocols-core-types.md` (REQ-001), per
`plans/20260825-142943_plan.md`.

## Scope

- In scope: the `CacheEntry` bullet in the types summary table (verified at line
  33 as of 2026-08-27) only.
- Out of scope: any other bullet in this list.

## Assumptions

- `CacheEntry` (`shared/tool_cache.py`) is no longer used by `ToolExecutor` (it
  never was integrated as a live cache backing — only imported for the
  `CacheEntry` dataclass shape, which is now also removed from
  `tool_executor.py` per `plans/done/20260826-120000_plan.md`) — re-verified
  2026-08-27 via `rg -n "CacheEntry" scripts/shared/tool_executor.py` returning
  no matches.

## Design decisions

- Change the "Used by" clause from "`shared/` (ToolExecutor cache)" to "`shared/`
  (standalone utility, unused)" — matching the corrected framing already applied
  to sibling files (`docs/01_overview-files-04-shared.md`,
  `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md`).

## Alternatives considered

- N/A: single-bullet correction.

## Implementation
### Target file
`docs/90_shared_02_01_types_and_protocols-core-types.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 33 as of 2026-08-27).
2. Edit the bullet.
3. Run `uv run python tools/check_docs_consistency.py` (correct domain).

### Method
Direct text edit (Edit tool) — one bullet.

### Details
Current text (verified 2026-08-27, line 33):
```
- `CacheEntry` (frozen dataclass) — `shared/tool_cache.py` — Used by `shared/` (ToolExecutor cache).
```
Change to:
```
- `CacheEntry` (frozen dataclass) — `shared/tool_cache.py` — Standalone utility, not currently used anywhere.
```

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-bullet revert via `git diff`/`git checkout -- <path>`; independent of
  the other 13 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_02_01_types_and_protocols-core-types.md` | Manual diff | `git diff <path>` | "ToolExecutor cache" attribution removed |
| `docs/90_shared_02_01_types_and_protocols-core-types.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py` (correct domain) | No new warning/error |

## Completion criteria

- `rg -n "ToolExecutor cache" docs/90_shared_02_01_types_and_protocols-core-types.md`
  returns no matches.

## Out of scope

- Any other bullet in this list.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Pending | — | — | |
| 2 | Edit the bullet | Pending | — | — | |
| 3 | Run `check_docs_consistency.py` (correct domain) | Pending | — | — | |

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
- **Related target files**: `docs/90_shared_02_01_types_and_protocols-core-types.md`
