# Reduce implementation-derived detail in docs/90_shared_01_03_overview-constraints-and-reference.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_01_03_overview-constraints-and-reference.md`: keep import-direction constraints and cross-cutting rules (JSON/httpx/logging-language/SQLite WAL, SecurityProfile/ProductionConfigValidator); remove overly fine constraint-value tables and DB-table enumerations.

## Reason for Change
This chapter is the canonical source for import constraints and cross-cutting rules (per `memo-doc-shared-review.md` §「章間の正本ルール」: import制約・横断制約 = `90_shared_01_03_overview-constraints-and-reference`). The import-direction rule enforced by `lint-imports` is a hard architectural boundary and must remain explicit.

## Implementation Intent
Keep this chapter focused on import-direction constraints, that they are enforced by import-linter, shared/db-common critical constraints, and the operational meaning of `SecurityProfile`/`ProductionConfigValidator`.

## Target Files or Areas
`docs/90_shared_01_03_overview-constraints-and-reference.md`

## Required Changes
- Keep: import-direction constraints, that import-linter enforces them, the overall picture of persistent DBs, cross-cutting constraints (JSON/orjson, httpx, English-only logging, SQLite WAL), the operational meaning of `SecurityProfile`/`ProductionConfigValidator`.
- Remove or compress: overly fine constraint-value tables, an AI-reference-guide question table, a mechanical DB-table enumeration, duplicated Related Documents/Keywords.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No overly fine constraint-value table, question table, or mechanical DB-table enumeration remains.
- Import-direction constraints and their `lint-imports` enforcement remain explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm import-direction constraints were not weakened — these are enforced by `PYTHONPATH=scripts uv run lint-imports` per `rules/toolchain.md`. No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but is architecturally significant — treat removal decisions conservatively.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/shared/` or `scripts/db/`, and the `lint-imports` contract definition itself.

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_01_03_overview-constraints-and-reference」. Do not edit code or the import-linter contract. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_01_03_overview-constraints-and-reference」
- Generated at: 2026-08-05
