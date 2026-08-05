# Reduce implementation-derived detail in docs/06_eventbus_01_system-overview.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_01_system-overview.md`: keep the purpose, publish/subscribe/replay/ack/nack/DLQ overview, Agent-independence, and the security model (no-auth premise, network-boundary protection); remove internal data structures and implementation values.

## Reason for Change
This chapter is the canonical source for overall scope and the security model (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: 全体像・対象範囲・セキュリティモデル = `06_eventbus_01_system-overview`). The no-auth premise and network-boundary protection judgment are security-critical and must not be diluted while trimming implementation detail like `EventBroker` internals and queue maxsize values.

## Implementation Intent
Keep this chapter as the canonical source for Event Bus's purpose, its independence from the Agent runtime, and its security model. Explicitly preserve: Agent integration is intentionally not yet implemented, and why.

## Target Files or Areas
`docs/06_eventbus_01_system-overview.md`

## Required Changes
- Keep: Event Bus's purpose, the publish/subscribe/replay/ack/nack/DLQ overview, that Event Bus is independent from the Agent runtime, that Agent integration is intentionally unimplemented at this time, the security model, the no-auth premise and its operational risk, the network-boundary-protection judgment, the SQLite-vs-in-memory-broker role split.
- Remove or compress: `EventBroker`'s internal data structures, fine implementation values like queue maxsize, internal shutdown-sentinel mechanics, a plain enumeration of future auth options — but keep that auth is currently unimplemented and that a threat-model evaluation would be needed before adding it.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No `EventBroker` internal-structure description or queue-maxsize value remains.
- The no-auth premise, network-boundary-protection judgment, and Agent-integration-unimplemented statement remain explicit and are not weakened during trimming.

## Testing Expectations
Not required for behavior (documentation-only), but review must explicitly confirm the security-model statements (no-auth premise, network boundary, Agent-integration status) were not silently dropped. No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches security-model documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_01_system-overview」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). When in doubt whether a detail is security-relevant, keep it. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_01_system-overview」
- Generated at: 2026-08-05
