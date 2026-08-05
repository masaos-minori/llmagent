# Reduce implementation-derived detail in docs/06_eventbus_02_01_publish-replay.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_02_01_publish-replay.md`: keep publish idempotency and replay-source-of-truth judgments; remove full request/response JSON examples and JSON Schema field tables.

## Reason for Change
This chapter is the canonical source for publish/replay design intent (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: publish / replay の設計意図 = `06_eventbus_02_01_publish-replay`), but currently also carries full JSON examples, JSON Schema field tables, regexes, and parameter-validation detail that duplicate the schema/OpenAPI source.

## Implementation Intent
Keep this chapter focused on why publish is idempotent, why JSONL-append failure does not fail publish, and when to use SSE vs. JSON replay.

## Target Files or Areas
`docs/06_eventbus_02_01_publish-replay.md`

## Required Changes
- Keep: why publish is idempotent, the design decision that duplicate `event_id` is not redelivered, the priority between SQLite commit and JSONL append, why JSONL-append failure still counts as publish success, the rule that replay reads from SQLite as the source of truth, when to use SSE replay vs. JSON replay, the operational caveat that SSE replay is not suited to paginated continuation.
- Remove or compress: full request-body JSON examples, full JSON Schema field tables, regexes, full response-field enumerations, 422 validation detail, mechanical explanation of `limit`/`offset`/`format`.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No full JSON example, JSON Schema table, or regex remains.
- SSE-vs-JSON replay usage guidance remains explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `publish_route.py`, `replay_route.py`) — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_02_01_publish-replay」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Point to Reference API / OpenAPI schema for exact request/response shapes rather than transcribing them. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_02_01_publish-replay」
- Generated at: 2026-08-05
