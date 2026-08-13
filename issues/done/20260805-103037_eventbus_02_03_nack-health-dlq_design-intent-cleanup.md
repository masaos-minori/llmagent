# Reduce implementation-derived detail in docs/06_eventbus_02_03_nack-health-dlq.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_02_03_nack-health-dlq.md`: keep nack/DLQ-promotion judgment and `/health` degraded-monitoring guidance; remove response-field tables and internal reason-name inventories.

## Reason for Change
This chapter is the canonical source for nack/health/DLQ design intent (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: nack / health / DLQ の設計意図 = `06_eventbus_02_03_nack-health-dlq`). Health-degraded monitoring guidance and requeue semantics are operationally critical for incident response and must not be lost.

## Implementation Intent
Keep this chapter focused on nack-as-delivery-failure, the max_retry-to-DLQ promotion decision, the write-file-then-update-DB ordering rationale, `/health` degraded semantics, and requeue's non-reset-of-failure-count behavior.

## Target Files or Areas
`docs/06_eventbus_02_03_nack-health-dlq.md`

## Required Changes
- Keep: that nack represents a delivery failure, the decision to promote to DLQ at `max_retry`, the intent behind writing the file before updating the DB during DLQ promotion, the meaning of `/health` degraded, how `/health` should be used for operational monitoring, that requeue does not reset the failure count, that requeue is not a "second chance," that an event not in DLQ cannot be requeued.
- Remove or compress: full response JSON examples, DLQ-list response field enumeration, per-endpoint parameter tables, an exhaustive table of internal reason names like `broker_queue_backlog_high` — keep an operationally-relevant summary, detailed implementation function names.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No full response JSON example or exhaustive internal-reason-name table remains.
- `/health` degraded semantics and requeue's failure-count-non-reset behavior remain explicit.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm health/DLQ operational judgment was not silently dropped. No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches incident-response-relevant documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `dlq_route.py`, `health_route.py`) — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_02_03_nack-health-dlq」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_02_03_nack-health-dlq」
- Generated at: 2026-08-05
