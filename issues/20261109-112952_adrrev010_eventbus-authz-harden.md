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

## Adversarial Verification Results

Verified against current source on 2026-11-10. Source read: `scripts/eventbus/auth.py`,
`scripts/eventbus/admin_route.py`, `scripts/eventbus/config.py`,
`tests/eventbus/test_authz_generation_ttl.py`,
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`.

### Claims confirmed true in current source

- **Generation counter restarts from 0.** `_CURRENT_GENERATION` is module-level
  (`auth.py:93`); `build_and_publish_generation()` sets `generation = 0 if previous is
  None else previous.generation + 1` (`auth.py:240`). A restart therefore resets to 0.
  CONFIRMED.
- **Admin endpoint contract.** `admin_route.py` rejects an empty body with 422
  (`:125-129`), compares `expected_generation` against the in-force generation BEFORE
  change detection and returns 409 on mismatch (`:155-169`), and returns a `changed`
  boolean; a non-empty but unchanged body returns 200 `changed: false` (`:214-225`).
  CONFIRMED.
- **Two control-plane credentials, identical roles.** Both `auth_token` and `admin_token`
  exist and are built with the same `_CONTROL_PLANE_ROLES` ({OPERATOR, MONITORING,
  ADMIN}); `admin_token` holds no Consumer role (`auth.py:96-98,174-223`). They are
  functionally redundant. CONFIRMED.
- **No `load_config()` guard for a shared `consumer_id`.** Neither `load_config()` nor
  `EventBusConfig.__post_init__` rejects a configuration granting one `consumer_id` to
  more than one principal. The only duplicate guard is the token-value check in
  `_build_principal_map()` (`auth.py:147-165`). CONFIRMED (a genuine gap; the issue's
  `Needs confirmation` is answered: it is not rejected today).
- **Verification-table mis-mappings.** The ADR-013 Verification table maps
  `persistent: false` to INV-03 (`:254`) and the admin 422 / no-op `changed: false` to
  INV-04 (`:255-256`). INV-03 is "DLQ administration and privileged replay MUST require
  operator authorization" (`:201`) and INV-04 is "unknown/missing/mistyped config keys
  MUST be rejected by `load_config()`" (`:204`). Neither matches the mapped behavior.
  Both mappings are WRONG. CONFIRMED.
- **Threat-model alternation + identity-store sentence.** The ADR calls the model
  "multi-tenant" (`:148`) and "single-operator" (`:153-154`) in adjacent alternatives,
  and states production deployments "should use a proper identity store" (`:183`).
  CONFIRMED.
- **Broken `load_config()` sentence.** Decision Details #6 (`:79`) ends "...rejects a
  configuration in which distinct token roles share one non-empty token value, and a
  TOML authorization mapping reaches the Consumer principal through it." The trailing
  clause does not parse. CONFIRMED (grammatically broken).

### Claims overstated or inaccurate

- **"generation, TTL, `expected_generation` 409/422, and baseline audit have no invariant
  or test" is FALSE.** Generation is mapped to INV-01 and tested
  (`test_generation_monotonicity`, `test_snapshot_immutability`,
  `test_racing_updates_publish_one_generation`); `expected_generation` 409 is covered by
  `test_racing_updates_publish_one_generation`; TTL expiry is covered by
  `TestTTLExpirySweep`. Generation, TTL, and the 409 path all have tests. The statement
  overstates the gap. (TTL and the 409 path lack a *dedicated* ADR invariant row beyond
  INV-01; that is a narrower doc-consistency item, not an untested blind spot.)
- **The no-op "cannot be implemented consistently" framing is an overstatement.** The
  code IS internally consistent: it distinguishes an empty/malformed body (422) from a
  well-formed but unchanged body (200 `changed: false`). The real inconsistency is between
  ADR rule 12 (`:99`: "a body that produces no actual change is rejected with HTTP 422")
  and (a) the code that returns 200 `changed: false`, and (b) the ADR's own Verification
  row 256 ("No-op detected: `changed: false`"). This is a DOC-vs-CODE drift in ADR-013,
  resolvable by editing the ADR, not an implementation impossibility.

### Restart vulnerability is largely theoretical

- After a restart the baseline is reloaded from `config/eventbus.toml` as generation 0
  (ADR-013 rule 15, `:109`), and runtime overrides are never persisted. So a stale
  `expected_generation=N` accepted after the counter again reaches N operates on the
  freshly-reloaded baseline that every observer sees. There is no divergent hidden state
  to attack. The boot-epoch hardening is defensive, not a fix for a reachable exploit.
  The issue itself lists the boot-epoch form as an Unresolved Question.

### Assessment

- **Real, verifiable problems:** the two Verification-table mis-mappings (`persistent:
  false`→INV-03, admin 422/no-op→INV-04), the ADR rule 12 vs code/row-256 no-op drift,
  the grammatically broken Decision Details #6 sentence, the threat-model alternation,
  and the "proper identity store" sentence. All four are DOCUMENT fixes to ADR-013.
- **Not warranted as stated:** merging `auth_token`/`admin_token` (redundant, but a
  config-breaking change with blast radius — maintainer decision); standardizing no-op as
  422 and removing `changed` (would discard the currently-useful empty-vs-no-op
  distinction the code already implements correctly — regression risk); rejecting a shared
  `consumer_id` at `load_config()` (defensible guard, single-operator threat model,
  maintainer decision); adding a boot epoch (theoretical harm, form undecided).
- **Net:** this issue is DOCUMENTS/authority-only for ADR-013 plus three maintainer
  decisions (credential merge, no-op standardization, shared-`consumer_id` guard) and one
  undecided design choice (boot-epoch form). No clear code correctness fix is required.
  The verified doc defects can be fixed without fabricating any governance approval.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112952
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/config.py`, `config/eventbus.toml`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_01_index.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`
