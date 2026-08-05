# Reduce implementation-derived detail in docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`: keep migration-vs-recreation judgment criteria and single-node-SQLite scaling limits; remove migration internals and unverified numeric thresholds stated as fact.

## Reason for Change
This chapter is the canonical source for migration/scaling/schema-change policy (per `memo-doc-shared-review.md` §「章間の正本ルール」: migration / scaling / schema change方針 = `90_shared_04_03_db_architecture_and_schema-migration-and-scaling`). Whether a schema change requires migration or DB recreation is a decision with data-loss consequences and must remain clear and not overstated as precise fact where it is actually an estimate.

## Implementation Intent
Keep this chapter focused on schema init/migration policy, that rag/session/eventbus have no compatibility migration (recreate instead), that only `workflow.sqlite` has incremental migration, that `mdq.sqlite` has a separate legacy-schema auto-detection approach, and single-node scaling limits.

## Target Files or Areas
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

## Required Changes
- Keep: the schema-initialization-and-migration policy, that rag/session/eventbus have no compatibility migration, that only `workflow.sqlite` has incremental migration, that `mdq.sqlite` has a separate legacy-schema-detection mechanism, judgment criteria for schema changes, the data-loss risk when DB recreation is required, single-node SQLite's scaling limits, that stated thresholds are estimates requiring per-environment verification, a migration-warning-sign checklist.
- Remove or compress: internal migration-list names, `ALTER TABLE` detail, implementation detail like swallowing `duplicate column name` errors, RAG-consistency-function internal judgment formulas, an AI-reference table, an overly detailed canonical-source-list, numeric thresholds stated as definitive rather than as estimates.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No internal migration-list name, `ALTER TABLE` detail, or internal judgment formula remains.
- Numeric thresholds are explicitly framed as estimates requiring per-environment verification, not as definitive facts.
- The migration-vs-recreation judgment criteria and data-loss-risk warning remain explicit.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the migration-vs-recreation criteria and data-loss warnings were not weakened. No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches data-loss-risk-relevant documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/db/` (including `rag_consistency.py`).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_04_03_db_architecture_and_schema-migration-and-scaling」. Do not edit code. Frame numeric thresholds as estimates, not fact, per the memo's explicit instruction (しきい値は見積もりであり、環境ごとの検証が必要). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_04_03_db_architecture_and_schema-migration-and-scaling」
- Generated at: 2026-08-05
