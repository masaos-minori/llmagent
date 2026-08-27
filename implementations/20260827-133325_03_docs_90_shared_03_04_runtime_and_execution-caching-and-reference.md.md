## Goal

Remove the stale `ToolExecutor` cache description from
`docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md`'s section 9
and the AI Reference Guide, and correct the `ToolResultCache` stampede-protection
comparison in section 15 (REQ-001), per `plans/20260825-142943_plan.md`.

## Scope

- In scope: section 9 "`ToolExecutor` and Surrounding Concepts" (verified lines
  1-16 as of 2026-08-27), the `ToolResultCache` "stampede protection" clause in
  section 15 (verified line ~13 in that section), and the two `ToolExecutor`-cache
  AI Reference Guide rows (verified in section 20).
- Out of scope: sections 14 (`LlmRetryHandler`), 16 (`ToolSpec`), 17
  (`McpServerHealthState`/`McpServerHealthRegistry`), 18 (`LlmPayloadHandler`), 19
  (`LlmHotConfigHandler`) — all unrelated to `ToolExecutor`'s cache and still
  accurate; every other AI Reference Guide row.

## Assumptions

- **Correction to the existing (never-implemented) implementation procedure**:
  `implementations/20260825-224356_11_docs_tool_cache_removal.md`'s Action for
  this file was "Either delete the entire file or rewrite it as a historical
  reference" — re-reading the full file (2026-08-27) found this recommendation
  overly broad: the file also documents `LlmRetryHandler`, `ToolResultCache`
  (`CacheEntry` itself, which still exists in code and is unrelated to
  `ToolExecutor`'s removed cache), `ToolSpec`, `McpServerHealthState`/
  `McpServerHealthRegistry`, `LlmPayloadHandler`, `LlmHotConfigHandler`, and an AI
  Reference Guide covering all of the above — none of which should be deleted.
  This item scopes the fix to only the `ToolExecutor`-cache-specific content
  (section 9's cache description, section 15's stampede-protection comparison,
  and two AI Reference Guide rows), not the whole file.
- `ToolExecutor` no longer has any cache; `_execute_with_stampede_protection()`
  and `self._inflight` are also fully removed — re-verified 2026-08-27.
- `CacheEntry`/`ToolResultCache` (`shared/tool_cache.py`) themselves still exist
  in code, unused by `ToolExecutor` — this item does not touch section 15's
  factual description of `ToolResultCache` itself, only its comparison to
  `ToolExecutor`'s (now-removed) stampede protection.

## Design decisions

- Rewrite section 9's "Execution Flow" sentence and "Caching Behavior" sentence
  the same way as the parallel edit in
  `implementations/20260827-133325_03_docs_90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md.md`
  (same underlying `ToolExecutor.execute()` behavior, described in a different
  file).
- In section 15, remove only the "kept for potential future use without
  stampede protection" clause — `ToolResultCache`'s own description (frozen
  dataclass, key format, `store_if_success()`) remains accurate and unchanged.
- In the AI Reference Guide (section 20), remove the two rows specifically about
  `ToolExecutor`'s cache ("When does `ToolExecutor` use its cache?", "What is the
  `ToolExecutor` cache key format?") — every other row is unrelated and stays.

## Alternatives considered

- Deleting the entire file (the existing, never-implemented procedure's
  suggestion) was considered and rejected per Assumptions — the file's other 6
  sections and most of the AI Reference Guide remain accurate and independently
  useful.

## Implementation
### Target file
`docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified as of
   2026-08-27; re-read the full file first since section numbering may shift if
   any section is later removed by an unrelated change).
2. Rewrite section 9's "Execution Flow"/"Caching Behavior" content (see Details).
3. Remove the stampede-protection clause from section 15.
4. Remove the two `ToolExecutor`-cache rows from the AI Reference Guide (section
   20).
5. Run `uv run python tools/check_docs_consistency.py` (correct domain).

### Method
Direct text edits (Edit tool) — one section content rewrite, one clause removal,
two table row removals.

### Details
Section 9 current text (verified 2026-08-27):
```
**Responsibility:** Core engine for tool dispatching — handles tool → server resolution, caching, concurrency limits, health gating, and transport communication.

**`ToolCallResult` Data Class ...** (leave unchanged — see Out of scope)

**Execution Flow:** TTL+LRU cache check (success results only); stampede protection shares a `Future` for concurrent calls with the same key; resolve `tool_name` → `server_key` via `ToolRouteResolver`; `startup_mode=none` gate rejects disabled servers; `McpServerHealthRegistry.is_unavailable()` blocks `UNAVAILABLE` dispatch (`HALF_OPEN` allows one attempt per cooldown); `lifecycle.ensure_ready()` if configured; execute via `HttpTransport.call()` behind a per-server-key semaphore; cache success results only; return `ToolCallResult`.

**Caching Behavior:** Success results only (`is_error=False` excluded); TTL+LRU eviction configurable via `tool_cache_ttl_sec`/`tool_cache_maxsize`; key = (`tool_name`, serialized_args); side-effect tools fully bypass the cache.
```
Change "**Responsibility:**" to remove "caching" from the list (e.g. "handles
tool → server resolution, concurrency limits, health gating, and transport
communication"). Rewrite "Execution Flow" to remove the cache-check/stampede
clauses (mirror the sibling file's rewrite). Delete "Caching Behavior" entirely.

Section 15 current text (verified 2026-08-27): `` A standalone LRU+TTL cache
utility for tool results. Not currently used by `ToolExecutor`; kept for
potential future use without stampede protection. `` — remove "kept for
potential future use without stampede protection" (since `ToolExecutor` has no
stampede protection to contrast with anymore); keep "Not currently used by
`ToolExecutor`" as still-accurate.

AI Reference Guide (section 20) current rows (verified 2026-08-27): `| When does
\`ToolExecutor\` use its cache? | Only for \`is_error=False\` results; uses TTL +
LRU. Note: \`ToolExecutor\` uses its own internal \`OrderedDict\`-based cache
(\`_execute_with_cache()\`) rather than \`shared/tool_cache.py\`'s
\`ToolResultCache\` (section 15) |` and `| What is the \`ToolExecutor\` cache key
format? | \`{tool_name}:{json_dumps(args)}\` (using \`shared.json_utils.dumps\`)
|` — delete both rows entirely.

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected. `CacheEntry`/`ToolResultCache`'s own description is preserved
  unchanged.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Text revert via `git diff`/`git checkout -- <path>`; independent of the other
  13 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md` | Manual diff | `git diff <path>` | Section 9 no longer describes a `ToolExecutor` cache; section 15's stampede-protection clause removed; the two AI Reference Guide rows removed; sections 14/16-19 and `ToolResultCache`'s own description unchanged |
| `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py` (correct domain) | No new warning/error |

## Completion criteria

- Section 9 no longer claims `ToolExecutor` has a cache.
- Section 15 no longer contrasts `ToolResultCache` against `ToolExecutor`'s
  (removed) stampede protection.
- The AI Reference Guide no longer has a row about `ToolExecutor`'s cache.
- Sections 14, 16-19 and every other AI Reference Guide row are unchanged.

## Out of scope

- The `ToolCallResult` data class description in section 9.
- Sections 14, 16, 17, 18, 19.
- Deleting this file entirely (rejected, see Assumptions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm current section content | Pending | — | — | |
| 2 | Rewrite section 9 | Pending | — | — | |
| 3 | Remove stampede-protection clause from section 15 | Pending | — | — | |
| 4 | Remove 2 AI Reference Guide rows | Pending | — | — | |
| 5 | Run `check_docs_consistency.py` (correct domain) | Pending | — | — | |

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
- **Source implementation procedure**: N/A: this document is the generated implementation procedure; corrects and supersedes `implementations/20260825-224356_11_docs_tool_cache_removal.md`'s overly-broad "delete entire file" suggestion for this target (left Blocked, never implemented)
- **Generated at**: 20260827-133325
- **Related target files**: `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md`
