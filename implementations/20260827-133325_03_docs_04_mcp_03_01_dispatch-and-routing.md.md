## Goal

Remove the stale cache/stampede-protection description from
`docs/04_mcp_03_01_dispatch-and-routing.md`'s Tool Call Dispatch Flow (REQ-001), per
`plans/20260825-142943_plan.md`.

## Scope

- In scope: the dispatch-flow code block's "1. Cache check" step (verified at
  lines 32-33 as of 2026-08-27), the "Implementation Notes" bullet describing
  stampede protection (line 49), and the keyword-list entry "stampede protection"
  (line 188).
- Out of scope: the rest of the dispatch flow description (startup_mode gate,
  health registry, lifecycle, semaphore, transport call — all still accurate); any
  other section of this document.

## Assumptions

- `ToolExecutor.execute()` no longer performs a cache lookup or stampede-protection
  step — re-verified 2026-08-27: `execute()` calls `_raw_execute()` directly, which
  resolves `server_key`, runs the startup-mode/health gate chain
  (`_run_gate_chain()`), calls `_ensure_lifecycle_ready()`, resolves the transport,
  and dispatches via a per-server semaphore (`_invoke_and_record()`) — no cache, no
  inflight-future sharing anywhere in this path.

## Design decisions

- Remove the "1. Cache check" step from the dispatch-flow code block entirely and
  renumber the remaining steps, rather than leaving a numbered gap.
- Replace the "stampede protection" bullet (line 49) with a note that this
  behavior no longer exists, or remove it outright — since the file's own
  Implementation Notes section otherwise describes only currently-accurate
  behavior, removal (not "marked removed") is more consistent with this section's
  style.
- Remove "stampede protection" from the keyword list (line 188) since it no longer
  describes any current mechanism in this file.

## Alternatives considered

- Keeping the cache step but marking it "(removed)" was considered and rejected —
  per `skills/DESIGN.md` Avoid implementation-reference duplication, a removed
  mechanism with no current relevance is better deleted than annotated in place,
  matching this Plan's Design section's chosen approach (delete/rewrite, not
  "future TBD" placeholders).

## Implementation
### Target file
`docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified at lines
   32-33, 49, 188 as of 2026-08-27).
2. Remove the "1. Cache check (TTL + LRU) ... (cache miss: aggregates concurrent
   execution ... stampede protection)" step from the dispatch-flow code block;
   renumber "2. MCP server dispatch" to "1.".
3. Remove or rewrite the stampede-protection Implementation Notes bullet (line 49).
4. Remove "stampede protection" from the keyword list (line 188).
5. Run `uv run python tools/check_docs_consistency.py --domain mcp`.

### Method
Direct text edits (Edit tool) — one code-block step removal + renumbering, one
bullet removal, one keyword-list entry removal.

### Details
Current dispatch-flow code block (verified 2026-08-27):
```
   → ToolExecutor.execute(tool_name, args)
        1. Cache check (TTL + LRU)             — returns cached result if hit; no HealthRegistry update
           (cache miss: aggregates concurrent execution of the same key with an inflight future — stampede protection)
        2. MCP server dispatch (internal dispatch)
             → startup_mode==none gate → immediate error ("disabled (startup_mode=none)")
             ...
```
Replace with:
```
   → ToolExecutor.execute(tool_name, args)
        1. MCP server dispatch (internal dispatch)
             → startup_mode==none gate → immediate error ("disabled (startup_mode=none)")
             ...
```
Remove line 49's bullet: `- On cache miss, concurrent calls to the same
\`cache_key\` (\`tool_name:json(args)\`) share an \`asyncio.Future\`, ensuring the
actual processing is executed only once (stampede protection). If the caller
raises an exception, that exception is propagated to all waiting callers.
(Explicit in code)` entirely.

Remove the standalone `stampede protection` line from the keyword list (line 188).

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Text revert via `git diff`/`git checkout -- <path>`; independent of the other 13
  target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_03_01_dispatch-and-routing.md` | Manual diff | `git diff <path>` | No cache/stampede-protection claim remains |
| `docs/04_mcp_03_01_dispatch-and-routing.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | No new warning/error |

## Completion criteria

- The dispatch-flow code block no longer includes a cache-check step.
- No "stampede protection" reference remains in this file.

## Out of scope

- The rest of the dispatch-flow description (startup_mode gate, health registry,
  lifecycle, semaphore, transport call).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers | Pending | — | — | |
| 2 | Remove cache-check step, renumber | Pending | — | — | |
| 3 | Remove stampede-protection Implementation Notes bullet | Pending | — | — | |
| 4 | Remove stampede-protection keyword entry | Pending | — | — | |
| 5 | Run `check_docs_consistency.py --domain mcp` | Pending | — | — | |

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
- **Related target files**: `docs/04_mcp_03_01_dispatch-and-routing.md`
