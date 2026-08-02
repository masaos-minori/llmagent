# Document the RAG/Agent responsibility boundary (docs/04_mcp_05_04 and related)

## Priority
High

## Summary
This review identifies the RAG/Agent responsibility boundary as the single most important undocumented viewpoint in the MCP domain: nowhere is it explicitly stated that `RagPipeline` implements core logic while the Agent layer, in production, must call it only through `rag-pipeline-mcp` (the HTTP boundary) — nor whether any direct-import path from Agent code to `RagPipeline` is test/dev-only or actually reachable in production.

## Reason for Change
Without this boundary being explicit, an implementer could add a production code path that imports `RagPipeline` directly, bypassing the MCP boundary's access control, audit logging, and health-gating — silently reintroducing a responsibility-boundary violation that the architecture is designed to prevent.

## Implementation Intent
Add an explicit "RAG and Agent Responsibility Boundary" statement (either as a new subsection in `docs/04_mcp_05_04_mdq-rag-boundary.md` or a new dedicated file, per this review's own reconstruction policy) stating: `RagPipeline` implements core logic; production-path Agent code must call it only via `rag-pipeline-mcp`; any direct-import path is test/dev-only. Confirm whether direct import is only a convention or actually enforced (e.g. via lint-imports or an architecture boundary rule) before asserting it as an absolute prohibition.

## Target Files or Areas
`docs/04_mcp_05_04_mdq-rag-boundary.md` (or a new dedicated file if this review's authors decide the topic warrants one)

## Required Changes
- Add a "RAG and Agent Responsibility Boundary" section describing: `RagPipeline` (core logic) vs. `rag-pipeline-mcp` (production HTTP boundary that Agent code must use).
- Investigate whether direct `RagPipeline` imports from Agent code exist anywhere in current production code paths, or are confined to tests/dev tooling.
- Investigate whether this boundary is enforced by any architectural mechanism (e.g. `lint-imports`/import-linter contract) or is purely a convention; state whichever is confirmed, and register as Needs Confirmation if the enforcement status can't be determined.

## Acceptance Criteria
The RAG/Agent responsibility boundary is explicitly documented in at least one canonical location; the direct-import question (test/dev-only vs. production-reachable) is either confirmed and stated, or explicitly tracked as Needs Confirmation.

## Testing Expectations
Not required (documentation-only). Manually verify via `grep -rn "RagPipeline" scripts/agent/` and by checking `import-linter`/`lint-imports` contract definitions for any RAG-related boundary rule before finalizing.

## Documentation Impact
`docs/04_mcp_05_04` (or a new file) gains this domain's most important missing design-intent section.

## Out of Scope
Do not add an architectural enforcement mechanism (e.g. a new `lint-imports` contract) in this issue if one does not already exist — documentation only; if enforcement is found to be missing, note that as a separate follow-up concern rather than implementing it here.

## AI Implementation Instruction
This is the highest-value documentation gap identified in the entire MCP review — verify both the direct-import question and the enforcement-mechanism question via actual source/config inspection rather than asserting either as fact without checking.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 item 12, 再構成の基本方針 item 3), §4 強化候補 (RAGとAgentの責務境界)
- Generated at: 2026-08-02
