## Goal

Replace the "unresolved, tracked as NC-023" sentence in the Software Runtime Dependency Graph section with the confirmed wrapper-relationship statement (REQ-001).

## Scope

In scope: the one sentence citing NC-023 in the "Not represented as an edge" paragraph. Out of scope: any other part of the Software Runtime Dependency Graph section.

## Assumptions

N/A: none — the confirmed relationship (Plan's Problem section) is settled evidence, not an assumption.

## Design decisions

State the relationship as confirmed fact, replacing the "unresolved" framing entirely rather than appending a correction alongside the old question.

## Alternatives considered

Appending a "Resolved:" note after the existing sentence instead of replacing it: rejected — leaves the stale "unresolved... tracked as NC-023" claim readable, which is misleading once NC-023 is removed from the inventory (row 2 of this Plan).

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

1. Re-confirm the current wording at the "Not represented as an edge" paragraph (confirmed present, unchanged, at line 469-473 as of this cycle) immediately before editing.
2. Replace "Whether `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/` are the same or a different RAG implementation is unresolved and tracked as `NC-023`." with a sentence stating the confirmed relationship: `scripts/mcp_servers/rag_pipeline/` is an MCP-facing wrapper around `scripts/rag/`'s `RagPipeline` (confirmed via `rag_pipeline_service.py::RagPipelineMCPService.start()`'s direct import/instantiation of it, and confirmation that no other file under `scripts/mcp_servers/rag_pipeline/` duplicates RAG pipeline logic), reachable via the existing `Agent → MCP` edge with no separate node or edge needed.

### Method

Single-sentence replacement in an existing paragraph.

### Details

- Confirmed current text (re-verified this cycle, line 469-473): "Not represented as an edge: no direct RAG ↔ Agent call path exists in current source (`scripts/agent/` contains no import of `scripts/rag/`) — RAG-related functionality, if any, is reached only through the generic `Agent → MCP` edge above. Whether `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/` are the same or a different RAG implementation is unresolved and tracked as `NC-023`."
- Only the final sentence changes; the preceding sentences about the RAG↔Agent non-edge remain accurate and unchanged.

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the prior sentence.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Automated | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py` | Pass, no new findings |

## Completion criteria

- The section no longer describes the relationship as undetermined or references NC-023 (AC-1).

## Out of scope

- Any other section of this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-154441 | 20260927-154441 | Re-confirmed at Step 4a: sentence now at lines 476-480 (shifted from cited 469-473 by an unrelated concurrent edit elsewhere in the same doc); content unchanged. Confirmed via Read: `rag_pipeline_service.py::RagPipelineMCPService.start()` does `from rag.pipeline import RagPipeline` and instantiates it; no other file under `scripts/mcp_servers/rag_pipeline/` duplicates pipeline logic |
| 2 | Add or update tests per Validation plan | Completed | 20260927-154441 | 20260927-154441 | N/A: documentation-only, automated checks per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-154441 | 20260927-154441 | N/A: documentation-only; docs checkers run instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-154441 | 20260927-154441 | N/A: this document's own target file IS the documentation being updated |

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
- **Source issue**: issues/done/20260927-115727_nc023_determine-rag-implementation-relationship-for-dependency-graph.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121302_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124333
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
