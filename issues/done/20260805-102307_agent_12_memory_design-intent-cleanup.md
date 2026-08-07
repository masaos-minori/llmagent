# Reduce implementation-derived detail in docs/05_agent_12_*_memory*.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the memory chapter (overview-and-modes parts 1-2, gate-data-model-search parts 1-2, module-ref core-and-store, retrieval-and-injection, extraction-and-facade, ops-and-scoring): keep mode/fallback/boundary judgments and scoring's operational meaning; remove dataclass/enum/API lists and scoring formulas.

## Reason for Change
This chapter is the canonical source for the memory-layer's optional/degraded-mode design and RAG boundary, but currently also carries full dataclass/enum/store-API lists, retriever/ingestion/extraction function lists, and scoring-formula detail that belongs in code.

## Implementation Intent
Keep this chapter as the canonical source for memory-layer design intent (per `memo-doc-agent-review.md` §「章間の正本ルール」: メモリレイヤー = `05_agent_12_memory`). Search-quality judgment tied to scores may be kept, but the formulas/constants themselves must be delegated to code.

## Target Files or Areas
- `docs/05_agent_12_01_memory-overview-and-modes-part1.md`
- `docs/05_agent_12_01_memory-overview-and-modes-part2.md`
- `docs/05_agent_12_02_memory-gate-data-model-search-part1.md`
- `docs/05_agent_12_02_memory-gate-data-model-search-part2.md`
- `docs/05_agent_12_03_memory-module-ref-core-and-store.md`
- `docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `docs/05_agent_12_06_memory-module-ref-ops-and-scoring.md`

## Required Changes
- Keep: why the memory layer is optional, the operational meaning of hybrid / fts-only / degraded / disabled modes, the relationship between JSONL and SQLite storage, the fallback policy when embedding is unavailable, memory injection's effect on answer quality and associated cautions, the memory-vs-RAG responsibility boundary.
- Remove or compress: memory dataclass/enum/store-API lists, retriever/ingestion/extraction function lists, per-`source_type` mechanical field tables, scoring-formula detail and constant tables.
- Where scoring is discussed, keep only the operational meaning needed for search-quality judgment; delegate the formula itself to code.

## Acceptance Criteria
- All eight files follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No dataclass/enum/store-API list or scoring-formula/constant table remains.
- Mode semantics (hybrid/fts-only/degraded/disabled) and the embedding-unavailable fallback policy remain explicit.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- The memory/RAG code implementing scoring itself.

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_12_memory」 including its 注意 note: keep score-meaning relevant to search-quality judgment, delegate the formula/constants to code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_12_memory」
- Generated at: 2026-08-05
