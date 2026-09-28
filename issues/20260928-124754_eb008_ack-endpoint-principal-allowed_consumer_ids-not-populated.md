# EventBus ack endpoint: principal allowed_consumer_ids not populated at request time

## Priority
High

## Summary
`tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_principal_ownership_validation` fails: an ACK request with a `consumer_id` not owned by the calling principal returns `200` instead of the expected `403`/`409`, because the resolved `Principal.allowed_consumer_ids` is `None` at the ownership-check call site, not the fixture's configured `frozenset({"consumer-A"})`.

## Background
Discovered during the post-docs-reorg full-suite validation re-check (`implementations/20260925-111411_04_tests___full_suite_.md`, Execution Status Step 3). A prior run of this same procedure (20260927) filed `eb001`-`eb007` for a cluster of eventbus ack/nack/dlq/auth failures, all since resolved (`issues/done/`); a re-run today found 4 remaining failures, of which this is one — likely a residual gap in the same area, not yet covered by those fixes.

## Problem
`scripts/eventbus/ack_route.py:52-60`'s ownership check is:
```python
if (
    _principal
    and _principal.allowed_consumer_ids
    and consumer_id not in _principal.allowed_consumer_ids
):
    raise HTTPException(status_code=403, ...)
```
The test's `principal_client` fixture configures the token->principal mapping with `allowed_consumer_ids=frozenset({"consumer-A"})` (`tests/eventbus/test_eventbus_ack_endpoint.py:73`), and calls `/events/{event_id}/ack` with `consumer_id="unauthorized-consumer"`. The captured debug log at request time shows the actual resolved principal as `Principal(roles=frozenset({<Role.CONSUMER: 'consumer'>}), allowed_consumer_ids=None, allowed_topics=None, token_fingerprint='1e3e678043777287')` — `allowed_consumer_ids` is `None`, so the `and _principal.allowed_consumer_ids` condition is falsy and the whole ownership check is skipped, returning `200` instead of `403`.

## Reason for Change
This is an authorization bypass: a consumer-scoped token is meant to be restricted to its mapped `consumer_id`(s), but the restriction is silently not enforced when `allowed_consumer_ids` fails to populate on the resolved principal, letting any consumer_id be acked/nacked with a valid token regardless of ownership.

## Implementation Intent
Trace how `_principal` is resolved for the `/events/{event_id}/ack` route (the auth dependency / token-to-`Principal` mapping, likely near `_TOKEN_CONSUMER_MAP` or equivalent) and confirm why `allowed_consumer_ids` does not carry through to the `Principal` instance `_do_ack` receives, despite the token being configured with an owned consumer set in the test fixture.

## Target Files or Areas
- `scripts/eventbus/ack_route.py` (`_do_ack`, ownership check at line ~52-60)
- EventBus auth/principal-resolution dependency (confirm exact path — the token→`Principal` mapping consumed by the `/ack` route)
- `tests/eventbus/test_eventbus_ack_endpoint.py` (`principal_client` fixture, line ~73)

## Required Changes
- Confirm the exact code path populating `Principal.allowed_consumer_ids` from the token map for this route, and why it resolves to `None` here.
- Fix the resolution so a consumer-scoped token's `allowed_consumer_ids` is correctly attached to the `Principal` used by `_do_ack`.

## Constraints
Must not change behavior for principals that are intentionally unrestricted (no consumer-id restriction configured) — only the case where a restriction is configured but not propagated.

## Acceptance Criteria
- The listed test passes (`403` returned for an unauthorized `consumer_id` when the principal's token is scoped to a different consumer).
- Other passing ack/nack tests in the same file remain passing.

## Testing Expectations
Run `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py -v`; run full suite once after the fix.

## Documentation Impact
If the principal-resolution fix changes documented auth behavior, update the eventbus auth/authorization documentation (confirm exact path, e.g. under `docs/24_eventbus/`).

## Out of Scope
The other 3 failures found in the same full-suite re-check (docs-quality golden pairs, orchestrator config restore, ingestion embedding-failure test) — tracked as separate issues.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: whether this is a regression introduced while fixing `eb001`-`eb007`, or a pre-existing gap those fixes didn't cover.

## AI Implementation Instruction
This is an authorization-bypass bug (security-relevant) — root-cause the principal resolution rather than loosening the test's expected status codes to make it pass.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260928-124754
- **Related target files**: scripts/eventbus/ack_route.py, tests/eventbus/test_eventbus_ack_endpoint.py
