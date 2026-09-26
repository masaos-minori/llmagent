# EventBus DLQ endpoint returns 422 for all requests

## Priority
High

## Summary
All 4 tests in `tests/eventbus/test_eventbus_dlq.py` receive HTTP 422 (Unprocessable Entity) regardless of their expected status code (200, 404, or 409), suggesting a request-schema validation failure at the FastAPI/pydantic layer before the DLQ handler logic even runs.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
- `test_inline_dlq_promotion_not_found`: `assert 422 == 404`
- `test_inline_dlq_promotion_on_nack`: `assert 422 == 200`
- `test_inline_dlq_promotion_skipped_below_threshold`: `assert 422 == 200`
- `test_nack_on_already_dlq_event_does_not_repromote`: `assert 422 == 409`

The uniform 422 across all four, despite differing expected codes, strongly suggests a single shared cause: a request body/model change (e.g. a new required field, changed field type) on the DLQ-related request schema(s) these tests post, rather than four independent handler bugs.

## Reason for Change
A blanket 422 means the DLQ inline-promotion code path is not being reached/tested at all currently — a meaningful gap in coverage for dead-letter-queue promotion behavior (nack-triggered promotion, threshold-based skip, re-promotion guard).

## Implementation Intent
Identify the exact FastAPI endpoint(s) and Pydantic request model(s) these 4 tests post to. Diff the model's current required fields against what the tests send. Determine whether the model gained a new required field (fix: update tests to send it) or the tests were already sending a field the model no longer accepts under a different name (fix: align naming).

## Target Files or Areas
- EventBus DLQ route/request-model module (confirm exact path under `scripts/eventbus/`)
- `tests/eventbus/test_eventbus_dlq.py`

## Required Changes
- Capture the actual 422 validation error detail (not just the status code) for at least one of the 4 failing tests to identify the missing/mismatched field.
- Update the tests' request payloads (or the model, if the tests reflect the intended contract) accordingly.

## Constraints
Do not relax request validation to accept a payload shape the production system should reject — confirm the correct schema before choosing which side to fix.

## Acceptance Criteria
- All 4 listed tests pass with their originally-expected status codes (404, 200, 200, 409 respectively).

## Testing Expectations
Run `tests/eventbus/test_eventbus_dlq.py`; run full suite once after the fix.

## Documentation Impact
If the request schema's required fields changed, update any eventbus DLQ endpoint documentation describing its request body (confirm exact doc path, e.g. `docs/24_eventbus/eventbus_05_dlq_endpoint.md`).

## Out of Scope
Other unrelated eventbus failing tests from the same full-suite run (tracked as separate issues, e.g. eb001, eb002, eb004-eb007).

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: the exact 422 validation error detail (which field is missing/invalid) — must be captured with `-vv` or by inspecting the response body directly, since the current investigation only captured the status code.

## AI Implementation Instruction
First reproduce one failing test with full response-body output (e.g. print `resp.json()` on 422) to see the actual validation error detail before deciding the fix. Do not guess the missing field.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/eventbus/test_eventbus_dlq.py
