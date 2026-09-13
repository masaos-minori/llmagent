# EventBus auth test fixture's local routes never declare `Depends(require_role(...))`, so role-based authorization is never actually tested

## Priority
High

## Summary
`tests/eventbus/test_eventbus_auth.py`'s `_make_test_app()` helper builds its own
local FastAPI app with its own route handlers (`@local_app.post("/publish")`, etc.)
that call the real route logic (`eb_app.publish_route(request)`, etc.) directly, but
— unlike `scripts/eventbus/app.py`'s real routes — never declare
`Depends(require_role(...))` or `Depends(require_consumer_identity)` on those local
handlers. Every "authorized role can do X" test in this file therefore only ever
exercised Bearer-token *authentication* (via `attach_auth_middleware`), never
role-based *authorization* — a caller holding any valid token (regardless of which
role it grants) could pass every test in this file that asserts a 200/success
response.

## Background
Discovered while adding a regression test for
`implementations/done/20260913-122501_05_scripts_eventbus_auth.py.md` (REQ-005/AC-4:
a `consumer_token` bearer must be rejected, not authorized, for a
`Role.PUBLISHER`-gated route like `/publish`). Attempting to add the missing
`Depends(require_role(...))` declarations directly to `_make_test_app()`'s local
routes (mirroring `scripts/eventbus/app.py`'s real routes exactly) surfaced this gap
immediately: several previously-`PASSED` tests (e.g.
`TestSubscribeAuth::test_subscribe_with_valid_consumer_token`) started failing with
403, because activating `require_consumer_identity`'s dependency chain for the first
time also activated the topic-allowlist check now tracked separately as `eb005`
(`_TOKEN_TOPIC_MAP` empty-set contradiction). The `Depends(...)` addition was
reverted for that reason (to avoid conflating two unrelated fixes in one change);
this issue tracks the missing-`Depends(...)` gap on its own.

## Problem
Confirmed by direct reading of `_make_test_app()` (all seven locally-registered
routes: `/publish`, `/subscribe`, `/dlq`, `/dlq/{event_id}/requeue`, `/replay`,
`/events/{event_id}/ack`, `/nack`) against the corresponding real routes in
`scripts/eventbus/app.py` (which do declare `_role: Role =
Depends(require_role(...))` and, where applicable, `_identity: dict[str, Any] =
Depends(require_consumer_identity)`) — none of the seven local handlers declare
either dependency. FastAPI only resolves a dependency that a route handler itself
declares; calling the delegated-to route function (e.g. `eb_app.publish_route(...)`)
directly does not retroactively invoke dependencies the *caller* never declared.

## Reason for Change
This test file's own docstring states its purpose is "Positive/negative
authorization tests for every EventBus route category," but with this gap, every
"positive" case (e.g. `test_publish_with_valid_publisher_token`,
`test_dlq_list_with_valid_operator_token`) would also pass if authenticated with a
token for a *different* role, or even the shared `auth_token`/`admin_token` — the
tests cannot currently distinguish "authorized for this specific role" from "merely
authenticated." This directly undermines confidence in `eb002`'s REQ-005 fix (making
per-role tokens actually enforce role-scoped access), since this file's own tests
would not have caught a regression in that enforcement.

## Implementation Intent
Add the missing `Depends(require_role(...))` (and `Depends(require_consumer_identity)`
where the real route also has it: `/subscribe`, `/events/{event_id}/ack`, `/nack`) to
each of `_make_test_app()`'s seven local route handlers, mirroring
`scripts/eventbus/app.py`'s real declarations exactly (same role per route). Land
this only after (or together with) `eb005`'s fix, since activating
`require_consumer_identity`'s dependency chain here will also activate the
topic-allowlist check `eb005` covers — this issue's own fix is not independently
testable against the `/subscribe`/`/events/{event_id}/ack`/`/nack` routes until that
one lands.

## Target Files or Areas
- `tests/eventbus/test_eventbus_auth.py` (`_make_test_app()`'s seven local route
  declarations)

## Required Changes
- Add `_role: Role = Depends(require_role(Role.<X>))` to each of the seven local
  routes, matching the role each corresponding real route in `scripts/eventbus/app.py`
  requires.
- Add `_identity: dict[str, Any] = Depends(require_consumer_identity)` to the three
  routes that need it (`/subscribe`, `/events/{event_id}/ack`, `/nack`), matching the
  real routes.
- Thread `_role`/`_identity` through to the delegated-to route function calls
  (`eb_app.publish_route(request, _role=_role)`, etc.), matching the real routes'
  call signature.
- After landing, add (or keep) at least one negative-direction test per role-gated
  route confirming a wrong-role token is rejected (403) — not only the existing
  "no token" (401) cases.

## Constraints
Do not change `scripts/eventbus/app.py`'s real routes, `_populate_token_maps`,
`require_role`, `require_consumer_identity`, or any other production authorization
code — this issue is a test-fixture-only fix. Do not land this independently of
`eb005` for the three consumer-identity routes; verify each affected existing test
individually rather than assuming which ones are affected.

## Acceptance Criteria
- Every one of `_make_test_app()`'s seven local routes declares the same
  `Depends(require_role(...))`/`Depends(require_consumer_identity)` as its real
  `scripts/eventbus/app.py` counterpart.
- A new test confirms a `consumer_token` bearer is rejected (403) from a
  `Role.PUBLISHER`-gated route through this fixture's own HTTP layer (not only via a
  unit-level `_check_role` call, which is how this gap's regression test was written
  as a stopgap in `implementations/done/20260913-122501_02_tests_eventbus_test_eventbus_auth.py.md`).
- All existing tests in this file that authenticate with a specific role's token
  still pass.

## Testing Expectations
- Run `tests/eventbus/test_eventbus_auth.py` in full after the change; every test
  must pass with the added `Depends(...)` in place.
- Run the full `tests/eventbus/` suite to confirm no regression.

## Documentation Impact
N/A: test-only fix; no operational or API-contract documentation depends on this
fixture's internal completeness.

## Out of Scope
- The topic-allowlist empty-set contradiction itself (tracked as `eb005`) — this
  issue only depends on it, does not fix it.
- Any change to `scripts/eventbus/app.py`'s real routes.

## Dependencies
Depends on `issues/20260913-143134_eb005_token-topic-map-empty-set-contradiction.md`
(`_TOKEN_TOPIC_MAP` empty-set contradiction) for the three routes that also declare
`Depends(require_consumer_identity)` (`/subscribe`, `/events/{event_id}/ack`,
`/nack`) — activating that dependency here surfaces that issue's bug in
currently-passing tests until it is fixed.

## Unresolved Questions
N/A: none — the gap and its fix are established by direct comparison against
`scripts/eventbus/app.py`'s real route declarations.

## AI Implementation Instruction
Read `scripts/eventbus/app.py`'s seven route declarations and
`tests/eventbus/test_eventbus_auth.py`'s `_make_test_app()` in full before changing
anything — confirm `eb005` is resolved first (or resolve it in the same session) for
the three consumer-identity routes, and re-verify this issue's claims against
current source, since it may have changed since filing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/done/20260913-122501_02_tests_eventbus_test_eventbus_auth.py.md
- **Generated at**: 20260913-143134
- **Related target files**: tests/eventbus/test_eventbus_auth.py
