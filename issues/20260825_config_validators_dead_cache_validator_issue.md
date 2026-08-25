# Delete `validate_tool_cache_max_size` once `tool_cache_max_size` is removed

## Priority
Low

## Summary
Once `tool_cache_max_size` is removed from `ToolConfig` as part of the `ToolExecutor` cache removal, its validator `validate_tool_cache_max_size` (imported as `_v_tool_cms`) becomes dead code.

## Background
This issue assumes the same not-yet-filed cache-removal change referenced by `issues/20260825_cfgreload_toolexecutor_cache_wiring_issue.md`. As of this writing, `tool_cache_max_size: int = 200` is still defined on `ToolConfig` (`scripts/agent/config_dataclasses.py`) and its validator is still called from `__post_init__` — this issue is not actionable until that removal lands.

## Problem
Verified:
- `scripts/agent/services/config_validators.py:139` defines `validate_tool_cache_max_size(cfg: ToolConfig) -> None`.
- `scripts/agent/config_dataclasses.py:91` imports it as `validate_tool_cache_max_size as _v_tool_cms`, and line 235 calls `_v_tool_cms(self)` inside `ToolConfig.__post_init__`.
- `tool_cache_ttl: float = 300.0` and `tool_cache_max_size: int = 200` are both still declared as fields on `ToolConfig` in current source.

## Reason for Change
Once the cache fields are removed, leaving the validator and its `__post_init__` call in place is dead code that references a field that no longer exists, which would either fail to type-check or silently validate nothing.

## Implementation Intent
Delete the validator and its wiring in lockstep with the cache field removal — not before.

## Target Files or Areas
- `scripts/agent/services/config_validators.py`
- `scripts/agent/config_dataclasses.py` (import + `__post_init__` call)

## Required Changes
- Delete `validate_tool_cache_max_size` from `config_validators.py`.
- Remove its import (`as _v_tool_cms`) and the `_v_tool_cms(self)` call from `ToolConfig.__post_init__`.
- Remove `tool_cache_ttl` / `tool_cache_max_size` fields from `ToolConfig` (this is the cache-removal change itself; list here for completeness of what must land together).

## Constraints
- Must land together with the cache-removal change (`ToolExecutor` + factory injection) — this validator has no purpose independent of the fields it validates.

## Acceptance Criteria
- [ ] No reference to `validate_tool_cache_max_size` / `_v_tool_cms` remains anywhere in the codebase.
- [ ] `ToolConfig` no longer defines `tool_cache_ttl` / `tool_cache_max_size`.

## Testing Expectations
- `grep -rn "tool_cache_max_size\|_v_tool_cms" scripts/` returns nothing.
- `python -c "from agent.config_dataclasses import ToolConfig; ToolConfig()"` succeeds without error.

## Documentation Impact
Covered by `issues/20260825_docs_tool_cache_removal_stale_docs_issue.md` — no separate doc work needed here.

## Out of Scope
- Other `config_validators.py` cleanups (tracked separately in `issues/20260825_config_validators_duplicate_range_checks_issue.md`).

## Dependencies
- Depends on the same not-yet-filed `ToolExecutor` cache-removal change referenced by `issues/20260825_cfgreload_toolexecutor_cache_wiring_issue.md`. Do not implement in isolation before that change lands.

## Unresolved Questions
- N/A: none beyond the shared cache-removal dependency already noted.

## AI Implementation Instruction
Verify the cache-removal change has actually landed (`rg "tool_cache_max_size" scripts/shared/tool_executor.py` returns nothing) before touching this issue. Keep the change to exactly the three deletions listed in Required Changes.
