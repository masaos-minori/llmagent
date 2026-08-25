# Update documentation once the ToolExecutor result cache is removed

## Priority
Medium

## Summary
Once the tool-result TTL cache (and its stampede protection) is removed from `ToolExecutor` (see Dependencies), several docs will still describe it as active — cache behavior, defaults, and the `Cache hits` stat. This issue tracks the doc updates that must land alongside that removal.

## Background
This issue assumes the same not-yet-filed cache-removal change referenced by `issues/20260825_cfgreload_toolexecutor_cache_wiring_issue.md`. As of this writing, the cache (`ToolExecutor._cache`, `_execute_with_cache`, `stat_cache_hits`, `apply_config(cache_ttl=...)`) is still fully present in `scripts/shared/tool_executor.py` — none of the doc changes below should be applied until the code removal has actually landed.

## Problem
Verified via `grep -rl "stat_cache_hits\|Cache hits\|tool_cache_ttl\|tool_cache_max_size" docs/`, the following docs currently reference the cache (a superset of what was originally noted, confirmed by re-running the search against current file names — several docs have been renumbered/split since this cache documentation was first written and the file list below is the current, verified set):
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md` (§ ToolExecutor cache, § ToolResultCache)
- `docs/04_mcp_03_01_dispatch-and-routing.md`
- `docs/04_mcp_03_02_tool-registry.md` (Cache Behavior, stampede, side-effect detection)
- `docs/04_mcp_06_04_major-default-values.md` (tool cache TTL / max size defaults)
- `docs/05_agent_01_system-overview.md` (Key Constraints: tool cache TTL)
- `docs/05_agent_08_03_configuration-tools-memory.md` (ToolConfig caching section)
- `docs/05_agent_08_01_configuration-loading-agent-config.md`
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
- `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`

## Reason for Change
Leaving these docs describing removed behavior after the code change lands would mislead both human maintainers and AI agents reading the docs into believing tool results are still cached.

## Implementation Intent
Remove or rewrite the sections identified above to state that tool results are no longer cached and that identical concurrent calls now each hit the MCP server (stampede protection removed). Apply `skills/DESIGN.md` "Avoid implementation-reference duplication" — describe the change in terms of behavior/intent, not line-by-line code detail.

## Target Files or Areas
See the list under Problem — re-run the grep at implementation time (`grep -rl "stat_cache_hits\|Cache hits\|tool_cache_ttl\|tool_cache_max_size" docs/`) since this list may drift further before the cache-removal change lands.

## Required Changes
- Remove or rewrite each identified section per Implementation Intent.
- Remove `tool_cache_ttl` / `tool_cache_max_size` from any documented config reference (defaults tables, config field lists).
- Remove or mark-removed the `Cache hits` stat description in any `/stats` or session-summary doc.

## Constraints
- Do not apply any of these edits before the code removal has actually landed — verify with `grep -n "apply_config(self, \*, cache_ttl" scripts/shared/tool_executor.py` returning nothing first.

## Acceptance Criteria
- [ ] No doc claims `ToolExecutor` caches successful results.
- [ ] `tool_cache_ttl` / `tool_cache_max_size` are no longer documented as active config.
- [ ] The `Cache hits` stat description is removed or marked removed.

## Testing Expectations
- Run the repository's documentation consistency check (`tools/check_docs_consistency.py` or equivalent named in `rules/toolchain.md`) and confirm it passes for all affected doc domains.

## Documentation Impact
This issue is itself a documentation-impact issue; no further downstream doc updates are expected beyond the files listed.

## Out of Scope
- Documenting a future replacement cache, if one is ever introduced.
- Any code change (tracked in the separate cache-removal and follow-up issues).

## Dependencies
- Depends on the same not-yet-filed `ToolExecutor` cache-removal change referenced by `issues/20260825_cfgreload_toolexecutor_cache_wiring_issue.md` and `issues/20260825_config_validators_dead_cache_validator_issue.md`. Should land with or immediately after that code removal, not before.

## Unresolved Questions
- N/A: none beyond the shared cache-removal dependency already noted.

## AI Implementation Instruction
Re-run the grep in Target Files or Areas before starting — do not rely solely on the file list captured when this issue was filed, since doc renumbering has already changed this list once between the original investigation and this issue's filing. Do not touch any doc section unrelated to the tool-result cache.
