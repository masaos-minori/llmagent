# Determine RAG implementation relationship for dependency graph

## Priority
Medium

## Summary
Confirm the relationship between `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/`, and update `docs/00_governance/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph accordingly, closing Needs Confirmation item NC-023.

## Background
`docs/00_governance/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph notes that "Whether `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/` are the same or a different RAG implementation is unresolved and tracked as `NC-023`." NC-023 itself records this as not investigated (`plans/done/20260902-191512_plan.md` explicitly listed it Out-of-Scope).

## Problem
This issue's own investigation found evidence NC-023 did not have: `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py::RagPipelineMCPService.start()` (line 96-97) directly imports and instantiates `RagPipeline` from `scripts/rag/pipeline.py` (`from rag.pipeline import RagPipeline`, marked `# lazy: avoids circular import`). No other file under `scripts/mcp_servers/rag_pipeline/` imports from `scripts/rag/` or duplicates its logic — the remaining files (`rag_pipeline_models.py`, `rag_pipeline_server.py`, `rag_pipeline_tools.py`, `document_manager.py`) define MCP-facing models, the MCP server/tool registration, and a document-manager helper, none of which reimplement RAG pipeline logic. This strongly suggests `scripts/mcp_servers/rag_pipeline/` is an MCP-tool-facing wrapper around `scripts/rag/`'s `RagPipeline`, not an independent second implementation — but this issue's evidence-gathering was a quick pass, not an exhaustive review of every function in both packages.

## Reason for Change
Without confirming and documenting this relationship, the Software Runtime Dependency Graph's RAG node scope stays ambiguous, and no future edge involving RAG can be confirmed as direct-vs-indirect (e.g. whether `Agent → MCP` already implicitly covers RAG access, or whether a distinct `Agent → RAG` relationship needs its own edge).

## Implementation Intent
Confirm the wrapper relationship found above is complete (no independent RAG logic exists elsewhere in `scripts/mcp_servers/rag_pipeline/`), then update the Software Runtime Dependency Graph's documentation to state the relationship explicitly — e.g. a note that `scripts/mcp_servers/rag_pipeline/` is the MCP-facing wrapper for `scripts/rag/`'s implementation, reachable via the existing `Agent → MCP` edge, with no separate RAG runtime node needed.

## Target Files or Areas
- `scripts/rag/pipeline.py`
- `scripts/mcp_servers/rag_pipeline/` (all files, to confirm no independent logic exists beyond the wrapper)
- `docs/00_governance/governance_01_documentation-policy.md` (Software Runtime Dependency Graph section)

## Required Changes
- Complete the wrapper-relationship confirmation (review remaining logic in `scripts/mcp_servers/rag_pipeline/` beyond this issue's quick pass).
- Update the Software Runtime Dependency Graph's prose to state the confirmed relationship instead of leaving it as an open question.
- Remove NC-023 from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items once confirmed.

## Constraints
N/A: this is a documentation/confirmation task; no behavior change is expected.

## Acceptance Criteria
- The relationship between `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/` is confirmed with concrete evidence (import graph, function-level review) and documented.
- `docs/00_governance/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph section no longer describes this relationship as undetermined.
- NC-023 is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items.

## Testing Expectations
Not required: documentation/investigation task, no behavior change.

## Documentation Impact
Update `docs/00_governance/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph section to state the confirmed RAG/MCP relationship. Remove the NC-023 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` once resolved.

## Out of Scope
- Any refactor of `scripts/rag/` or `scripts/mcp_servers/rag_pipeline/` — this issue is investigation and documentation only.
- Changing the Software Runtime Dependency Graph's node set or edges beyond clarifying the RAG relationship.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none — this issue's own investigation already narrowed the question substantially; remaining work is confirming completeness and documenting the finding.

## AI Implementation Instruction
Verify this issue's preliminary finding (the wrapper relationship) against every file in `scripts/mcp_servers/rag_pipeline/`, not just `rag_pipeline_service.py`, before updating documentation — do not treat this issue's own quick evidence as sufficient confirmation on its own. If the review finds independent RAG logic this issue's evidence missed, correct the conclusion and report it rather than forcing the "wrapper" framing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-115727
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md, scripts/rag/pipeline.py, scripts/mcp_servers/rag_pipeline/
