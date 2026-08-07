# Reduce implementation-derived detail in docs/05_agent_04_*_state-and-persistence*.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the state-and-persistence chapter (state-model parts 1-2, history-compression, platform-databases): keep scope/ownership boundaries between session/turn/persistent state and between databases; remove full field lists and CRUD/DB-operation enumerations.

## Reason for Change
This chapter is the canonical source for state-and-persistence boundaries, but currently also carries `AgentContext`/`ConversationState`/`TurnState`/`RuntimeStats` full field lists, CRUD method lists, and table-column enumerations that are mechanically derivable from the schema/dataclass source and add drift risk without decision value.

## Implementation Intent
Keep this chapter as the canonical source for state/persistence boundaries (per `memo-doc-agent-review.md` §「章間の正本ルール」: 状態と永続化 = `05_agent_04_state-and-persistence`).

## Target Files or Areas
- `docs/05_agent_04_01_state-and-persistence-state-model-part1.md`
- `docs/05_agent_04_01_state-and-persistence-state-model-part2.md`
- `docs/05_agent_04_02_state-and-persistence-history-compression.md`
- `docs/05_agent_04_03_state-and-persistence-platform-databases.md`

## Required Changes
- Keep: session-scope / turn-scope / persistent-scope distinction, the relationship between `ctx.conv.history` and `session.sqlite`, why `session_diagnostics` is separated from `messages`, why `workflow.sqlite` is the source of truth for workflow state, the RAG-DB vs. memory-DB responsibility boundary, `/undo` caveats after compression, the policy against crossing DB boundaries with direct operations.
- Remove or compress: full field lists for `AgentContext`/`ConversationState`/`TurnState`/`RuntimeStats`, CRUD method lists, DB operation function lists, mechanical table-column enumerations, mechanical save/fetch/update descriptions.

## Acceptance Criteria
- All four files follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No full dataclass field list or CRUD/DB-function enumeration remains.
- The DB-boundary-crossing prohibition and `/undo`-after-compression caveat are stated explicitly as operational rules.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing (includes DB-schema-drift check vs. `schema_sql.py`).

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- `docs/05_agent_09_*` data-layer chapter (separate issue; do not merge DB-table detail there without checking for duplication).
- Code changes.

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_04_state-and-persistence」. Where content would duplicate `05_agent_09_data-layer`, prefer a pointer over re-explaining. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_04_state-and-persistence」
- Generated at: 2026-08-05
