# EventBus `require_consumer_identity` dependency's `consumer_id` has no default, breaking consumer_id-optional endpoints

## Priority
High

## Summary
`scripts/eventbus/auth.py`'s `require_consumer_identity()` FastAPI dependency declares
`consumer_id: str` with no default. Every endpoint that depends on it
(`/subscribe`, `/events/{event_id}/ack`, `/nack`) separately declares its own
`consumer_id: str = Query(default="")` to make the parameter optional, but FastAPI
resolves a `Depends()` callable's parameters independently of the endpoint's own
declaration — the endpoint-level default does not propagate to the dependency, so
`consumer_id` remains a mandatory query parameter on all three endpoints regardless of
the endpoint's own declaration.

## Background
N/A: covered by Summary

## Problem
Confirmed by direct inspection of the resolved FastAPI route `dependant` objects (`uv
run python` against `eventbus.app.app.routes`): for all three affected routes, the
top-level query parameter `consumer_id` has `default=""` as expected, but the
`require_consumer_identity` dependency's own `consumer_id` parameter reports
`default=PydanticUndefined` (i.e. required) in every case. `/nack` was given its own
`consumer_id: str = Query(default="")` declaration in a prior fix attempt on the
(incorrect) assumption that an endpoint-level default would be shared with the
dependency's same-named parameter — verified here to not be the case; that endpoint's
declaration alone does not fix the underlying issue.

## Reason for Change
Confirmed by repository evidence: a request to any of the three affected endpoints
without a `consumer_id` query parameter is rejected with `422 {'detail': [{'type':
'missing', 'loc': ['query', 'consumer_id'], ...}]}` before the endpoint's own handler
logic (which is written to tolerate an empty/absent `consumer_id`, per
`require_consumer_identity`'s own `if consumer_id and consumer_id not in ...` guard)
ever runs. This breaks any legitimate consumer-less use of ack/nack/subscribe (e.g. a
caller that does not track per-consumer offsets), which the endpoint-level default
values were clearly intended to support.

## Implementation Intent
Give `require_consumer_identity`'s own `consumer_id` parameter a default value
(`consumer_id: str = ""`) directly on the dependency function, matching what its
internal logic already assumes (`if consumer_id and ...`) and what all three call
sites' own declarations already assume. This is a single-parameter change in one
function that fixes all three affected endpoints at once, since they all depend on
the same function.

## Target Files or Areas
- `scripts/eventbus/auth.py` (`require_consumer_identity()`)

## Required Changes
- Add `= ""` as the default for `require_consumer_identity`'s `consumer_id`
  parameter.
- Re-verify (via the same route-inspection approach used to confirm this bug) that
  `consumer_id` is now optional on all three dependent routes.

## Constraints
Do not change `require_consumer_identity`'s authorization logic itself (the
allowlist check) — only its parameter's default value.

## Acceptance Criteria
- A request to `/nack`, `/events/{event_id}/ack`, or `/subscribe` with no
  `consumer_id` query parameter no longer returns 422 for a missing-parameter reason.
- Existing consumer_id-provided call paths (allowlist enforcement, offset tracking)
  are unaffected.

## Testing Expectations
Run the ack/nack/subscribe test files under `tests/eventbus/` after this fix and
after Issue eb001 (the `/events/{event_id}/ack` routing fix) is also applied — several
tests currently fail on the eb001 routing bug before this one is even reached, so this
issue's fix cannot be fully verified against `/events/{event_id}/ack` in isolation.
`/nack`'s own tests can verify this fix independently of eb001.

## Documentation Impact
N/A: internal dependency-parameter fix; no operational or API-contract documentation
depends on this default value being explicit.

## Out of Scope
- The `/events/{event_id}/ack` `_ROUTE_ROLE_MAP` routing issue (tracked separately as
  eb001) — this issue's fix alone will not make ack tests pass while that routing bug
  remains.
- The per-role token validation issue (tracked separately as eb002).
- The `_dlq_loop` shutdown/segfault issue (tracked separately as eb003).

## Dependencies
Verification against `/events/{event_id}/ack` depends on eb001 (the `_ROUTE_ROLE_MAP`
fix) also being applied — that routing bug currently returns 403 before this
dependency's own behavior can be observed on that endpoint. `/nack` and `/subscribe`
have no such blocking dependency.

## Unresolved Questions
N/A: none — the fix and its scope are established by direct route inspection.

## AI Implementation Instruction
Change only `require_consumer_identity`'s `consumer_id` default in
`scripts/eventbus/auth.py`. Do not modify the auth route map, per-role token
validation, or `_dlq_loop` — each has its own tracked issue. Verify the fix using the
same FastAPI route-`dependant` inspection technique described in Problem above (not
only end-to-end HTTP tests, since `/events/{event_id}/ack` is also blocked by eb001
independently of this fix).

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-093611
- **Related target files**: scripts/eventbus/auth.py
