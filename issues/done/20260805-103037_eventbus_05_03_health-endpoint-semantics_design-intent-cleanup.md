# Reduce implementation-derived detail in docs/06_eventbus_05_03_health-endpoint-semantics.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_05_03_health-endpoint-semantics.md`: keep the HTTP-status-as-primary-signal monitoring guidance and the meaning of degraded; remove full JSON body examples and internal key inventories.

## Reason for Change
This chapter is the canonical source for `/health` monitoring guidance (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: health監視 = `06_eventbus_05_03_health-endpoint-semantics`). Misreading `503 degraded` as "process down" instead of an operational warning is a documented misunderstanding risk that this chapter exists specifically to prevent.

## Implementation Intent
Keep this chapter focused on why HTTP status (not JSON body) should be the primary monitoring signal, what `ok`/`degraded` mean, and representative degraded causes to check.

## Target Files or Areas
`docs/06_eventbus_05_03_health-endpoint-semantics.md`

## Required Changes
- Keep: the `/health` monitoring policy, the meaning of `ok` and `degraded`, that HTTP 503 indicates a degraded state rather than the process being down, that monitoring tools should treat HTTP status as the primary signal, representative degraded causes to check (DB unavailable, DLQ task stopped, queue backlog, slow consumers).
- Remove or compress: a full JSON body example, a mechanical status-value table, an internal `degraded_reasons` key inventory.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No full JSON body example or internal-key inventory remains.
- The HTTP-status-as-primary-signal guidance and the 503-is-not-down clarification remain explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the "503 is degraded, not down" clarification was not lost — this is the specific misunderstanding this chapter is meant to prevent. No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but is monitoring-critical documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `health_route.py`) — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_05_03_health-endpoint-semantics」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_05_03_health-endpoint-semantics」
- Generated at: 2026-08-05
