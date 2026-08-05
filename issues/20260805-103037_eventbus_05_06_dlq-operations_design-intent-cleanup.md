# Reduce implementation-derived detail in docs/06_eventbus_05_06_dlq-operations.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_05_06_dlq-operations.md`: keep the inline-promotion-vs-background-sweep role split and requeue caveats; remove full log-message quotes and duplicated interval-value explanations.

## Reason for Change
This chapter is the canonical source for DLQ operations (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: DLQ運用 = `06_eventbus_05_06_dlq-operations`), but currently carries verbatim log messages and repeated interval-value explanations already covered elsewhere.

## Implementation Intent
Keep this chapter focused on what a nonzero sweep count means operationally, and that requeue does not reset the failure count and may immediately return to DLQ.

## Target Files or Areas
`docs/06_eventbus_05_06_dlq-operations.md`

## Required Changes
- Keep: what DLQ file creation signifies, the role split between inline promotion and background sweep, what should be investigated when the sweep count is nonzero, that requeue does not reset the failure count, the condition under which a requeued event immediately returns to DLQ, that DLQ monitoring requires log analysis.
- Remove or compress: full log-message quotes, repeated explanation of fine values like the 60-second interval, mechanical usage instructions for the endpoint.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No full log-message quote or duplicated interval-value explanation remains.
- The requeue-does-not-reset-failure-count caveat and immediate-re-DLQ condition remain explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `dlq.py`) — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_05_06_dlq-operations」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_05_06_dlq-operations」
- Generated at: 2026-08-05
