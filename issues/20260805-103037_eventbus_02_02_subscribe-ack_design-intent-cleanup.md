# Reduce implementation-derived detail in docs/06_eventbus_02_02_subscribe-ack.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_02_02_subscribe-ack.md`: keep the ack-only offset model, at-least-once delivery, and known offset-monotonicity limitation; remove query-parameter and SSE-frame-format detail.

## Reason for Change
This chapter is the canonical source for subscribe/ack/offset design intent (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: subscribe / ack / offset の設計意図 = `06_eventbus_02_02_subscribe-ack`). The ack-only offset model, at-least-once guarantee, and non-monotonic-offset limitation are consumer-facing correctness constraints that must survive the cleanup intact.

## Implementation Intent
Keep this chapter focused on the replay+live-push hybrid model, the ack-only offset-advance rule, and consumer-side ordering/idempotency responsibilities.

## Target Files or Areas
`docs/06_eventbus_02_02_subscribe-ack.md`

## Required Changes
- Keep: why subscribe is a hybrid of replay and live push, the boundary at which replay switches to live push, the consumer_id-based reconnect-recovery model, that offset only advances on ack, the intent behind the ack-only offset model, at-least-once delivery and the possibility of duplicates, the known limitation that ack-offset monotonicity is not guaranteed, that consumers must ack in order, the drop+replay policy for slow consumers.
- Remove or compress: full query-parameter enumeration, SSE-frame-format detail, complete 200/404 response examples, mechanical explanation of fields like `already_acked`, detailed API history of the old `/ack` alias — but keep that it is removed and only the canonical path should be used.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No query-parameter table, SSE-frame-format detail, or full response example remains.
- The ack-only offset model, at-least-once guarantee, and non-monotonic-offset limitation remain explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the ack/offset/at-least-once constraints were not silently dropped. No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches delivery-semantics documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `subscribe_route.py`, `ack_route.py`) — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_02_02_subscribe-ack」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_02_02_subscribe-ack」
- Generated at: 2026-08-05
