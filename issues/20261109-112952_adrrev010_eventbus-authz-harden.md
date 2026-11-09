# Harden EventBus authorization generations, consumer grants, and credentials, and fix the ADR-013 contract

## Priority
High

## Summary
Make the EventBus authorization guarantees hold across restarts and across principals (generation values that survive a restart, one principal per `consumer_id`, a minimal credential set, one no-op contract), and give every ADR-013 decision a correct invariant mapping and a test.

## Background
- Source: `memo-issue.md` items H-12 and M-02, re-checked against current source on 2026-11-09.
- `Explicit in code`: `scripts/eventbus/auth.py` keeps the current authorization generation in a module-level variable; a new generation is `0` when none exists, otherwise the previous value plus one. After a service restart the counter therefore restarts from `0` (consistent with the memo; the lost-update scenario with `expected_generation` follows from it and `Needs confirmation` by test).
- `Explicit in code`: `scripts/eventbus/admin_route.py` rejects an empty request body with 422, compares `expected_generation` before change detection (409 on mismatch), and returns a `changed` boolean in a 200 response, so an unchanged non-empty update returns `changed: false`. ADR-013 text is said to reject empty or unchanged updates with 422 yet also document `changed: false` (`Documentation only`; `Needs confirmation` against the ADR).
- `Explicit in code`: `scripts/eventbus/config.py` has both `auth_token` and `admin_token`; the comment states the shared `auth_token` and `admin_token` hold only the Operator, Monitoring, and Admin roles. `Needs confirmation`: whether `load_config()` rejects one `consumer_id` granted to several principals (not found in this review's search).
- `Documentation only` (from the review memo, not re-verified): shared ACKs under one `consumer_id` can lose events (ADR-006 INV-07); the ADR-013 Verification table maps `persistent:false` to INV-03 and the 422 rejection to INV-04, both reportedly wrong; generation, TTL, `expected_generation` 409/422, and baseline audit have no invariant or test; the threat model alternates between "multi-tenant" and "single-operator" and says "use a formal identity store in production"; one sentence about `load_config()` rejecting shared token values is broken.
- Related archived: `eballow01_require-non-empty-consumer-authorization-for-eventbus-consumer-token`, `ebsec001_eventbus_auth_token_startup_block` under `issues/done/`. Existing tests: `tests/eventbus/test_authz_generation_ttl.py`, `test_admin_topics_authorization.py`.

## Problem
- Optimistic concurrency breaks across restarts: an administrator who read generation N before a restart can send `expected_generation=N` after the counter has again reached N, and the update is accepted against a state they never saw.
- Two principals sharing one `consumer_id` can advance the offset past events the other never processed.
- Two credentials with identical powers double the secret-handling surface without a least-privilege benefit.
- A contract that both rejects no-ops and reports `changed: false` cannot be implemented consistently; wrong or missing invariant mappings leave the most security-relevant behavior unverified.

## Reason for Change
- ADR-013 is the authentication and authorization contract for a service that carries a security boundary; these gaps weaken guarantees that the ADR claims.
- The EventBus is kept (maintainer decision of 2026-11-09, planned future integration), so this issue is not conditional.

## Implementation Intent
- The ADR-013 guarantees hold across restarts and across principals with a minimal credential set, and every decision has an invariant and a test.
- Keep the existing role model except where this issue merges the two control-plane credentials.

## Target Files or Areas
- `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/config.py`, `config/eventbus.toml`
- Tests: `tests/eventbus/test_authz_generation_ttl.py`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_consumer_authorization.py`
- Docs: ADR-013 (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`), ADR-006, `docs/10_adr/adr_01_index.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`

## Required Changes
- Include a boot epoch (or a hash of the baseline) in the generation, and reject generations issued before a restart with 409.
- Reject at `load_config()` any configuration that grants one `consumer_id` to more than one principal.
- Merge `auth_token` and `admin_token` into one control-plane credential, and update the configuration, `eventbus_02`, `eventbus_07`, and ADR-013.
- Standardize the no-op outcome as 422, and remove the `changed` field from the response and the tests.
- Fix the invariant mapping in the ADR-013 Verification table; add invariants for generation, TTL, `expected_generation`, and baseline audit, each with a test, and add the Implementation column.
- Fix the threat model (single operator), remove the "formal identity store in production" sentence, and rewrite the broken `load_config()` sentence.

## Constraints
- Config load must reject the removed credential key; no compatibility shim.
- Secrets must not appear in tests, documents, or logs; tests use dummy values.
- ADR-013 amendments need approval records (governance-ledger issue); the implementer must not fabricate approvals.
- Measure blast radius before changing the generation type or the response shape (`rules/toolchain.md`).

## Acceptance Criteria
- After a restart, a request carrying a generation issued before the restart receives 409.
- A configuration granting one `consumer_id` to more than one principal fails config load.
- Only one control-plane token key exists.
- Every ADR-013 decision maps to at least one invariant and test, and no contradictory statements remain.
- `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_structure.py`, `check_docs_consistency.py --domain eventbus`, and the EventBus tests pass.

## Testing Expectations
- New or updated tests in `tests/eventbus/` for the restart epoch, duplicate grants, the merged credential, the no-op contract, and each new invariant; the full validation sequence from `rules/toolchain.md`.
- Documentation checkers listed above.

## Documentation Impact
- ADR-013, ADR-006 (if affected), the ADR index, `eventbus_02`, `eventbus_07`, and `security_01` change. State intent, the single-operator threat model, failure behavior, and invariants; do not copy configuration values.

## Out of Scope
- Route handler structure and authorization enforcement per route (EventBus route handler issue in this batch).
- Outbox, `/replay`, `/health`, and configuration-loading specifications (EventBus specification issue in this batch).

## Dependencies
- Depends on: `issues/20261109-112504_adrrev001_eventbus-route-handlers.md` and `issues/20261109-112739_adrrev006_eventbus-future-decision.md`.
- Blocks: `issues/20261109-113152_adrrev014_eventbus-spec-gaps.md` (EventBus specification gaps).
- Related, recently archived: `eballow01` and `ebsec001` under `issues/done/`.

## Unresolved Questions
- `Needs confirmation`: whether `load_config()` already rejects a shared `consumer_id` grant; whether ADR-013 contains the contradictions and invariant mapping errors the memo lists.
- Maintainer decision: the form of the boot epoch (separate field versus hash of the baseline).

## AI Implementation Instruction
- Do not change the role model beyond merging the two control-plane credentials.
- Use dummy secrets only; do not write approval records on a maintainer's behalf.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112952
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/config.py`, `config/eventbus.toml`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_01_index.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`
