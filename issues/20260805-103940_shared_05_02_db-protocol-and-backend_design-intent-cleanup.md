# Reduce implementation-derived detail in docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md`: keep the Protocol-based abstraction intent and the store-vs-agent-side responsibility split; remove full method/class enumerations.

## Reason for Change
This chapter is the canonical source for store Protocol/backend boundaries (per `memo-doc-shared-review.md` §「章間の正本ルール」: store protocol / backend境界 = `90_shared_05_02_db_api_and_operations-protocol-and-backend`), but currently carries Protocol method lists and backend class enumerations that duplicate the code.

## Implementation Intent
Keep this chapter focused on why Protocol is used, why `SQLiteSessionStore` is a thin adapter while `SessionMessageRepository` holds semantics, and why `MemoryStore` lives on the agent/memory side rather than in `db/`.

## Target Files or Areas
`docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md`

## Required Changes
- Keep: the intent behind using Protocol, the design of abstracting the SQLite implementation to leave room for a future alternate backend, that `SQLiteSessionStore` is a thin DB adapter while `SessionMessageRepository` holds the semantics, that message role validation/content normalization/JSON encode-decode are the agent side's responsibility, that `MemoryDeleteStore` is the boundary for safely handling cross-table deletion, that `MemoryStore` lives on the agent/memory side and not in `db/`.
- Remove or compress: a full Protocol method list, an embedding-helper function list, a SQLite backend class list, `MemoryStore`'s method table, detailed SQL-operation explanations.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No full Protocol method list or backend class list remains.
- The thin-adapter-vs-semantics-owner split (`SQLiteSessionStore` vs. `SessionMessageRepository`) and the `MemoryStore`-lives-outside-db/ boundary remain explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/db/` (including `store_protocols.py`) or the agent-side `MemoryStore` implementation.

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_05_02_db_api_and_operations-protocol-and-backend」. Do not edit code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_05_02_db_api_and_operations-protocol-and-backend」
- Generated at: 2026-08-05
