# Remove dead ToolExecutor TTL-cache wiring from the config reload path once the cache is removed

## Priority
High

## Summary
`ConfigReloadService` calls `ToolExecutor.apply_config(cache_ttl=...)` and diff-applies `tool_cache_ttl`, both of which target a cache implementation that is planned for removal. If `apply_config` is deleted from `ToolExecutor` without updating the reload path, `/reload` will raise `AttributeError` at runtime.

## Background
This issue assumes a separate, not-yet-filed change that removes the tool-result TTL cache (and its stampede protection) from `ToolExecutor`. See Dependencies and Unresolved Questions — that removal is not currently tracked as an issue in this repository as of this writing.

## Problem
Verified against current source (`scripts/agent/services/config_reload.py`):
- `_sync_services()` contains:
  ```
  if ctx.services_required.tools is not None:
      ctx.services_required.tools.apply_config(
          cache_ttl=ctx.cfg.tool.tool_cache_ttl
      )
      result.applied.append("tools")
  ```
- `_apply_tool_params()` contains:
  ```
  _apply_float(
      new_cfg, "tool_cache_ttl", lambda v: setattr(cfg.tool, "tool_cache_ttl", v)
  )
  ```
- `ToolExecutor.apply_config(self, *, cache_ttl: float | None = None)` (`scripts/shared/tool_executor.py`) and the `tool_cache_ttl` field on `ToolConfig` (`scripts/agent/config_dataclasses.py`) both still exist today — the cache has not yet been removed. This issue is a follow-up to be implemented together with that removal, not something to apply against the current code as-is.

## Reason for Change
Once the cache and `ToolExecutor.apply_config` are removed, this dead wiring in the config reload path would raise `AttributeError` on every `/reload` call, breaking a live operator-facing command.

## Implementation Intent
Remove the two code blocks in lockstep with the cache removal:
1. Delete the `tools.apply_config(cache_ttl=...)` block from `_sync_services()`, including the `result.applied.append("tools")` line.
2. Delete the `_apply_float(new_cfg, "tool_cache_ttl", ...)` line from `_apply_tool_params()`.
Do not remove other, unrelated fields handled by the same functions.

## Target Files or Areas
- `scripts/agent/services/config_reload.py`

## Required Changes
- Remove the `tools.apply_config(cache_ttl=...)` block in `_sync_services()`.
- Remove the `_apply_float(new_cfg, "tool_cache_ttl", ...)` line in `_apply_tool_params()`.
- Confirm whether `"tools"` should still appear in the reload "applied" report for any other reason before removing `result.applied.append("tools")` — if `ToolExecutor` retains other config knobs synced via `apply_config` after cache removal, keep the call with only the remaining parameters instead of deleting it outright.

## Constraints
- Must land together with (not before) the `ToolExecutor` cache removal change — landing this alone would silently stop applying `tool_cache_ttl` to a cache that still exists.

## Acceptance Criteria
- [ ] No reference to `tool_cache_ttl` or a cache-only `tools.apply_config` call remains in `config_reload.py`, once the cache removal has landed.
- [ ] `/reload` runs without error after the cache-removal change lands.
- [ ] `"tools"` no longer appears in the reload "applied" report, or is documented as removed / repurposed for remaining `ToolExecutor` config knobs.

## Testing Expectations
- Unit test covering `apply_config_dict()` / `_sync_services()` after the change: `/reload` does not raise and does not report `"tools"` as applied (or reports it correctly if `apply_config` is retained for other fields).
- Regression: existing `config_reload` test suite continues to pass.

## Documentation Impact
Covered by the separate documentation issue for the cache removal (see `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md` and related files) — no additional doc changes required here beyond what that issue covers.

## Out of Scope
- Deleting the `ToolExecutor` cache implementation itself (tracked as a separate, not-yet-filed change — see Unresolved Questions).
- Any other `_sync_services()` / `_apply_tool_params()` field.

## Dependencies
- Depends on a separate, not-yet-filed change that removes the `ToolExecutor` TTL cache (`_cache`, `_execute_with_cache`, `stat_cache_hits`) and its `apply_config(cache_ttl=...)` parameter. Do not implement this issue in isolation before that change lands.

## Unresolved Questions
- No issue currently tracks the `ToolExecutor` cache removal itself (verified via repository-wide search of `issues/` and `plans/`). A related but narrower issue, `issues/20260821_09_issue.md`, proposes unifying `ToolResultCache` and `ToolExecutor`'s internal cache rather than removing caching outright — confirm whether that issue supersedes, precedes, or is unrelated to the full removal this issue assumes, before scheduling this work.

## AI Implementation Instruction
Do not implement this issue until the prerequisite `ToolExecutor` cache-removal change has landed and is verifiable in the current source (`rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py` returns nothing). When implementing, re-run `grep -rn "tool_cache_ttl\|apply_config" scripts/agent/services/config_reload.py` first to catch any drift since this issue was filed. Keep the change minimal — remove only the two identified blocks, do not refactor surrounding code.
