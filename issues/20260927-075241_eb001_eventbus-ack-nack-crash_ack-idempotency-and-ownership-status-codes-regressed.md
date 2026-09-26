# EventBus ack nack crash_ack idempotency and ownership status codes regressed

## Priority
High

## Summary
The eventbus ack/nack HTTP endpoints no longer return the expected 403 (ownership violation) / 409 (conflict/already-processed) status codes for already-acked, already-owned-by-another-consumer, or crash-before-ack scenarios — several tests observe 200 (success) or 404 (not found) instead.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
Observed mismatches:
- `tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_principal_ownership_validation`: expected 200 in (403, 409), unclear which — needs re-check of exact assertion.
- `test_ack_event_delivery_verification`: `assert 200 == 409`
- `test_ack_event_not_found`: `assert 404 == 409`
- `tests/eventbus/test_eventbus_ack_nack.py::TestAckHttpBehavior::test_ack_unknown_event_returns_404`: `assert 404 == 409`
- `TestNackEvent::test_nack_event_not_found`: `assert 200 == 409`
- `TestNackEvent::test_nack_event_principal_ownership_validation`: `assert 200 in (403, 409)`
- `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_crash_ack_event_delivery_verification`: `assert 200 == 409`
- `TestCrashBeforeAck::test_crash_ack_principal_ownership_validation`: `assert 200 in (403, 409)`

This is a consistent pattern: the endpoint accepts operations (200) or reports not-found (404) where the tests expect a conflict/forbidden response (409/403), across ack, nack, and crash-recovery-ack scenarios.

## Reason for Change
If genuine, this is a correctness/security regression in event-ownership and idempotency enforcement for the eventbus's ack/nack HTTP surface — a consumer could ack/nack an event it does not own, or double-process an already-acked event, both of which the tests assert should be rejected.

## Implementation Intent
Read the current ack/nack endpoint handlers (likely `scripts/eventbus/routes.py` or similar) to determine current status-code branching for: (a) event not found, (b) event already acked/nacked, (c) requester does not own the event. Compare against each failing test's exact scenario setup to confirm whether the test's expectation or the handler's current behavior is correct, then align the losing side.

## Target Files or Areas
- EventBus HTTP route handlers for ack/nack (confirm exact path under `scripts/eventbus/`)
- `tests/eventbus/test_eventbus_ack_endpoint.py`
- `tests/eventbus/test_eventbus_ack_nack.py`
- `tests/eventbus/test_eventbus_crash_ack.py`

## Required Changes
- Read current ack/nack/crash-ack handler status-code logic.
- For each failing test, determine whether the handler's current status code or the test's expected status code reflects the intended contract.
- Apply the fix to whichever side is wrong; if the handler is wrong, restore the correct 403/409 branching.

## Constraints
Preserve backward-compatible response shape for already-passing ack/nack scenarios; do not broaden 409/403 responses to cases that should legitimately succeed.

## Acceptance Criteria
- All 8 listed tests pass.
- Ownership/idempotency semantics for ack/nack/crash-ack are each covered by at least one passing test that exercises the rejection path.

## Testing Expectations
Run the 3 affected test files; run full suite once after the fix.

## Documentation Impact
If handler behavior changes, update the eventbus ack/nack endpoint documentation (`docs/24_eventbus/eventbus_15_ack_nack_endpoints.md` — confirm exact path) to match (Needs confirmation on exact doc file).

## Out of Scope
- `eb002` (NackResult tuple-equality failures in the same test files) — tracked separately since it is a distinct type-contract issue, not a status-code issue.
- Other unrelated failing tests from the same full-suite run.

## Dependencies
Related to `eb002` (same test files, different root cause) — investigate together but fix/track separately.

## Unresolved Questions
Needs confirmation: exact current handler source location and whether the regression is in the handler or the tests reflect an intentionally changed contract.

## AI Implementation Instruction
Read the current ack/nack/crash-ack handler source and at least 3 of the 8 failing test bodies before deciding the fix direction. Do not assume the handler is wrong — some tests may assert an outdated expectation. Fix only the confirmed-wrong side per test.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/eventbus/test_eventbus_ack_endpoint.py, tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_crash_ack.py
