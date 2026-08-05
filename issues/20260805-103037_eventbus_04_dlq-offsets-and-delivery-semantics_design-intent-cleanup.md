# Reduce implementation-derived detail in docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`: keep the at-least-once delivery guarantee, consumer_id stability requirements, and offset-monotonicity limitation; remove file-sanitization and physical-format detail.

## Reason for Change
This chapter is the canonical source for delivery semantics and consumer responsibility (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: delivery semantics と consumer責務 = `06_eventbus_04_dlq_offsets_and_delivery_semantics`). These are the constraints a consumer implementer must design around, so they must remain explicit and precise.

## Implementation Intent
Keep this chapter focused on why delivery is at-least-once (not exactly-once), why consumers must be idempotent, consumer_id stability/collision risk, and offset/DLQ-requeue caveats.

## Target Files or Areas
`docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

## Required Changes
- Keep: that the delivery guarantee is at-least-once and not exactly-once, why duplicate delivery can occur, that consumers must assume idempotent processing, consumer_id stability requirements, the risk of consumer_id collisions, that offset only advances via ack, the known limitation that ack-offset monotonicity is not guaranteed, DLQ requeue caveats, the reliability role split between JSONL/SQLite/DLQ files.
- Remove or compress: fine character-replacement rules for offset-directory filename sanitization, the physical format of offset files, a mechanical delivery-guarantee-table explanation, detailed history of `offset_checkpoint_interval` — but keep that a removed setting causes startup failure.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No filename-sanitization rule or physical-offset-file-format detail remains.
- At-least-once delivery, consumer idempotency requirement, and offset-monotonicity limitation remain explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm delivery-semantics constraints were not weakened. No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches delivery-guarantee documentation that consumer implementers rely on — treat removal decisions conservatively.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `offsets.py`, `dlq.py`) — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_04_dlq_offsets_and_delivery_semantics」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_04_dlq_offsets_and_delivery_semantics」
- Generated at: 2026-08-05
