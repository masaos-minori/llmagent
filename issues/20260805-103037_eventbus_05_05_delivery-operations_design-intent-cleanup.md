# Reduce implementation-derived detail in docs/06_eventbus_05_05_delivery-operations.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_05_05_delivery-operations.md`: keep the operational actions for slow-consumer detection and replay recovery; remove curl/jq command examples and latency-estimate detail.

## Reason for Change
This chapter is the canonical source for delivery operations (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: delivery運用 = `06_eventbus_05_05_delivery-operations`), but currently carries command examples and timing estimates that are environment-specific and will go stale.

## Implementation Intent
Keep this chapter focused on the purpose of live-delivery verification, the operational action to take after detecting a slow consumer, and the reconnect-with-stable-consumer_id guidance.

## Target Files or Areas
`docs/06_eventbus_05_05_delivery-operations.md`

## Required Changes
- Keep: the purpose of verifying live delivery, the operational action after a slow consumer is detected, that a queue drop should be recovered via replay, that reconnection should use a stable consumer_id, that events are still persisted to SQLite even with zero subscribers.
- Remove or compress: detailed curl command examples, jq command examples, localhost millisecond-level timing estimates, a plain enumeration of simple verification commands.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No curl/jq command example or environment-specific timing estimate remains.
- Slow-consumer operational response and the SQLite-persists-even-with-zero-subscribers fact remain explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_05_05_delivery-operations」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_05_05_delivery-operations」
- Generated at: 2026-08-05
