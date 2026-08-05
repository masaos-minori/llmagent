# Reduce implementation-derived detail in docs/90_shared_01_01_overview-purpose-and-scope.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_01_01_overview-purpose-and-scope.md`: keep the shared/db purpose, scope, and out-of-scope boundary; remove exhaustive module-name listings.

## Reason for Change
This chapter is the canonical source for shared/db's overall scope (per `memo-doc-shared-review.md` §「章間の正本ルール」: 全体像・対象範囲 = `90_shared_01_01_overview-purpose-and-scope`), but currently carries full module-name enumerations for `shared/` and `db/` that duplicate what a directory listing already shows.

## Implementation Intent
Keep this chapter focused on why shared/ and db/ exist, their high-level roles (common foundation vs. persistence foundation), the upper/lower layer boundary, and what is explicitly out of scope (MCP, RAG pipeline, Agent REPL, external LLM/embedding servers).

## Target Files or Areas
`docs/90_shared_01_01_overview-purpose-and-scope.md`

## Required Changes
- Keep: the purpose of the shared/db layer, in-scope/out-of-scope boundary, the shared/-as-common-foundation vs. db/-as-persistence-foundation role split, the boundary with upper layers, that MCP/RAG pipeline/Agent REPL/external LLM/embedding servers are out of scope.
- Remove or compress: a full module-name list under `shared/`, a full module-name list under `db/`, an exhaustive individual-file-name enumeration, a plain list of type/DTO names.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No full module/file-name enumeration remains.
- The out-of-scope boundary (MCP/RAG/Agent REPL/external servers) remains explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/shared/` or `scripts/db/`.

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_01_01_overview-purpose-and-scope」. Do not edit code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_01_01_overview-purpose-and-scope」
- Generated at: 2026-08-05
