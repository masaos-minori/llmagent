## Goal

Remove the stale "Caching" subsection (`tool_cache_ttl`/`tool_cache_max_size`)
from `docs/05_agent_08_03_configuration-tools-memory.md` (REQ-002), per
`plans/20260825-142943_plan.md`.

## Scope

- In scope: the `#### Caching` subsection (verified at lines 46-48 as of
  2026-08-27) only.
- Out of scope: "Context Bloat Prevention" and "Parallel Execution" subsections
  (still accurate); this file's separate "Embedding Related" section's
  `memory_embed_dim` fix (already covered by a different implementation procedure
  in an earlier pass, `implementations/20260827-112854_15_docs_05_agent_08_03_configuration-tools-memory.md.md`
  — an unrelated fix to a different subsection of this same file; both may be
  applied independently).

## Assumptions

- `tool_cache_ttl`/`tool_cache_max_size` are no longer live configuration for
  `ToolExecutor` — re-verified 2026-08-27.
- This is a different target section of the same file already touched by
  `implementations/20260827-112854_15_...` (the `memory_embed_dim` fix) — both
  implementation procedures may be applied to this file in either order without
  conflict, since they touch disjoint line ranges (Embedding Related vs. Caching
  subsections).

## Design decisions

- Delete the entire `#### Caching` subsection (heading + 2 bullets) — per this
  Plan's Design decision for configuration reference content.

## Alternatives considered

- N/A: single-subsection removal.

## Implementation
### Target file
`docs/05_agent_08_03_configuration-tools-memory.md`

### Procedure
1. Re-confirm current line numbers immediately before editing (verified at lines
   46-48 as of 2026-08-27) — note this file may have already been modified by
   `implementations/20260827-112854_15_...`'s `memory_embed_dim` fix; re-read the
   full file to locate the current position of the `#### Caching` subsection if
   line numbers have shifted.
2. Delete the `#### Caching` subsection.
3. Run `uv run python tools/check_docs_consistency.py --domain agent`.

### Method
Direct text deletion (Edit tool) — one subsection (heading + 2 bullets).

### Details
Current text (verified 2026-08-27, lines 46-48):
```
#### Caching

- `tool_cache_ttl`: TTL for tool execution result cache (seconds).
- `tool_cache_max_size`: LRU cache size.
```
Delete this subsection entirely, including its `####` heading. Leave "Context
Bloat Prevention" (above) and "Parallel Execution" (below) unchanged.

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-subsection revert via `git diff`/`git checkout -- <path>`; independent of
  the other 13 target files in this Plan's pass and of the unrelated
  `memory_embed_dim` fix already applied/pending to this same file.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_08_03_configuration-tools-memory.md` | Manual diff | `git diff <path>` | "Caching" subsection removed; "Context Bloat Prevention"/"Parallel Execution" unchanged |
| `docs/05_agent_08_03_configuration-tools-memory.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain agent` | No new warning/error |

## Completion criteria

- `rg -n "tool_cache_ttl|tool_cache_max_size" docs/05_agent_08_03_configuration-tools-memory.md`
  returns no matches.

## Out of scope

- "Context Bloat Prevention", "Parallel Execution".
- The "Embedding Related" section's `memory_embed_dim` fix (separate
  implementation procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers (account for possible prior edit to this file) | Pending | — | — | |
| 2 | Delete the "Caching" subsection | Pending | — | — | |
| 3 | Run `check_docs_consistency.py --domain agent` | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142943_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure; supersedes the corresponding portion of `implementations/20260825-224356_11_docs_tool_cache_removal.md` (left Blocked, never implemented). Distinct from `implementations/20260827-112854_15_docs_05_agent_08_03_configuration-tools-memory.md.md`, which fixes an unrelated section of this same file.
- **Generated at**: 20260827-133325
- **Related target files**: `docs/05_agent_08_03_configuration-tools-memory.md`
