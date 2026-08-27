## Goal

Remove the stale cache/stampede-protection description from
`docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`'s `ToolExecutor`
section (REQ-001), per `plans/20260825-142943_plan.md`.

## Scope

- In scope: the "Execution Flow" sentence (verified at line 11 as of 2026-08-27),
  the "Caching Behavior" sentence (line 13), and the "Tool Execution" summary
  sentence in section 12 (verified at line 59).
- Out of scope: the `ToolCallResult` data class description (line 9 — still
  accurate, `source` field's `'cache'` value is discussed separately, see Details);
  "Health Gate", "Concurrency Behavior", "Side-Effect Detection" sections — all
  still accurate.

## Assumptions

- `ToolExecutor` no longer has any cache or stampede-protection step —
  re-verified 2026-08-27.
- `ToolCallResult.source`'s `'cache'` value (mentioned in this file's line 9 as
  one of `'mcp'/'cache'/empty`) is a DTO-level enum value that may still exist in
  the dataclass definition even though nothing sets it anymore — this file's DTO
  description (line 9) is out of this item's scope; confirm against
  `shared/transport_dto.py` at implementation time whether the `'cache'` value
  itself was removed from the DTO (if so, this sentence needs a separate,
  follow-up correction not covered by this Plan's 14-file list).

## Design decisions

- Rewrite the "Execution Flow" sentence to remove the cache-check and
  stampede-protection clauses, keeping the rest of the sequence (resolve →
  startup_mode gate → health registry → lifecycle → transport call) accurate to
  current `_raw_execute()` behavior.
- Remove the "Caching Behavior" sentence entirely — no caching behavior exists to
  describe.
- Rewrite "Tool Execution: ... → health gate → cache → raw MCP call" to remove the
  cache step.

## Alternatives considered

- N/A: narrow, targeted removals following this Plan's established pattern.

## Implementation
### Target file
`docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified at lines
   11, 13, 59 as of 2026-08-27).
2. Rewrite the "Execution Flow" sentence.
3. Remove the "Caching Behavior" sentence.
4. Rewrite the "Tool Execution" summary sentence in section 12.
5. Run `uv run python tools/check_docs_consistency.py --domain deployment` (or the
   applicable domain per `docs/00_index.md`'s task mapping for `90_shared_*`
   files — verify before running).

### Method
Direct text edits (Edit tool) — two sentence rewrites, one sentence removal.

### Details
Current text (verified 2026-08-27):
- Line 11 (Execution Flow): `**Execution Flow:** TTL+LRU cache check (success
  results only); stampede protection shares a \`Future\` for concurrent calls
  with the same key; resolve \`tool_name\` $\rightarrow$ \`server_key\` via
  \`ToolRouteResolver\`; \`startup_mode=none\` gate rejects disabled servers;
  \`McpServerHealthRegistry.is_unavailable()\` blocks \`UNAVAILABLE\` dispatch
  (\`HALF_OPEN\` allows one attempt per cooldown); \`lifecycle.ensure_ready()\` if
  configured; execute via \`HttpTransport.call()\` behind a per-server-key
  semaphore; cache success results only; return \`ToolCallResult\`.`
- Line 13 (Caching Behavior): `**Caching Behavior:** Success results only
  (\`is_error=False\` excluded); TTL+LRU eviction configurable via
  \`tool_cache_ttl_sec\`/\`tool_cache_maxsize\`; key = (\`tool_name\`,
  serialized_args); side-effect tools fully bypass the cache.`
- Line 59 (section 12): `**Tool Execution:** \`ToolExecutor.execute(tool_name,
  args)\` $\rightarrow$ health gate $\rightarrow$ cache $\rightarrow$ raw MCP
  call.`

Rewrite line 11 to: `**Execution Flow:** resolve \`tool_name\` $\rightarrow$
\`server_key\` via \`ToolRouteResolver\`; \`startup_mode=none\` gate rejects
disabled servers; \`McpServerHealthRegistry.is_unavailable()\` blocks
\`UNAVAILABLE\` dispatch (\`HALF_OPEN\` allows one attempt per cooldown);
\`lifecycle.ensure_ready()\` if configured; execute via \`HttpTransport.call()\`
behind a per-server-key semaphore; return \`ToolCallResult\`.`

Delete line 13 (the entire "Caching Behavior" sentence).

Rewrite line 59 to: `**Tool Execution:** \`ToolExecutor.execute(tool_name, args)\`
$\rightarrow$ health gate $\rightarrow$ raw MCP call.`

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
| `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md` | Manual diff | `git diff <path>` | No cache/stampede-protection claim remains |
| `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py` (correct domain) | No new warning/error |

## Completion criteria

- `rg -n "cache|stampede" docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`
  returns no matches referring to `ToolExecutor`'s own removed cache (the
  `ToolCallResult.source` DTO field description, if kept, is a separate, narrower
  scope — see Assumptions).

## Out of scope

- `ToolCallResult` data class description (line 9).
- "Health Gate", "Concurrency Behavior", "Side-Effect Detection" sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers | Pending | — | — | |
| 2 | Rewrite "Execution Flow" | Pending | — | — | |
| 3 | Remove "Caching Behavior" | Pending | — | — | |
| 4 | Rewrite "Tool Execution" summary (section 12) | Pending | — | — | |
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
- **Source implementation procedure**: N/A: this document is the generated implementation procedure; supersedes the corresponding portion of `implementations/20260825-224356_11_docs_tool_cache_removal.md` (left Blocked, never implemented)
- **Generated at**: 20260827-133325
- **Related target files**: `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`
