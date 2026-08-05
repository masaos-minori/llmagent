# Reduce implementation-derived detail in docs/06_eventbus_03_persistence_schema_and_replay.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_03_persistence_schema_and_replay.md`: keep SQLite-as-source-of-truth and JSONL-as-auxiliary-archive judgments; remove full DDL, column lists, and index inventories.

## Reason for Change
This chapter is the canonical source for persistence and source-of-truth judgment (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: 永続化と正本データ = `06_eventbus_03_persistence_schema_and_replay`). Which store is authoritative (SQLite, not JSONL) is a correctness-critical fact referenced by recovery/query procedures elsewhere and must not be lost.

## Implementation Intent
Keep this chapter focused on why SQLite is the source of truth, why JSONL is auxiliary only, the WAL rationale, and the shared-connection/lock-serialization safety reasoning.

## Target Files or Areas
`docs/06_eventbus_03_persistence_schema_and_replay.md`

## Required Changes
- Keep: that SQLite is the source-of-truth store, that JSONL is an auxiliary archive and not the source of truth for query/recovery, the intent behind using WAL, the safety reasoning behind shared-connection-plus-lock serialization, that replay originates from SQLite, the basic migration policy for existing DBs, a brief note that `retry_count` was removed for lacking meaningful data.
- Remove or compress: full DDL text, column-list tables, complete index inventories, `ALTER TABLE` detail, implementation branching in `open_db()`/`_init_schema()`, content directly visible in `schema.sql`.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No full DDL, column-list table, or index inventory remains; readers are pointed to `schema.sql` for exact schema.
- The SQLite-source-of-truth / JSONL-auxiliary distinction remains explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the SQLite-vs-JSONL source-of-truth statement was not weakened. No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches data-integrity-critical documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `db.py`, `schema.sql`) — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_03_persistence_schema_and_replay」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Point to `schema.sql` for exact column/index detail rather than transcribing it. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_03_persistence_schema_and_replay」
- Generated at: 2026-08-05
