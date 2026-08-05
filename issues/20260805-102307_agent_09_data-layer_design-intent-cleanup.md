# Reduce implementation-derived detail in docs/05_agent_09_*_data-layer*.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the data-layer chapter (session-db, access-patterns, indexing-boundaries): keep DB-ownership and boundary judgments; remove table/column lists, CRUD function lists, and raw SQL/DDL.

## Reason for Change
This chapter is the canonical source for DB responsibility boundaries, but currently also carries table lists, column enumerations, and SQL/DDL that duplicate `schema_sql.py` verbatim and will drift on any schema change.

## Implementation Intent
Keep this chapter as the canonical source for DB responsibility boundaries (per `memo-doc-agent-review.md` §「章間の正本ルール」: DB責務境界 = `05_agent_09_data-layer`).

## Target Files or Areas
- `docs/05_agent_09_01_data-layer-session-db.md`
- `docs/05_agent_09_02_data-layer-access-patterns.md`
- `docs/05_agent_09_03_data-layer-indexing-boundaries.md`

## Required Changes
- Keep: the responsibility boundary between `session.sqlite`/`workflow.sqlite`/`rag.sqlite`/`eventbus.sqlite`, which DB is the source of truth for what, which DBs the Agent may/may not touch directly, operational judgment for DB recreation/migration/recovery, `session_diagnostics`'s role, why workflow state lives in `workflow.sqlite`.
- Remove or compress: table lists, column lists, CRUD function lists, raw SQL/DDL, content that is directly visible in `schema_sql.py`.

## Acceptance Criteria
- All three files follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No table/column enumeration or raw SQL/DDL block remains; readers are pointed to `schema_sql.py` for exact schema.
- DB-boundary rules (which DB may be touched directly by the Agent) are stated explicitly as a constraint.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing (schema-drift check vs. `schema_sql.py`).

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters, especially `05_agent_04_state-and-persistence` (separate issue — avoid re-duplicating DB boundary text there; use a pointer instead).
- `schema_sql.py` itself (code, not documentation).

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_09_data-layer」. Check `05_agent_04_state-and-persistence` for overlapping content and replace duplication with a cross-reference per the canonical-source rule. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_09_data-layer」
- Generated at: 2026-08-05
