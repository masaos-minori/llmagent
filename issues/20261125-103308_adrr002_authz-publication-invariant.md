# Make the authorization generation publication boundary explicit

## Priority
Medium

## Summary
Authorization generation writers rely on an implicit "no await between read and publish" property, and keep `app.state.config` and the published generation as two assignments. Make the conditional publication explicit and tested so a later change cannot reintroduce lost updates.

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issues 002 and 003). The note claims lost updates and mixed-generation reads today; that is not reproducible in the current design:
- `publish_generation()` is a plain module-level assignment (`scripts/eventbus/auth.py:227-235`).
- The admin handler reads `current_generation()`, builds the next generation, then assigns `request.app.state.config` and calls `publish_generation()` (`scripts/eventbus/admin_route.py:211-212`); the only `await` in the handler is `await request.json()` at the top. The TTL sweep re-checks `current_generation() is not gen` and then publishes (`scripts/eventbus/authz_ttl.py:80-95`) with no await in between, and `authz_sweep_loop` calls it directly on the event loop. The service is a single process (no worker setting was found under `deploy/`). Within one event loop the read-build-publish sequence cannot interleave, and `test_same_expected_generation_second_request_409` already covers two updates from one generation (`tests/eventbus/test_admin_topics_authorization.py:235`).
- Confirmed: the two assignments (`app.state.config` then `publish_generation`) are separate statements in both writers, and ADR-013 Decision Detail 14 describes the sweep as compare-and-swap.
- Not found: any evidence of duplicate `N -> N+1` audit records or a reader that observes mixed state.
- Not verified: whether any reader runs in a worker thread (database callables use `asyncio.to_thread`; the authorization readers were not shown to).

## Problem
The correctness of generation publication depends on an unwritten property (no suspension point inside the critical section). The conditional-publish logic is duplicated between the admin route and the sweep, and runtime authorization state is split between `app.state.config` and `AuthzGeneration`.

## Reason for Change
A future `await` inside either writer would silently introduce lost updates, and nothing would fail a test. Making the boundary explicit is cheap now and removes the split authority.

## Implementation Intent
Provide one conditional-publication function in `scripts/eventbus/auth.py` that both writers use, and make authorization readers take config and principals from one generation snapshot. Keep startup-wide service configuration in `app.state.config`.

## Target Files or Areas
- `scripts/eventbus/auth.py`
- `scripts/eventbus/admin_route.py`
- `scripts/eventbus/authz_ttl.py`
- `scripts/eventbus/route_helpers.py`
- `tests/eventbus/test_admin_topics_authorization.py`
- `tests/eventbus/test_authz_generation_ttl.py`

## Required Changes
- Add a publish-if-current function (compare the expected generation or object identity, publish only on a match) and use it from the admin route and the sweep; the losing admin request returns 409 and the losing sweep aborts and retries.
- Stop runtime authorization writers from replacing `app.state.config`, and read authorization config from the generation snapshot.
- Add tests that interleave the two writers (a barrier or a forced suspension between read and publish) and a mixed-generation reader test.
- Document the restart behavior (runtime overrides vanish; the TOML baseline is rebuilt as generation 0), which ADR-013 Decision Detail 15 already states.

## Constraints
- No behavior change for single, uncontended requests; the 409 contract and audit output stay as they are.
- Do not change ADR decisions; this is an implementation hardening.

## Acceptance Criteria
- Two admin updates from one expected generation produce exactly one success and one 409, even with a forced suspension between read and publish.
- An admin update racing a TTL sweep never loses a committed update; generation numbers stay strictly increasing without duplicates.
- No reader observes authorization config and principals from different generations; unrelated service configuration is unchanged by an authorization update.

## Testing Expectations
Barrier-controlled concurrent admin update test, admin-versus-sweep race test, mixed-generation reader test, service-config stability test, and a restart baseline test; whole-suite run and changed-path gates.

## Documentation Impact
No ADR text change is expected; if ADR-013's compare-and-swap description gains a named function, update its component list only.

## Out of Scope
- Request validation order (issues/20261125-103307_adrr001_admin-ttl-precedence.md); multi-process deployments (the state stays process-local).

## Dependencies
- Should follow issues/20261125-103307_adrr001_admin-ttl-precedence.md to avoid overlapping edits in `admin_route.py` and its tests.

## Unresolved Questions
- `不明`: whether any supported deployment runs more than one worker process (none was found); an in-process mechanism is sufficient only for a single process.
- `不明`: whether any authorization reader runs in a worker thread.

## AI Implementation Instruction
Implement the explicit conditional publication and its tests first; do not claim a currently reproducible race; keep the 409 and audit contracts unchanged.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103308
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/route_helpers.py`
