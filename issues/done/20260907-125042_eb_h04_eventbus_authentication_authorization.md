# Implement EventBus authentication, authorization, and strict security configuration

## Priority
High

## Summary
No route in `scripts/eventbus/` authenticates or authorizes callers — confirmed by direct read
of `app.py`, `publish_route.py`, `subscribe_route.py`, `ack_route.py`, `dlq_route.py`, and
`replay_route.py`, none reference any auth mechanism. Any client that can reach the bound port
can publish, subscribe with an arbitrary `consumer_id`, ACK/NACK on behalf of any consumer,
inspect and requeue the DLQ, and replay full history. `EventBusConfig.__post_init__`
(`config.py` lines 44-54) already rejects any non-loopback `host` at startup — this is stronger
than memo4.md's original premise ("configuration permits public binding when explicitly
enabled") and should be reflected as already-resolved, not re-implemented. `load_config()`
(`config.py` lines 60-80) also already rejects a fixed, hardcoded set of removed keys
(`_REMOVED_CONFIG_KEYS`) but still uses a bespoke `tomllib.load()` rather than the shared
`ConfigLoader`, and any *other* unknown key is silently ignored (only the explicitly-listed
required keys are read via `data["..."]`/`data.get("host", ...)`).

## Background
Confirmed by direct read: `config.py`'s `EventBusConfig.__post_init__` raises `ValueError` for
any `host` other than `127.0.0.1`/`::1` (lines 50-54), and `app.py`'s `_main()` adds a
post-startup `_LoopbackVerifyingServer` socket check (lines 203-219) as defense-in-depth. Both
of these already satisfy memo4.md's "reject public binding when valid authentication is not
configured" concern in its strongest form (public binding is rejected unconditionally, not only
absent authentication) — this part of the original issue is resolved and should not be
re-implemented. However, `load_config()` performs no schema validation beyond the fixed
`_REMOVED_CONFIG_KEYS` list — an unrelated typo'd key in `eventbus.toml` is silently ignored
rather than rejected, and the loader does not go through `scripts/shared/config_loader.py`.

## Problem
- No authentication middleware exists — every route accepts unauthenticated requests.
- No authorization model exists — a caller can act as any `consumer_id`, access any topic,
  administer the DLQ, and trigger replay, all without any permission check.
- `load_config()` bypasses the shared `ConfigLoader` and only rejects a fixed, hardcoded set of
  removed keys — any other unknown, missing, or incorrectly-typed key is silently accepted or
  ignored rather than failing closed.

## Reason for Change
Establish EventBus as a fail-closed security boundary. Authentication must identify the
caller, authorization must limit actions, topics, and consumer IDs, and configuration behavior
must be consistent, strict, and auditable — separately from the loopback-binding protection
that already exists.

## Implementation Intent
Create or update the security ADR before implementing the runtime policy. Implement
centralized authentication middleware and define publisher/consumer/operator/monitoring
permissions. Bind authenticated consumer identity to allowed consumer IDs and topics. Require
operator permission for DLQ administration and privileged replay. Separately, migrate EventBus
configuration loading to the shared `ConfigLoader` (or document and get approval for a
justified exception) so unknown/missing/incorrectly-typed keys fail closed, not only the
current fixed removed-key list.

## Target Files or Areas
- `scripts/eventbus/app.py`
- `scripts/eventbus/config.py`
- `scripts/eventbus/publish_route.py`
- `scripts/eventbus/subscribe_route.py`
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/dlq_route.py`
- `scripts/eventbus/replay_route.py`
- `scripts/shared/config_loader.py`
- `docs/00_security_01_architecture-and-trust-boundaries.md`

## Required Changes
- Create or update the security ADR before implementing the runtime policy.
- Implement centralized authentication middleware.
- Define publisher, consumer, operator, and monitoring permissions.
- Bind authenticated consumer identity to allowed consumer IDs and topics.
- Require operator permission for DLQ administration and privileged replay.
- Migrate EventBus configuration loading to the shared `ConfigLoader` or document and approve
  a justified exception.
- Reject unknown, removed, missing, and incorrectly typed security-related configuration keys
  (beyond the current fixed `_REMOVED_CONFIG_KEYS` list).
- Audit authorization failures and privileged actions without recording secrets.
- Do not re-implement or weaken the existing loopback-only bind enforcement
  (`EventBusConfig.__post_init__` and `_LoopbackVerifyingServer`) — confirm it remains intact.

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability — including the already-strict
  loopback-bind rejection currently in `config.py`/`app.py`.
- Do not weaken the existing unconditional public-bind rejection while adding authentication —
  authentication is additive to, not a replacement for, loopback-only binding.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] Unauthenticated protected requests are rejected.
- [ ] A consumer cannot act as another consumer or access an unauthorized topic.
- [ ] DLQ administration requires operator authorization.
- [ ] The existing loopback-only bind rejection (`EventBusConfig.__post_init__`,
      `_LoopbackVerifyingServer`) is confirmed unchanged by this work.
- [ ] Configuration typos and unknown keys do not silently pass validation.
- [ ] Positive and negative authorization tests cover every route category.

## Testing Expectations
Add unit/integration tests for authentication middleware and per-route authorization (positive
and negative cases for publish/subscribe/ack/nack/dlq/replay). Update
`tests/eventbus/test_eventbus_config.py` to cover the stricter config-loading behavior. Run the
complete EventBus test suite and the repository's linting, type checking, and documentation
consistency checks.

## Documentation Impact
Create or update the EventBus security ADR and `docs/00_security_01_architecture-and-trust-boundaries.md`
to document the authentication/authorization model as the canonical specification. Note in the
same update that loopback-only binding was already enforced prior to this issue (avoid
re-describing it as newly added).

## Out of Scope
- Transactional ACK/offset redesign, backpressure handling, and DLQ requeue redesign (each
  tracked separately in this batch).
- Re-implementing loopback-only binding — already implemented; verify only.

## Dependencies
N/A: none

## Unresolved Questions
Which authentication mechanism to adopt (static bearer token, rotatable service token, mutual
TLS, reverse-proxy authentication) — this must be an explicit design decision recorded in the
security ADR before implementation, not inferred here.

## AI Implementation Instruction
Do not re-implement loopback-only binding — `EventBusConfig.__post_init__` (`config.py` lines
44-54) and `_LoopbackVerifyingServer` (`app.py` lines 203-219) already enforce it; confirm with
a regression test instead. Focus implementation effort on authentication middleware,
per-route/per-consumer authorization, and closing the config-loader's unknown-key gap.
