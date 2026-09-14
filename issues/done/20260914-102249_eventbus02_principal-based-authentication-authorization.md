# Implement principal-based authentication and role authorization

## Priority
High

## Summary
EventBus authentication currently resolves roles/tokens in a way that is split between middleware and per-endpoint dependencies, permitting inconsistent authorization decisions; this issue consolidates credential resolution into one typed principal used uniformly for every endpoint's authorization decision.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` EVENTBUS-008 ("No Production Authentication Model for Event Bus HTTP API") states no authentication middleware is implemented, while `scripts/eventbus/auth.py` already defines a `Role` enum, a route-to-role map, and per-role token maps — this issue's own scope (and issue `eventbus10`, filed in this same batch) exists in part to reconcile that apparent discrepancy once the principal model below is implemented and verified.

## Problem
Authentication, per-role tokens, route authorization, and end-to-end authorization verification are currently split across middleware and per-endpoint dependencies in `scripts/eventbus/auth.py` and `scripts/eventbus/app.py`, with no single typed principal object carrying resolved roles/identity through the request. This permits the middleware and a dependency to reach different authorization conclusions for the same request.

## Reason for Change
Authentication, per-role tokens, route authorization, and end-to-end authorization verification are one security boundary. The current split design permits inconsistent decisions between middleware and dependencies.

## Implementation Intent
Resolve each credential to one typed principal and use that principal for every endpoint authorization decision. Choose one authentication authority for the whole EventBus process rather than duplicating the check between middleware and dependencies.

## Target Files or Areas
- `scripts/eventbus/auth.py`
- `scripts/eventbus/app.py`
- `tests/eventbus/test_eventbus_auth.py`
- `scripts/eventbus/config.py`
- `config/eventbus.toml`
- `tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_crash_ack.py` (Unknown: source review cited a `test_eventbus_ack.py` file that does not exist under `tests/eventbus/`; these three existing ACK-related test files are the likely intended targets — confirm exact file(s) before implementation)
- `tests/eventbus/test_eventbus_subscribe.py`

## Required Changes
- Introduce an authenticated principal containing roles, allowed consumer IDs, allowed topics, and a non-secret token identifier or fingerprint.
- Resolve the principal from the presented token.
- Compare the endpoint's required role with the principal's roles.
- Return HTTP 401 for unknown tokens and HTTP 403 for insufficient roles.
- Choose one authentication authority for all EventBus requests.
- Accept configured per-role tokens and map them to principals.
- Remove duplicate authentication checks between middleware and dependencies, or make the middleware populate the principal for dependencies.
- Define and document the compatibility behavior of `auth_token`.
- Remove string-prefix route authorization where the endpoint dependency already declares the required role.
- If route metadata is required, use the FastAPI route name or path template.
- Add authorization tests for routes containing path parameters.
- Create end-to-end tests using the actual FastAPI application and configured role tokens.
- Cover authentication, role checks, consumer identity, topic restrictions, and dynamic routes.
- Verify that authorization failures occur before persistent state changes.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- Publisher, consumer, operator, and monitoring tokens can access only their authorized endpoints.
- A valid token with the wrong role receives HTTP 403.
- An unknown or missing token receives HTTP 401.
- Raw token values are never logged.
- Every configured per-role token can authenticate successfully.
- Authentication is performed once per request.
- The same unauthorized-response contract is used on all endpoints.
- Backward compatibility for `auth_token` is explicitly tested or removed.
- A consumer principal can ACK through `/events/{event_id}/ack`.
- A non-consumer principal receives HTTP 403.
- Unknown routes remain denied.
- Tests include dynamic event IDs.
- Every consumer operation has positive and negative authorization cases.
- No unauthorized request changes events, deliveries, offsets, retries, or DLQ state.
- Tests execute through the public HTTP routes rather than calling handlers directly.

## Testing Expectations
Add or update unit, integration, and regression tests for all affected boundaries (see Acceptance Criteria); tests must execute through the public HTTP routes rather than calling handlers directly. Run the relevant test suites, static analysis, and type checks.

## Documentation Impact
Update active design documents and the known-issue inventory (including `EVENTBUS-008`'s description of the authentication model) only after implementation evidence is available.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
Issues `eventbus03` (consumer/topic authorization), `eventbus05` (audit logging), and `eventbus09` (config validation/role-token policy) build on the principal introduced here; `eventbus10` (ADR/known-issue reconciliation) depends on this issue's outcome to correct `EVENTBUS-008`'s description.

## Unresolved Questions
Whether `test_eventbus_ack.py` (cited in the source review) refers to one of the three existing ACK-related test files (`test_eventbus_ack_endpoint.py`, `test_eventbus_ack_nack.py`, `test_eventbus_crash_ack.py`) or a file that has not yet been created — confirm before adding tests there. Non-blocking: resolve during implementation by checking existing test coverage first.

## AI Implementation Instruction
Keep changes scoped to authentication/authorization resolution (`scripts/eventbus/auth.py`, `scripts/eventbus/app.py`) and directly-dependent config (`scripts/eventbus/config.py`, `config/eventbus.toml`); do not rewrite unrelated route handlers' business logic. Preserve existing public request/response shapes unless a fix explicitly requires a change. Confirm that failure paths do not expose credentials, tokens, payloads, or sensitive configuration. Do not update `EVENTBUS-008`'s governance entry as part of this issue — that correction belongs to `eventbus10`, once this issue's implementation is verified. Stop and report if the existing ACK test file naming is ambiguous rather than guessing which file to modify.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102249
- **Related target files**: scripts/eventbus/auth.py, scripts/eventbus/app.py, tests/eventbus/test_eventbus_auth.py, scripts/eventbus/config.py, config/eventbus.toml, tests/eventbus/test_eventbus_ack_endpoint.py, tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_subscribe.py
