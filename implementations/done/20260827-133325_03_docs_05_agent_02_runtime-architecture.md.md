## Goal

Remove the stale "TTL cache" mention from `docs/05_agent_02_runtime-architecture.md`'s
component-dependency diagram (REQ-001), per `plans/20260825-142943_plan.md`.

## Scope

- In scope: the single `ToolExecutor` line in the ASCII component diagram
  (verified at line 20 as of 2026-08-27) only.
- Out of scope: the rest of the diagram (LLMClient, HistoryManager,
  ServerLifecycleRouter, etc. — all still accurate).

## Assumptions

- `ToolExecutor` no longer has a TTL cache — re-verified 2026-08-27.

## Design decisions

- Change the line's description from "MCP routing, TTL cache" to "MCP routing" —
  matching the identical edit already made to
  `docs/05_agent_01_system-overview.md`'s Component Dependencies table row for
  the same component.

## Alternatives considered

- N/A: single-line diagram edit.

## Implementation
### Target file
`docs/05_agent_02_runtime-architecture.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 20 as of 2026-08-27).
2. Edit the line, preserving the diagram's exact indentation and box-drawing
   characters.
3. Run `uv run python tools/check_docs_consistency.py` (correct domain).

### Method
Direct text edit (Edit tool) — one line within a fenced code block, preserving
alignment.

### Details
Current text (verified 2026-08-27, line 20):
```
   │    ├─ ToolExecutor         — MCP routing, TTL cache
```
Change to:
```
   │    ├─ ToolExecutor         — MCP routing
```
Preserve the exact leading whitespace/box-drawing characters (`│    ├─`) and the
spacing before the em-dash, so the diagram's column alignment with sibling lines
(`LLMClient`, `HistoryManager`, `ServerLifecycleRouter`) is not disturbed.

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
| `docs/05_agent_02_runtime-architecture.md` | Manual diff | `git diff <path>` | "TTL cache" removed; diagram alignment preserved |
| `docs/05_agent_02_runtime-architecture.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py` (correct domain) | No new warning/error |

## Completion criteria

- `rg -n "TTL cache" docs/05_agent_02_runtime-architecture.md` returns no
  matches.
- The diagram's column alignment is unchanged for all other lines.

## Out of scope

- The rest of the component-dependency diagram.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Pending | — | — | |
| 2 | Edit the line, preserve alignment | Pending | — | — | |
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
- **Related target files**: `docs/05_agent_02_runtime-architecture.md`
