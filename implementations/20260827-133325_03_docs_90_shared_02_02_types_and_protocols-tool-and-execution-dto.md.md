## Goal

Remove the stale "stampede protection" comparison from `CacheEntry`'s description
in `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` (REQ-001),
per `plans/20260825-142943_plan.md`.

## Scope

- In scope: the "7b. `CacheEntry` / `ToolResultCache`" section (verified at lines
  37-39 as of 2026-08-27) only.
- Out of scope: "6a. `ToolCallResult` / `TransportErrorInfo`" (line 15, mentions
  `source` field's `'cache'`/`'mcp'` values — a separate DTO description not in
  this Plan's target list; verify separately if it needs correction, see Details);
  "7. `ActionResult`", "7a. `ToolSpec`", "7c. `RuntimeTool`" — all unrelated and
  accurate.

## Assumptions

- `ToolExecutor` no longer has stampede protection (`_execute_with_stampede_protection()`,
  `self._inflight`) — re-verified 2026-08-27.
- `CacheEntry`/`ToolResultCache` themselves still exist in code
  (`shared/tool_cache.py`), unused by `ToolExecutor` — this item does not remove
  the `CacheEntry` description itself, only its now-inaccurate comparison to
  stampede protection.

## Design decisions

- Remove "kept for potential future reuse without stampede protection" from the
  `CacheEntry` description — mirroring the identical correction already applied
  to `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md`'s
  section 15 (same underlying dataclass, described in two files).

## Alternatives considered

- N/A: narrow clause removal.

## Implementation
### Target file
`docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified at lines
   37-39 as of 2026-08-27).
2. Remove the stampede-protection clause from the "7b" section.
3. While re-reading this file, verify whether "6a. `ToolCallResult` /
   `TransportErrorInfo`" (line 15) needs a correction for its `'cache'` source
   value — this file's own scope per this Plan's 14-file list does not explicitly
   name line 15, but confirm during implementation whether `ToolCallResult.source`
   still accepts `'cache'` in the current DTO definition (`shared/transport_dto.py`);
   if the value was removed from the DTO itself, report a `Plan Gap` rather than
   silently editing beyond this Plan's stated scope.
4. Run `uv run python tools/check_docs_consistency.py` (correct domain).

### Method
Direct text edit (Edit tool) — one clause removal.

### Details
Current text (verified 2026-08-27, section "7b", lines 37-39): `` `CacheEntry`
(output, is_error, cached_at) — an LRU+TTL cache utility. Currently not used by
`ToolExecutor`; kept for potential future reuse without stampede protection.
(Explicit in code) ``

Change to: `` `CacheEntry` (output, is_error, cached_at) — an LRU+TTL cache
utility. Currently not used by `ToolExecutor`. (Explicit in code) ``

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-clause revert via `git diff`/`git checkout -- <path>`; independent of
  the other 13 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` | Manual diff | `git diff <path>` | "stampede protection" clause removed from `CacheEntry` description |
| `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py` (correct domain) | No new warning/error |

## Completion criteria

- `rg -n "stampede" docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`
  returns no matches.

## Out of scope

- "6a. `ToolCallResult` / `TransportErrorInfo`", "7. `ActionResult`", "7a.
  `ToolSpec`", "7c. `RuntimeTool`".

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers | Pending | — | — | |
| 2 | Remove stampede-protection clause | Pending | — | — | |
| 3 | Check (not edit unless confirmed) `ToolCallResult.source`'s `'cache'` value | Pending | — | — | Report as Plan Gap if the DTO itself changed |
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
- **Related target files**: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`
