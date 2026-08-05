# Reduce implementation-derived detail in docs/06_eventbus_02_04_dlq-background-loop.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_02_04_dlq-background-loop.md`: keep the safety-net framing of the DLQ background loop; remove SELECT/UPDATE detail and function-name explanations, moving the `promote_to_dlq()` production-path note to Known Issues or Reference API.

## Reason for Change
This chapter is the canonical source for the DLQ background loop's design rationale (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: DLQ background loop の考え方 = `06_eventbus_02_04_dlq-background-loop`). `memo-doc-eventbus-review.md` explicitly notes (§「注意」 for this chapter) that the `promote_to_dlq()` production-path detail belongs in Known Issues or Reference API, not in the design body.

## Implementation Intent
Keep this chapter focused on why the background loop is a safety net (not the primary path), what it detects, and why optimistic locking prevents double promotion.

## Target Files or Areas
`docs/06_eventbus_02_04_dlq-background-loop.md`

## Required Changes
- Keep: that the DLQ background loop is a safety net rather than the primary path, its purpose of detecting missed inline promotions or race conditions, why optimistic locking prevents double promotion, the operational meaning of a nonzero sweep count, that log monitoring is required.
- Remove or compress: SELECT/UPDATE condition detail, the `sweep_orphans()` function-name explanation, detailed call-site description of `promote_to_dlq()`, full log-message quotes, verbatim description of the two-path implementation.
- Move the note that `promote_to_dlq()` is not called from the production path to `docs/06_eventbus_90_inconsistencies_and_known_issues.md` or the Reference API chapter rather than keeping it here in detail.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No SELECT/UPDATE detail, function-name explanation, or verbatim log-message quote remains.
- The `promote_to_dlq()` production-path detail is relocated to Known Issues/Reference API rather than described in depth here.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated eventbus docs-consistency script exists; manually check internal links, especially the new cross-reference to Known Issues.

## Documentation Impact
Coordinate with the Known Issues cleanup issue (`docs/06_eventbus_90_inconsistencies_and_known_issues.md`) so the `promote_to_dlq()` note is not duplicated in both places — this chapter should link there instead of re-explaining.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `dlq.py`) — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_02_04_dlq-background-loop」 including its 注意 note on relocating the `promote_to_dlq()` detail. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_02_04_dlq-background-loop」
- Generated at: 2026-08-05
