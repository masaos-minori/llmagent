# Reduce implementation-derived detail in docs/90_shared_01_02_overview-layer-responsibilities.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_01_02_overview-layer-responsibilities.md`: keep the layer structure and shared/db-vs-agent/rag/mcp_servers responsibility boundary; remove per-module responsibility tables and per-file function/DTO descriptions.

## Reason for Change
This chapter is the canonical source for layer responsibility boundaries (per `memo-doc-shared-review.md` §「章間の正本ルール」: レイヤー責務境界 = `90_shared_01_02_overview-layer-responsibilities`). What belongs in shared/ vs. db/ vs. agent/ is an architectural boundary enforced elsewhere (`lint-imports`) and must not be diluted while trimming file-level detail.

## Implementation Intent
Keep this chapter focused on "what belongs to which layer's responsibility," per the memo's explicit 注意: file-to-function mapping belongs in Reference, not here.

## Target Files or Areas
`docs/90_shared_01_02_overview-layer-responsibilities.md`

## Required Changes
- Keep: the layer structure, the import-direction concept, the shared/-vs-db/ responsibility boundary, the relationship with agent/rag/mcp_servers, what should and should not live in shared/, what should live in db/ vs. the agent side.
- Remove or compress: per-module responsibility tables, per-file function/DTO descriptions, fine per-file explanations (e.g. `mcp_config.py`), a detailed enumeration of individual responsibilities like `tool_constants` or `llm_sse_stream`.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No per-module responsibility table or per-file function/DTO description remains.
- The shared/-vs-db/-vs-agent/-vs-rag/-vs-mcp_servers boundary remains explicit and precise.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the layer-boundary statements were not weakened — this chapter is the canonical reference for a boundary enforced by `lint-imports`. No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but is architecturally significant (import-boundary documentation) — treat removal decisions conservatively.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/shared/` or `scripts/db/`, and the `lint-imports` contract definition itself.

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_01_02_overview-layer-responsibilities」 including its 注意 note: describe "which layer owns what," not "which file has which function" (that belongs in Reference). Do not edit code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_01_02_overview-layer-responsibilities」
- Generated at: 2026-08-05
