# Reduce implementation-derived detail in docs/06_eventbus_05_04_consumer-id-stability.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_05_04_consumer-id-stability.md`: keep consumer_id stability requirements and collision risk; remove duplicated explanations and mechanical query-parameter framing.

## Reason for Change
This chapter is the canonical source for consumer_id stability (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: consumer_id安定性 = `06_eventbus_05_04_consumer-id-stability`), but currently repeats explanation already given in the subscribe/ack chapter and frames the requirement as a mechanical parameter description rather than an operational constraint.

## Implementation Intent
Keep this chapter focused on why consumer_id must be stable across restarts, why volatile IDs (e.g. PIDs) should not be used, and the collision risk when multiple consumers share an ID.

## Target Files or Areas
`docs/06_eventbus_05_04_consumer-id-stability.md`

## Required Changes
- Keep: that consumer_id must be managed stably by the client, that it is required for resuming replay after a restart, that volatile IDs like PIDs should not be used, that sharing the same ID across multiple consumers causes offset collisions, that the server does not detect collisions.
- Remove or compress: repeated explanation already covered in `06_eventbus_02_02_subscribe-ack`, mechanical framing of consumer_id as a query parameter.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No content duplicates `06_eventbus_02_02_subscribe-ack` verbatim; overlapping detail is replaced with a cross-reference per the canonical-source rule.
- The stability requirement, PID-avoidance guidance, and collision risk remain explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated eventbus docs-consistency script exists; manually check internal links, especially the new cross-reference to `06_eventbus_02_02_subscribe-ack`.

## Documentation Impact
Coordinate with the `06_eventbus_02_02_subscribe-ack` cleanup issue to avoid re-duplicating consumer_id explanation across both chapters after editing.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_05_04_consumer-id-stability」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Check `06_eventbus_02_02_subscribe-ack` for overlapping content and cross-reference rather than duplicate. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_05_04_consumer-id-stability」
- Generated at: 2026-08-05
