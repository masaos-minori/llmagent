## Goal
Add an explicit distinction between `ToolExecutor.server_configs` (current, active
MCP execution configuration) and `ToolRouteResolver`'s removed `server_configs`
argument to `docs/04_mcp_03_01_dispatch-and-routing.md`, which currently documents
`ToolRouteResolver`/`RuntimeToolRegistry`/static-`ToolRegistry` responsibilities
accurately but does not mention `ToolExecutor.server_configs` at all.

## Scope
- **In-Scope**: `docs/04_mcp_03_01_dispatch-and-routing.md`'s `## ToolRouteResolver`
  section only — adding the `ToolExecutor.server_configs`-vs.-removed-argument
  distinction.
- **Out-of-Scope**: `docs/05_agent_13_reference-api.md` (seq 01 of this Plan); this
  file's existing constructor example (`resolver = ToolRouteResolver()` /
  `resolver.set_runtime_registry(registry)` / `resolver.resolve(...)`), already
  corrected by DOC-001 and not re-edited here; `docs/04_mcp_90_inconsistencies_and_known_issues.md`
  / REQ-006 — Obsolete per this Plan's 2026-09-03 correction (file no longer
  exists).

## Assumptions
- `scripts/shared/tool_executor.py`'s `ToolExecutor.__init__()` accepts
  `server_configs: dict[str, McpServerConfig]` and stores it as
  `self._server_configs`, used at line 62 (`self._server_configs.get(server_key)`)
  — re-verified 2026-09-03 by direct `Read` of `scripts/shared/tool_executor.py:43-62`,
  matching the Plan's own evidence with no drift.
- `docs/04_mcp_03_01_dispatch-and-routing.md` currently contains zero mentions of
  `server_configs` or `ToolExecutor.server_configs` specifically — re-verified
  2026-09-03 by direct `grep`, matching the Plan's own evidence with no drift.
- The file is 14211 bytes as of 2026-09-03, well under
  `tools/check_docs_structure.py`'s `MAX_SIZE` (24576, raised 2026-09-03 under a
  separate Plan — see `implementations/done/20260903-142052_01_...md`) — no size
  concern for this row's small addition.

## Design decisions
- **Insert the new distinction as a paragraph within the existing
  `## ToolRouteResolver` section**, immediately after its code example and before
  the unrelated "Four-layer responsibility of MDQ tool definitions" subsection —
  this keeps the new content adjacent to the exact resolver constructor it
  contrasts against, rather than in a new top-level section that would separate
  the two things being distinguished.
- **State the distinction as prose, not a table**, since it is a single
  contrastive statement (one component's field vs. another component's removed
  argument), not a multi-row enumeration — matching this section's existing mix of
  prose and tables (the tool-set-to-server-key table above it is a genuine
  enumeration; this is not).

## Alternatives considered
- **Add the distinction to a new `## ToolExecutor` subsection instead of within
  `## ToolRouteResolver`** — rejected: this document does not currently have a
  dedicated `## ToolExecutor` section (`ToolExecutor` is mentioned only in the
  dispatch-flow diagram and lifecycle overview); creating one would be a larger
  structural addition than REQ-005 calls for, when the contrast is naturally
  anchored to the `ToolRouteResolver` section this Plan is already correcting the
  false claim about (the removed constructor argument).
- **Cross-reference `docs/05_agent_13_reference-api.md`'s corrected Configuration
  line instead of restating the parameter list here** — considered, rejected: this
  document's own established pattern (e.g., the tool-set table, the MDQ four-layer
  table) is to be self-contained for the concepts it documents rather than
  requiring a reader to jump to the Agent reference doc for a one-sentence
  contrast; a link is added in addition to, not instead of, the inline statement.

## Implementation
### Target file
`docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure
1. Re-read `## ToolRouteResolver` (lines 85-126) in full immediately before
   editing to reconfirm no drift (done above; confirmed identical to the Plan's
   citation).
2. Insert the new distinction paragraph immediately after the closing ` ``` ` of
   the `resolver = ToolRouteResolver()` code example (line 108) and before
   `**Four-layer responsibility of MDQ tool definitions:**` (line 110).

### Method
Direct text edit (e.g. via the `Edit` tool) inserting the new paragraph at the
anchor point in Details below.

### Details

Before:
```
resolver = ToolRouteResolver()
resolver.set_runtime_registry(registry)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

**Four-layer responsibility of MDQ tool definitions:**
```

After:
```
resolver = ToolRouteResolver()
resolver.set_runtime_registry(registry)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

**Not to be confused with `ToolExecutor.server_configs`:** `ToolRouteResolver`'s constructor has no `server_configs` parameter — it accepts only `warn_on_missing`, `strict_mode`, and `runtime_registry` (see [Agent Reference API](05_agent_13_reference-api.md) for the full parameter list). `ToolExecutor.server_configs` (`shared/tool_executor.py`) is a separate, current, active configuration: a `dict[str, McpServerConfig]` used for MCP server transport and startup-mode checks (`self._server_configs.get(server_key)`), unrelated to tool-name routing.

**Four-layer responsibility of MDQ tool definitions:**
```

## Compatibility considerations
No other document links to `## ToolRouteResolver` by anchor in a way this
insertion would disturb (the paragraph is inserted within the section, not
replacing or moving its heading). Independent of seq 01 — this row can be applied
in any order relative to it.

## Security considerations
None — documentation-only addition of a component-responsibility distinction; no
code, credentials, or access-control content is affected.

## Rollback considerations
Single-file, single-insertion change to a Markdown document under version control;
revert via `git revert`. No other file references this new paragraph yet, so
rollback carries no cross-file follow-up.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/04_mcp_03_01_dispatch-and-routing.md | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors |
| docs/04_mcp_03_01_dispatch-and-routing.md | Domain consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | No new port/tool/link drift findings; the new `[Agent Reference API](05_agent_13_reference-api.md)` link resolves |
| docs/04_mcp_03_01_dispatch-and-routing.md | Manual cross-check | Re-read the new paragraph | `ToolExecutor.server_configs` is clearly distinguished from the removed resolver argument |

## Completion criteria
- `docs/04_mcp_03_01_dispatch-and-routing.md` explicitly distinguishes
  `ToolExecutor.server_configs` from the removed `ToolRouteResolver.server_configs`
  argument (AC-2, REQ-005).
- `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_consistency.py --domain mcp` report no new errors.

## Out of scope
`docs/05_agent_13_reference-api.md` (seq 01 of this Plan) — has its own
implementation-procedure document per this Plan's Implementation Target Files
table. `docs/04_mcp_90_inconsistencies_and_known_issues.md` / REQ-006 — Obsolete
per this Plan's 2026-09-03 correction (file no longer exists).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Re-verified lines 100-112 before editing — no drift. Inserted the distinction paragraph exactly as designed. |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | `check_docs_quality.py`: 0 errors, 1 pre-existing unrelated warning. `check_docs_consistency.py --domain mcp`: no finding mentions this file. `check_docs_structure.py docs/04_mcp_03_01_dispatch-and-routing.md`: All checks passed (new `[Agent Reference API](05_agent_13_reference-api.md)` link resolves). Diff confirmed scoped to exactly the 2 inserted lines. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903 | 20260903 | N/A: no `docs/00_index.md` task-scope mapping applies |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260902-143330_toolroutedoc_correct_tool_routing_docs_remove_obsolete_compat_claims.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-090104_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-151738
- **Related target files**: docs/04_mcp_03_01_dispatch-and-routing.md
