# EventBus role/consumer-identity authorization never actually runs

## Priority
High

## Summary
EventBus's role-based route authorization (`require_role`) and per-consumer
topic authorization (`require_consumer_identity`) are wired as FastAPI
`Depends(...)` defaults on functions that are never invoked through FastAPI's
dependency-injection system, so their checks never execute. Any caller
holding the single configured Bearer token can currently reach every
endpoint (publish, subscribe, ack, nack, dlq list/requeue, replay)
regardless of the route's declared required role or the consumer's allowed
topics.

## Background
`scripts/eventbus/app.py` registers one FastAPI route per endpoint
(`@app.get("/dlq")`, `@app.get("/subscribe")`, etc.), but each registered
handler is a thin wrapper that delegates to the real logic in
`scripts/eventbus/dlq_route.py`, `subscribe_route.py`, `ack_route.py`, and
`replay_route.py` via a plain `await` call (e.g. `return await
subscribe_route(request, topic=topic, since_seq=since_seq,
consumer_id=consumer_id)`). Those delegated-to functions are the ones
carrying the `Depends(require_role(...))` / `Depends(require_consumer_identity)`
parameters — not the `@app.get/post`-registered wrapper functions.

## Problem
Because the wrapper functions in `app.py` are what FastAPI actually resolves
dependencies for, and they don't declare `Depends(require_role(...))` /
`Depends(require_consumer_identity)` themselves, the delegated-to functions'
`Depends(...)`-defaulted parameters are never resolved by FastAPI at all.
When called as plain functions, Python simply uses each parameter's literal
default value — the un-evaluated `Depends(...)` marker object itself (or, if
no default was given, a `TypeError` for a missing argument). Either way, the
authorization function's body (`require_role`'s `_check_role` closure,
`require_consumer_identity`) never runs.

Independently of the wiring gap, `require_role`'s own check is a tautology:
`_check_role` compares the endpoint's own hardcoded `role` argument (e.g.
`Role.OPERATOR`, fixed at the `Depends(require_role(Role.OPERATOR))`
call site) against `_ROUTE_ROLE_MAP[path]` (also a hardcoded set for that
same path) — it never inspects the caller's token, session, or any other
identity signal to determine what role the caller actually holds. There is
no code anywhere that maps a caller's Bearer token to a `Role`.

`require_consumer_identity` compounds this: its return type is `None`
(nothing is returned on the success path), but `subscribe_route.py`'s
`subscribe()` does `_identity.get("topics", set())` on its result, assuming
a `dict`. Even in a hypothetical world where FastAPI did resolve this
dependency correctly, the call would raise `AttributeError: 'NoneType'
object has no attribute 'get'`.

Finally, `scripts/eventbus/auth.py`'s module-level `_TOKEN_CONSUMER_MAP` and
`_TOKEN_TOPIC_MAP` dicts — which `require_consumer_identity` reads to decide
whether a token may use a given `consumer_id`/topic — are initialized empty
and are never populated from `EventBusConfig`, any config file, or any other
source.

## Reason for Change
This is security-sensitive: the route-role map
(`scripts/eventbus/auth.py::_ROUTE_ROLE_MAP`) documents an intended
access-control boundary (only `Role.OPERATOR` callers should reach `/dlq`,
`/dlq/requeue`, `/replay`; only `Role.PUBLISHER` should reach `/publish`;
only `Role.CONSUMER` should reach `/subscribe`/`/ack`/`/nack`), but none of
it is enforced. Any caller with the single shared `auth_token` currently has
full access to every endpoint. This also crashes 2 tests outright
(`AttributeError` from the `None`-vs-`dict` mismatch) whenever a test
actually reaches the code path that would depend on
`require_consumer_identity`.

## Implementation Intent
This issue is intentionally left as an investigation record, not an
implementation plan — the actual fix requires product/security design
decisions this issue does not make:
- How should a caller's role actually be determined? (per-role tokens in
  config, a claims-bearing token format, a separate identity store, etc.)
- Should `require_role`/`require_consumer_identity` be re-architected to be
  declared directly on the `@app.get/post`-registered wrapper functions in
  `app.py` (so FastAPI's DI actually runs them), or should `app.py`'s
  wrappers call them explicitly as plain awaited functions instead of
  relying on `Depends(...)` defaults?
- What should `require_consumer_identity` actually return, and how should
  `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP` be populated (from
  `EventBusConfig`, a separate config file, or another source)?

## Target Files or Areas
- `scripts/eventbus/app.py` (all `@app.get/post` wrapper endpoints)
- `scripts/eventbus/auth.py` (`require_role`, `require_consumer_identity`,
  `_ROUTE_ROLE_MAP`, `_TOKEN_CONSUMER_MAP`, `_TOKEN_TOPIC_MAP`)
- `scripts/eventbus/dlq_route.py`, `subscribe_route.py`, `ack_route.py`,
  `replay_route.py` (the `Depends(...)`-defaulted parameters that are never
  resolved)
- `scripts/eventbus/config.py` (`EventBusConfig` — likely needs new fields
  if a token-to-role/consumer mapping is added here)
- `tests/eventbus/test_eventbus_auth.py`,
  `tests/eventbus/test_eventbus_subscribe.py` (tests that currently crash or
  would need to change once real enforcement exists)

## Required Changes
Not specified — see Implementation Intent; this issue records the problem
and defers the design decision.

## Constraints
Any fix must not break the existing single-shared-token deployment model
unless a migration path is also designed (config files, deployment docs,
and any operational tooling currently assume one `auth_token` per
`EventBusConfig`).

## Acceptance Criteria
- A caller holding a token that should only have `Role.CONSUMER` access
  cannot successfully call `/dlq`, `/dlq/requeue`, `/replay`, or `/publish`.
- A caller subscribing with a `consumer_id`/topic combination it is not
  authorized for is rejected (403), not silently allowed.
- `require_consumer_identity`'s return contract matches what its callers
  actually expect (no `AttributeError` on the success path).
- The two tests referenced in Problem no longer need to be skipped.

## Testing Expectations
Unit tests per fixed component (role mapping resolution, consumer identity
resolution) plus integration tests hitting each role-gated endpoint with a
token that should and should not be authorized, once the design is decided.

## Documentation Impact
Once fixed, update whichever `docs/06_eventbus_*` file documents
authentication/authorization to describe the real mechanism (current docs
may already describe the intended `_ROUTE_ROLE_MAP` design without noting
it isn't enforced — verify and correct during implementation).

## Out of Scope
- Changing the Bearer-token presence/validity check itself
  (`verify_bearer_token`, `attach_auth_middleware`) — that part does work
  and is out of scope for this issue.
- Any other MCP server's `attach_auth_middleware` usage
  (`scripts/mcp_servers/*`) — this issue is scoped to `scripts/eventbus/`
  only; whether the same wrapper-delegation pattern affects those servers
  was not investigated here.

## Dependencies
N/A: none

## Unresolved Questions
- Is a per-role/per-consumer token scheme, a claims-based token, or a
  separate identity store the intended direction? Needs a product decision
  before implementation.
- Were `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP` meant to be populated from a
  config file that doesn't exist yet, or is this dead scaffolding from an
  earlier, since-abandoned design? Needs confirmation before implementation.

## AI Implementation Instruction
Do not implement a fix without first getting explicit confirmation on the
Unresolved Questions above — this issue documents a discovered gap, not an
approved design. When implementation is authorized, read
`scripts/eventbus/app.py`, `auth.py`, and all four route modules in full
before changing anything, and re-verify this issue's claims against the
code's current state (it may have changed since this issue was filed).

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260911-133957
- **Related target files**: scripts/eventbus/app.py, scripts/eventbus/auth.py, scripts/eventbus/dlq_route.py, scripts/eventbus/subscribe_route.py, scripts/eventbus/ack_route.py, scripts/eventbus/replay_route.py, scripts/eventbus/config.py, tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_eventbus_subscribe.py
