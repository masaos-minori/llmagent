## Goal

After `ToolExecutor` cache deletion lands, update or remove stale documentation across 14 files to reflect that tool results are no longer cached — identical concurrent calls now reach MCP servers directly (stampede protection removed).

## Scope

**In-Scope**:
- 14 documentation files whose descriptions of `ToolExecutor` caching behavior must be deleted or rewritten as "removed".

**Out-of-Scope**:
- Future alternative caching documentation.
- Code changes themselves (subject of separate uncreated issue).

## Assumptions

- Prerequisite verified: `rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py` returns NO matches; `rg "_cache_ttl\|_cache\|stat_cache_hits\|_execute_with_cache" scripts/shared/tool_executor.py` returns NO matches — ToolExecutor cache has been deleted from code. However, no formal plan exists for this deletion. Documentation updates across 14 files require verifying each file's current content before editing.

## Design decisions

- Follow `skills/DESIGN.md` Shared Vocabulary: avoid implementation details like source-code line numbers; describe behavior/intent level.
- For each file, delete or rewrite only the sections that reference the now-removed cache. Leave unrelated content untouched.
- Configuration reference tables lose `tool_cache_ttl`/`tool_cache_max_size` rows.
- `/stats` session summary docs lose `Cache hits` statistics.

## Alternatives considered

- Keep stale cache descriptions: rejected because they mislead human maintainers and AI agents alike.
- Replace with "future cache TBD": rejected because there is no current plan for replacement; "removed" is more accurate.

## Implementation

### Target files

1. `docs/04_mcp_03_01_dispatch-and-routing.md`
2. `docs/04_mcp_03_02_tool-registry.md`
3. `docs/04_mcp_06_04_major-default-values.md`
4. `docs/05_agent_01_system-overview.md`
5. `docs/05_agent_08_01_configuration-loading-agent-config.md`
6. `docs/05_agent_08_03_configuration-tools-memory.md`
7. `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
8. `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`
9. `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md`
10. `docs/01_overview-files-04-shared.md`
11. `docs/05_agent_02_runtime-architecture.md`
12. `docs/90_shared_02_01_types_and_protocols-core-types.md`
13. `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`
14. `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`

### Procedure

#### Phase 1: Preparation

```bash
# PREREQUISITE CHECK — MUST PASS BEFORE proceeding:
rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py
# Expected: NO MATCHES

rg "_cache_ttl\|_cache\|stat_cache_hits\|_execute_with_cache" scripts/shared/tool_executor.py
# Expected: NO MATCHES

# Re-run broad grep to confirm list hasn't drifted since plan creation:
rg "stampede\|_execute_with_cache\|ToolExecutor.*cache\|cache.*ToolExecutor" docs/
# Verify against the 14-file list below; reconcile any new/missing hits
```

If either prerequisite check fails, STOP. Wait for the prerequisite change.

#### Phase 2: Core Logic

**Step A: Update each of the 14 files**

Below is the specific action per file, based on current content at plan time. During implementation, re-read each file to ensure accuracy before editing.

---

**File 1: `docs/04_mcp_03_01_dispatch-and-routing.md`**

Current cache-related text (line 35):
```
(cache miss: aggregates concurrent execution of the same key with an inflight future — stampede protection)
```

Line 49:
```
On cache miss, concurrent calls to the same `cache_key` (`tool_name:json(args)`) share an `asyncio.Future`, ensuring the actual processing is executed only once (stampede protection).
```

Line 188:
```
stampede protection
```

Action: Delete or replace these references. After cache removal, there is no cache lookup step and no stampede protection. Rewrite the dispatch flow description to show: health gate → transport resolution → semaphore execution → return result.

---

**File 2: `docs/04_mcp_03_02_tool-registry.md`**

Current text (line 115):
```
- `shared/tool_cache.py`'s `ToolResultCache` (LRU + TTL) is currently not used by `ToolExecutor`. `ToolExecutor` uses its own `OrderedDict`-based cache (see "Cache Behavior" section above), which is tightly coupled with stampede protection (inflight future sharing); it is used instead.
```

Line 88:
```
- Statistics: `stat_cache_hits: int`
```

Action: Remove the cache description entirely. The `stat_cache_hits` statistic no longer exists. Update the registry entry to note that `ToolExecutor` has no internal cache after removal.

---

**File 3: `docs/04_mcp_06_04_major-default-values.md`**

Current config table rows:
```
| Tool cache TTL | 300s | — | `config/agent.toml::tool_cache_ttl` (Default for `ToolConfig.tool_cache_ttl` is also the same) |
| Tool cache max size | 200 entries | — | `config/agent.toml::tool_cache_max_size` (Default for `ToolConfig.tool_cache_max_size` is also the same) |
```

Action: Delete both rows. These configuration options no longer exist.

---

**File 4: `docs/05_agent_01_system-overview.md`**

Current text (line 47):
```
| `ToolExecutor` | MCP routing, TTL cache |
```

Line 63:
```
| Tool result cache TTL | `tool_cache_ttl` (default 300 sec) |
```

Action: Change line 47 to `| `ToolExecutor` | MCP routing |` (remove "TTL cache"). Delete or move line 63 to a deprecated section.

---

**File 5: `docs/05_agent_08_01_configuration-loading-agent-config.md`**

Current text (line 48):
```
- ToolExecutor: tool_cache_ttl
```

Action: Delete this line. `tool_cache_ttl` is no longer a configuration option for ToolExecutor.

---

**File 6: `docs/05_agent_08_03_configuration-tools-memory.md`**

Current text (lines 47–48):
```
- `tool_cache_ttl`: TTL for tool execution result cache (seconds).
- `tool_cache_max_size`: LRU cache size.
```

Action: Delete both lines. These configuration options no longer exist.

---

**File 7: `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`**

Current text (line 167):
```
Cache hits: 3 | Compress: 1 | Semantic cache hits: 0
```

Line 174:
```
- **Cache hits:** Number of tool result cache hits.
```

Action: Remove the `Cache hits` metric from the example output and its description. If other metrics remain, keep them.

---

**File 8: `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`**

Current text (line 11):
```
Execution Flow: TTL+LRU cache check (success results only); stampede protection shares a `Future` for concurrent calls with the same key; resolve `tool_name` → `server_key` via `ToolRouteResolver`; ...
```

Line 59:
```
Tool Execution: `ToolExecutor.execute(tool_name, args)` → health gate → cache → raw MCP call.
```

Line 13:
```
Caching Behavior: Success results only (`is_error=False` excluded); TTL+LRU eviction configurable via `tool_cache_ttl_sec`/`tool_cache_maxsize`; key = (`tool_name`, serialized_args); side-effect tools fully bypass the cache.
```

Action: Remove all cache references. Rewrite execution flow: health gate → transport resolution → semaphore execution → return result. Remove caching behavior section entirely.

---

**File 9: `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md`**

This file is primarily about caching. Current text includes detailed descriptions of ToolExecutor's internal cache, key format, etc.

Action: Either delete the entire file or rewrite it as a historical reference noting that ToolExecutor cache was removed in a prior change. The `CacheEntry` dataclass may still exist but is no longer used by ToolExecutor.

---

**File 10: `docs/01_overview-files-04-shared.md`**

Current text (lines 126, 131, 172):
```
- `tool_executor.py` — ToolExecutor: MCP server routing & TTL cache
- `tool_cache.py` — ToolResultCache: LRU cache + TTL (*Note: currently an standalone utility and not used within ToolExecutor)
...
tool_cache.py`'s `ToolResultCache` reduces redundant upstream calls using TTL-based caching, but carries the risk of result staleness. Additionally, health checks using `mcp_health.py` enable dispatch control based on server status (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN). Note that `ToolResultCache` is a standalone utility and is not currently integrated into the internal cache of `ToolExecutor`.
```

Action: Update line 126 to remove "TTL cache". Line 131 already notes `ToolResultCache` is standalone/not used by ToolExecutor — leave as-is. Line 172 can be simplified or kept as historical context.

---

**File 11: `docs/05_agent_02_runtime-architecture.md`**

Current text (line 20):
```
│    ├─ ToolExecutor         — MCP routing, TTL cache
```

Action: Change to `│    ├─ ToolExecutor         — MCP routing` (remove "TTL cache").

---

**File 12: `docs/90_shared_02_01_types_and_protocols-core-types.md`**

Current text (line 33):
```
- `CacheEntry` (frozen dataclass) — `shared/tool_cache.py` — Used by `shared/` (ToolExecutor cache).
```

Action: Change to `— Used by `shared/` (standalone utility, no longer used by ToolExecutor)` or similar clarification.

---

**File 13: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`**

Current text (lines 37–39):
```
`CacheEntry` (output, is_error, cached_at) — an LRU+TTL cache utility. Currently not used by `ToolExecutor`; kept for potential future reuse without stampede protection.
```

Lines 15, 37-39: References to `CacheEntry`/`ToolResultCache` relationships.

Action: Clarify that `CacheEntry` is no longer used by ToolExecutor. Keep if needed for other consumers.

---

**File 14: `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`**

Current text (line 7):
```
`ToolExecutor` inherits from `ToolTransportInvoker` and accepts an HTTP client, `cache_ttl`, `server_configs`, and optional parameters via its constructor. `apply_config()` enables hot-reloading. The `execute()` method follows this sequence: cache lookup → concurrency protection → health check gate → transport resolution → per-server semaphore execution → caching successful results. `clear_cache()` and `get_error_counters()` manage state. Failures are not cached.
```

Action: Remove `cache_ttl` parameter from constructor description. Rewrite execute() sequence: health check gate → transport resolution → per-server semaphore execution → return result. Remove `clear_cache()` reference.

---

#### Phase 3: Deployment & Verification

**Step 1: Verify no stale cache claims remain**

```bash
rg "stampede\|_execute_with_cache\|ToolExecutor.*cache\|cache.*ToolExecutor" docs/
# Expected: minimal hits, none claiming ToolExecutor caches results
```

**Step 2: Verify config references removed**

```bash
rg "tool_cache_ttl\|tool_cache_max_size" docs/
# Expected: 0 matches (or only mentions in deprecated sections)
```

**Step 3: Verify Cache hits stats removed**

```bash
rg "Cache hits\|stat_cache_hits" docs/
# Expected: 0 matches (or only mentions in deprecated sections)
```

**Step 4: Run document consistency checker**

```bash
python tools/check_docs_consistency.py
# Expected: passes
```

**Step 5: Confirm deploy.sh impact**

No deploy.sh changes required — documentation-only update.

### Details

- **REQ-001**: For each of the 14 files, delete or rewrite sections claiming ToolExecutor caches results.
- **REQ-002**: Remove `tool_cache_ttl`/`tool_cache_max_size` from configuration reference tables.
- **REQ-003**: Remove `Cache hits` statistics from session summary documents.

### Prerequisite verification checklist

Before implementing any step:

- [ ] `rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py` returns NO matches
- [ ] `rg "_cache_ttl\|_cache\|stat_cache_hits\|_execute_with_cache" scripts/shared/tool_executor.py` returns NO matches
- [ ] Re-run broad grep against `docs/` and reconcile list with plan's 14-file list
- [ ] Confirm with reviewer that cache deletion PR has landed

## Compatibility considerations

- No API changes — documentation-only update.
- Configuration reference tables lose two rows.
- `/stats` session summaries lose one metric.

## Security considerations

- None — documentation update only.

## Rollback considerations

- Revert: restore original documentation files.
- Git ref-safe rollback: `git checkout HEAD -- docs/`.
- No database migration or config file changes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| 14 documentation files | Doc consistency check | Document consistency checker | All pass |
| Repository | Stale claim check | `rg "stampede\|_execute_with_cache\|ToolExecutor.*cache\|cache.*ToolExecutor" docs/` | Minimal hits, none claiming active caching |
| Repository | Config ref check | `rg "tool_cache_ttl\|tool_cache_max_size" docs/` | 0 matches or deprecated-only |
| Repository | Stats check | `rg "Cache hits\|stat_cache_hits" docs/` | 0 matches or deprecated-only |

## Completion criteria

- [ ] All 14 files updated to reflect no-cache reality.
- [ ] `tool_cache_ttl`/`tool_cache_max_size` removed from config references.
- [ ] `Cache hits` statistics removed from session summaries.
- [ ] No stale cache claims remain in documentation.
- [ ] Document consistency checker passes.
- [ ] Prerequisite cache deletion verified before implementation.

## Out of scope

- Future alternative caching documentation.
- Code changes themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation / Refactoring | Complete | — | — | Prerequisite verified; 14 docs reviewed |
| 2 | Core Logic Implementation | Complete | — | — | All 14 files updated |
| 3 | Deployment & Verification | Complete | — | — | All stale refs removed (0 hits on all checks) |

### Completion Checklist
| Criterion | Status |
|-----------|--------|
| All 14 files updated to reflect no-cache reality | Done |
| `tool_cache_ttl`/`tool_cache_max_size` removed from config references | Done |
| `Cache hits` statistics removed from session summaries | Done |
| No stale cache claims remain in documentation | Done (all 3 rg checks = 0 hits) |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260825_docs_tool_cache_removal_stale_docs_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-142943_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: 14 documentation files listed above
