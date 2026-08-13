# Reduce implementation-derived detail in docs/06_eventbus_02_05_failure-behavior-summary.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_02_05_failure-behavior-summary.md`: keep the failure-priority ordering (SQLite commit / JSONL archive / broker notify / consumer replay / DLQ promotion) and its operational implications; remove HTTP-status mapping tables and file-based justification notes.

## Reason for Change
This chapter is the canonical source for operational failure judgment (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: 失敗時の運用判断 = `06_eventbus_02_05_failure-behavior-summary`). The failure-priority ordering directly determines what an operator should conclude from a given failure and must remain intact.

## Implementation Intent
Keep this chapter focused on what is prioritized on failure and the operational consequences (JSONL-only failure after successful publish, event drops for slow consumers, degraded health as an alert signal, 409 on requeue).

## Target Files or Areas
`docs/06_eventbus_02_05_failure-behavior-summary.md`

## Required Changes
- Keep: the failure priority order (SQLite commit, JSONL archive, broker notification, consumer replay, DLQ promotion), that JSONL alone can fail after a successful publish, that slow consumers can experience event drops, that degraded health should be used as an operational alert, the meaning of a 409 on requeue.
- Remove or compress: mechanical HTTP-status-to-response mapping tables, file-name-based justification notes, a plain error-code enumeration.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No mechanical HTTP-status mapping table or plain error-code list remains.
- The failure-priority ordering and its operational implications remain explicit.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the failure-priority ordering was not altered or lost. No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but is operationally sensitive (failure-response runbook content) — treat removal decisions conservatively.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_02_05_failure-behavior-summary」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_02_05_failure-behavior-summary」
- Generated at: 2026-08-05
