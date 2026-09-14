# Update the EventBus API reference for current endpoint contracts

## Priority
Low

## Summary
Replay pagination, health responses, DLQ responses, and per-endpoint role requirements are not currently consolidated in one client-facing API reference; this issue documents them and updates `EVENTBUS-003`'s dual-DLQ-promotion-path note to reflect only the remaining documentation gap.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` `EVENTBUS-003` ("Dual Path for DLQ Promotion Undocumented") already tracks the immediate-vs-recovery-sweep DLQ promotion documentation gap this issue also addresses.

## Problem
Clients and operators currently cannot use the EventBus HTTP API's replay, health, and DLQ endpoints without reading source code, since their response formats, pagination, status codes, and role requirements are not consolidated into one reference document.

## Reason for Change
Replay pagination, health responses, DLQ responses, and role requirements belong in one client-facing API reference.

## Implementation Intent
Allow clients and operators to use the API without reading source code, documenting endpoint role requirements only after `eventbus02`/`eventbus03`'s authorization corrections have landed so the documented roles reflect the corrected model.

## Target Files or Areas
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/app.py`
- `scripts/eventbus/dlq.py`
- `docs/eventbus`
- `scripts/eventbus/health_route.py`
- `scripts/eventbus/replay_route.py`
- `scripts/eventbus/dlq_route.py`

## Required Changes
- Document the immediate and recovery promotion paths.
- Define idempotency and race behavior when both paths observe the same event.
- Update `EVENTBUS-003` to describe only the remaining documentation gap.
- Document health status codes and degraded reasons.
- Document replay SSE and JSON formats.
- Document DLQ list pagination and requeue response fields.
- Document endpoint role requirements after authorization is corrected.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- Operators can distinguish inline promotion from orphan recovery.
- The documented state transitions match implementation tests.
- Concurrent execution does not produce duplicate DLQ state.
- The API reference matches the implemented schemas and status codes.
- Examples do not contain credentials or environment-specific secrets.
- Documentation checks validate referenced endpoint paths.

## Testing Expectations
Not required for the documentation content itself; confirm documentation checks (referenced endpoint paths, examples) pass, and rely on `eventbus02`/`eventbus03`/`eventbus06`'s own test coverage for the behavior being documented.

## Documentation Impact
This issue's entire scope is `docs/eventbus`'s API reference content (replay, health, DLQ, role requirements) and updating `EVENTBUS-003`'s governance entry once the dual-path behavior is documented.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
Depends on `eventbus02`/`eventbus03` (for accurate role requirements) and `eventbus06` (for the DLQ requeue response contract) having landed before their respective sections are documented; the health and replay-format sections can be written independently.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Keep changes scoped to `docs/eventbus` API reference content and `EVENTBUS-003`'s governance entry; do not modify route handler code as part of this issue. Do not document endpoint role requirements until `eventbus02`/`eventbus03` have landed — write that section last, or mark it pending if written earlier. Ensure no credentials or environment-specific secrets appear in any example.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102632
- **Related target files**: scripts/eventbus/ack_route.py, scripts/eventbus/app.py, scripts/eventbus/dlq.py, docs/eventbus, scripts/eventbus/health_route.py, scripts/eventbus/replay_route.py, scripts/eventbus/dlq_route.py
