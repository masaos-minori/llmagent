---
title: "ADR-013: EventBus Authentication and Authorization"
area: governance
tags:
  - eventbus
  - authentication
  - authorization
related:
  - adr_02_002_config-isolation.md
  - adr_02_006_eventbus-sqlite-persistence-and-sse-delivery.md
  - eventbus_01_system-overview.md
  - eventbus_06_persistence_schema_and_replay.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - security_01_architecture-and-trust-boundaries.md
  - governance_03_issue-and-uncertainty-management.md
  - governance_01_documentation-policy.md
---

# ADR-013: EventBus Authentication and Authorization

## Keywords

- eventbus
- authentication
- authorization
- bearer-token
- security-boundary
- five-role-model

## Status

Accepted

## Summary

EventBus API establishes a fail-closed security boundary by adding Bearer-token authentication resolved by per-route dependencies, a five-role authorization model (publisher/consumer/operator/monitoring/admin) bound to caller identity, Consumer routes limited to Consumer-scoped principals bound to explicit `consumer_id` and topic authorizations (the shared `auth_token` and `admin_token` hold no Consumer role and have no Consumer bypass), structured audit logging of authorization failures and privileged actions, and fail-closed configuration-key validation — while leaving the already-strict loopback-only bind enforcement untouched.

## Context

### Problem

EventBus routes in `scripts/eventbus/` are intended to authenticate callers by Bearer token and authorize them by role. Roles are resolved by per-route dependencies and the HTTP middleware only assigns a request ID. Startup rejects a `consumer_token` configured without `consumer_authorization`. The accepted design admits to Consumer routes only a principal that holds the Consumer role and explicit `consumer_id` and topic authorizations; the shared `auth_token` and `admin_token` hold no Consumer role. `require_consumer_identity` rejects any principal without the Consumer role or without explicit bindings, and an empty `consumer_authorization` mapping resolves to deny-all. `load_config()` enforces fail-closed validation for unknown keys, missing required keys, and wrong-type keys, implemented locally, not via `ConfigLoader`.

### Current State

`attach_auth_middleware(app)` (request-ID assignment only) is attached in `scripts/eventbus/app.py`. Each route requires role-based authentication via `Depends(require_role(...))`. Consumer-facing routes (/subscribe, /ack, /nack) additionally require `Depends(require_consumer_identity)` for consumer identity validation.

### Constraints

- The `.importlinter` `eventbus-is-isolated` contract forbids importing `agent`/`mcp_servers`/`rag`/`db` from `eventbus` — confirmed via `PYTHONPATH=scripts uv run lint-imports`, contract `KEPT`.
- The existing `scripts/mcp_servers/server.py::attach_auth_middleware()` and `scripts/mcp_servers/audit.py::AuditRecord` patterns must be mirrored conceptually but reimplemented locally, not imported.
- EventBus configuration loading uses `scripts/shared/config_loader.py`'s `ConfigLoader` without `restrict_to()` (ADR-002 already documented and accepted this local-invariant exception); validating keys through a `ConfigLoader`-based schema is not adopted here.
- Loopback-only binding (`EventBusConfig.__post_init__`, `_LoopbackVerifyingServer`) is already implemented; this ADR does not re-implement or weaken it.

## Assumptions

- "Privileged replay" means all `/replay` calls require operator permission (all replay is treated as an operator action).
- The token is stored as a plain string in config (following the existing `auth_token = "${ENV:...}"` convention used by every `*_mcp_server.toml` file).
- Empty/missing `auth_token` must fail closed at startup.

## Decision

### Decision Details

1. **Authentication mechanism**: Bearer token, resolved per route by FastAPI dependencies (`resolve_principal`, `require_role(...)`, `require_consumer_identity`): a missing or unknown token is rejected with 401, and a valid token that lacks the route's role or binding is rejected with 403. The HTTP middleware attached by `attach_auth_middleware()` only assigns `X-Request-Id`. Two kinds of token are accepted: the shared `auth_token` and `admin_token`, which hold only the control-plane roles Operator, Monitoring, and Admin (no Publisher role and no Consumer role), and per-role tokens (`publisher_token`/`consumer_token`/`operator_token`/`monitoring_token`, each granting exactly one role). A caller's roles are resolved from *which* configured token it presented (`scripts/eventbus/auth.py`'s `_TOKEN_PRINCIPAL_MAP`), not merely from having presented *a* valid token. Server-side authorization does not depend on how tokens are distributed.
2. **Authorization model**: Five roles — publisher, consumer, operator, monitoring, admin — each granted a fixed subset of routes:
   - Publisher: POST `/publish`
   - Consumer: GET `/subscribe`, POST `/events/{event_id}/ack`, POST `/nack`
   - Operator: GET `/dlq`, POST `/dlq/{event_id}/requeue`, GET `/replay`
   - Monitoring: GET `/health`
   - Admin: POST `/admin/topics/authorization`

   Admin Role is not a superset of the Consumer Role: each role grants only its own routes. A principal that holds several roles can reach Consumer routes only if it also has explicit `consumer_id` and topic bindings.
3. Only a Consumer principal bound to explicit `consumer_id` and topic authorizations may access Consumer routes (`GET /subscribe`, `POST /events/{event_id}/ack`, `POST /nack`, and any route that operates on consumer delivery state). The shared `auth_token` and the `admin_token` do not grant the Consumer role and cannot be used for Subscribe, ACK, or NACK. No principal bypasses consumer identity or topic authorization. A request is admitted only when the principal has the Consumer role, a consumer authorization, and a topic authorization (a non-empty list, or an empty mapping that denies all), and the requested `consumer_id` and topics are authorized.
   - 401: the token is missing or unknown.
   - 403: the token is valid but lacks the Consumer role, lacks a consumer or topic authorization, or the requested `consumer_id` or topic is not authorized.
4. DLQ administration (`/dlq`, `/dlq/{event_id}/requeue`) and privileged replay (`/replay`) require operator permission.
5. Audit logging of authorization failures and privileged actions, with no secret/token values recorded.
6. Fail-closed rejection of unknown, missing, and incorrectly-typed EventBus configuration keys in `load_config()` — implemented locally, not via `ConfigLoader`.
7. A missing or empty `auth_token` in `config/eventbus.toml` must fail closed at startup, not silently start unauthenticated.
8. EventBus configuration is not loaded through `ConfigLoader` for key validation (ADR-002 documents the local-invariant exception).

### Scope

- **Components**: `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/config.py`, `scripts/eventbus/audit.py`
- **Tests**: `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_config.py`, `tests/eventbus/test_eventbus_consumer_authorization.py`
- **Documentation**: `docs/10_adr/adr_02_013_eventbus-authentication-authorization.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Out of Scope

- Re-implementing or weakening loopback-only binding (`EventBusConfig.__post_init__`, `_LoopbackVerifyingServer`) — already implemented; a regression test confirms it.
- Transactional ACK/offset redesign, backpressure handling, and DLQ requeue redesign — each outside this ADR's scope.
- Migrating EventBus configuration loading to `scripts/shared/config_loader.py`'s `ConfigLoader` for key validation — not adopted (ADR-002 documents a local-invariant exception).
- Choosing between static bearer token / rotatable service token / mutual TLS / reverse-proxy authentication — static bearer token is adopted.

## Rationale

### 1. Correctness / Security

An HTTP API with no authentication or authorization is exposed to unrestricted access regardless of loopback-only binding. Adding authentication identifies the caller; adding authorization limits what they can do. Fail-closed configuration validation prevents silent misconfiguration.

### 2. Defense in Depth

Loopback-only binding remains the first layer; authentication/authorization is the second. They are independent controls — neither replaces the other.

### 3. Auditability

A security boundary with this risk profile requires an audit trail that identifies which caller performed which action and whether it was authorized.

### 4. Consistency with Existing Patterns

The Bearer-token scheme follows the convention of `scripts/mcp_servers/server.py::attach_auth_middleware()` (EventBus resolves roles through dependencies rather than in the middleware), and the audit record structure mirrors `scripts/mcp_servers/audit.py::AuditRecord` — both reimplemented locally per the isolation contract.

## Alternatives Considered

### Alternative A: Rely entirely on loopback-only binding and leave EventBus without authentication/authorization

- **Advantages:** Less code; simpler deployment; no token management overhead.
- **Disadvantages:** No protection if loopback binding is bypassed (e.g., misconfiguration, container network changes); no accountability for who performs which action; no separation of concerns between roles.
- **Reason for Rejection:** Violates the fail-closed security boundary principle adopted for other high-risk components; loopback-only binding alone is insufficient for a multi-tenant security model even on localhost.

### Alternative B: Use mutual TLS instead of Bearer tokens

- **Advantages:** Stronger cryptographic guarantees; no token storage or rotation concerns.
- **Disadvantages:** Overkill for loopback-only deployment; adds operational complexity (certificate management); no benefit over static token for single-operator use case.
- **Reason for Rejection:** Static Bearer token sufficient for loopback-only deployment; mTLS would add unnecessary complexity without security benefit for this threat model.

### Alternative C: Migrate to `ConfigLoader` for configuration validation

- **Advantages:** Consistent configuration validation across the project; centralized schema management.
- **Disadvantages:** Key validation through a `ConfigLoader`-based schema conflicts with the local-invariant exception ADR-002 documents (EventBus loads its configuration through `ConfigLoader` without `restrict_to()`).
- **Reason for Rejection:** ADR-002 documents the exception. Equivalent fail-closed validation is implemented locally in `load_config()` instead.

## Consequences

### Positive Consequences

- EventBus API has a fail-closed security boundary with authentication and authorization.
- Clear separation of concerns between roles (publisher/consumer/operator/monitoring/admin).
- Audit trail for security events without recording secrets.
- Configuration typos and unknown keys are rejected rather than silently accepted.
- Consumer identity binding is an exception-free contract, so a token distribution mistake does not lead directly to Consumer state changes.
- ACK, NACK, offset, and DLQ delivery integrity is strengthened, and no manual-review ban on distributing superuser tokens is needed.

### Negative Consequences

- Reimplementation of Bearer-token and audit patterns locally (cannot import from `mcp_servers` per isolation contract); risk of silent behavioral drift between implementations over time.
- Requires `auth_token` to be populated in `config/eventbus.toml` before deployment.
- Added complexity in route handlers for identity binding checks.
- A deployment that uses a shared token alone on Consumer routes is no longer compatible; every Consumer process needs a dedicated Consumer credential with an explicit mapping, and an administrator who operates on Consumer state also needs a separate Consumer-scoped credential.

### Ongoing Risks

- Token storage in TOML config requires careful handling (never commit to version control).
- Consumer identity binding assumes the token encodes the consumer identity; production deployments should use a proper identity store.
- Audit log format evolution must remain compatible with log aggregation tools.

### Operational Consequences

- Operators must populate `auth_token` in `config/eventbus.toml` before starting; an empty/missing token causes startup failure (see Failure Policy).
- Operators configure a per-role token for each caller (see Decision Details #1); a Consumer process uses a `consumer_token` with explicit `consumer_authorization` and `topic_authorization` mappings, and a Publisher process uses a `publisher_token`.

### Security Consequences

- Closes the authentication gap on all EventBus routes.
- Authorization boundaries prevent role escalation.
- Audit records identify the affected caller and action without exposing secrets.

## Invariants

- INV-01: All EventBus routes MUST reject unauthenticated requests with HTTP 401.
- INV-02: A caller MUST NOT act as another `consumer_id` or access an unauthorized topic. Every principal admitted to a Consumer route is bound to explicit `consumer_id` and topic authorizations; no superuser bypass exists.
- INV-03: DLQ administration and privileged replay MUST require operator authorization.
- INV-04: Unknown, missing, or incorrectly-typed configuration keys MUST be rejected by `load_config()`.
- INV-05: Audit records MUST never include secret/token values.
- INV-06: Loopback-only binding enforcement MUST remain unchanged.
- INV-07: A token without explicit `consumer_id` and topic authorizations MUST NOT access Consumer routes, even when it has Admin, Operator, or other privileged roles.

## Failure Policy

### Fail-Fast Conditions

- Missing or empty `auth_token` in `config/eventbus.toml` causes startup failure.
- Unauthenticated request to any protected route returns 401.
- Unauthorized role attempting a restricted route returns 403.
- A Consumer route called without the Consumer role, without a consumer or topic authorization, or with an unauthorized `consumer_id` or topic returns 403, for the shared `auth_token` and `admin_token` as well.
- A rejected Subscribe, ACK, or NACK changes no delivery state, offset, failure count, DLQ state, replay position, or active Consumer connection.
- Unknown or wrong-type configuration key raises `ValueError`.

### Fail-Open or Degraded Conditions

- None. `/health` requires the Monitoring role.

### Retry Policy

Not applicable for authentication failures.

### Fallback Policy

Not applicable — a rejected request MUST be reported as rejected, not silently downgraded to a no-op, a fallback, or a warning-and-continue. An authorization failure is a runtime fail-closed Authorization failure, not an availability failure.

## Data Ownership and Persistence

Not applicable in the DB sense — this ADR governs a control-flow/validation boundary, not persisted state. The audit record (JSON lines, per-call) is the relevant persisted artifact and is covered by INV-05's requirement for no secret logging.

## Verification

### Automated Tests

| Test | Verifies | Type | Blocking |
|---|---|---|---|
| Unauthenticated requests to protected routes return 401 (`test_publish_without_token`, `test_subscribe_without_token`, etc.) | INV-01 | Integration | Yes (the fixture-app tests are complemented by `TestProductionRouteWiring`, which checks the production app's route dependencies and the 401/403/200 behavior of `/health` and `/publish`) |
| Wrong-role caller rejected on restricted routes (`test_subscribe_as_wrong_role`, `test_nack_with_publisher_token_is_rejected`, `test_dlq_list_with_publisher_token_is_rejected`, `test_dlq_requeue_with_publisher_token_is_rejected`, `test_replay_with_publisher_token_is_rejected`) | INV-03 (operator-gated routes) | Integration | Yes |
| consumer topic restriction is enforced and returned by `require_consumer_identity` (`test_non_empty_topic_restriction_is_enforced_and_returned`) | INV-02 (topic access) | Unit | Yes |
| empty `consumer_authorization`/`topic_authorization` mappings resolve to deny-all and reject every `consumer_id` (`test_empty_mappings_deny_all_consumers`) | INV-02 empty-mapping case | Unit | Yes |
| `load_config()` rejects an empty `auth_token` (`test_load_config_rejects_empty_auth_token`) | Decision Details #7 | Unit | Yes |
| `load_config()` rejects unknown TOML keys (`test_load_config_rejects_unknown_key`) | INV-04 | Unit | Yes |
| `load_config()` rejects wrong-type keys (`test_load_config_rejects_wrong_type`) | INV-04 | Unit | Yes |
| `EventBusConfig(host="0.0.0.0", ...)` raises ValueError (`test_non_loopback_host_raises_value_error`) | INV-06 | Regression | Yes |
| audit records do not include token values (`test_no_credential_leakage_in_audit_records`) | INV-05 | Unit | Yes |
| `auth_token` and `admin_token` receive 403 on Subscribe, ACK, and NACK, and hold no Consumer or Publisher role (`TestSharedAndAdminTokensHaveNoConsumerBypass::test_subscribe_ack_and_nack_return_403`, `test_shared_and_admin_tokens_have_no_consumer_bypass`) | INV-02, INV-07 | Integration | Yes |
| a Consumer token with an authorized `consumer_id` succeeds; an unauthorized `consumer_id` or topic returns 403; an empty `consumer_authorization` mapping denies every `consumer_id`; a principal without a topic binding is rejected (`TestConsumerPrincipalBinding`, `test_principal_without_topic_binding_is_rejected`) | INV-02, INV-07 | Integration | Yes |
| a rejected ACK or NACK leaves delivery state, offset, failure count, and DLQ state unchanged (`TestSharedAndAdminTokensHaveNoConsumerBypass::test_rejected_ack_and_nack_change_no_delivery_state`) | INV-02, INV-07 | Integration | Yes |

## Implementation Notes

See Implementation References for the current file/symbol list.

## Known Deviations

Not applicable

## Review Triggers

- EventBus is exposed to callers other than the single trusted Agent process.
- A legitimate operational need for token rotation is identified (triggers revisiting the static bearer-token mechanism in Decision Details #1).
- The `.importlinter` `eventbus-is-isolated` contract is relaxed to allow importing from `mcp_servers`.
- The Consumer token model, or the consumer or topic authorization model, changes.
- An administrator needs to repair Consumer state, short-lived credentials, delegation, or OAuth scopes are introduced, or several Consumers must share one credential.

## Approval

### Required Reviewers

- Architecture Owner
- Security Reviewer

### Approval Record

- **Approved By**: Task-level approval decision (repository owner; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
- **Current Decision Approval**: Task-level approval decision (repository owner instruction) covers the current decision text as of 2026-10-15, including the Consumer-route admission rule and the removal of the superuser bypass; individual reviewer names are not recorded.

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-006: EventBus SQLite Persistence and SSE Delivery

## Implementation References

- `scripts/eventbus/auth.py` — `attach_auth_middleware()`, `require_role()`, `require_consumer_identity()`
- `scripts/eventbus/audit.py` — `AuditRecord`, `log_auth_failure()`, `log_privileged_action()`
- `scripts/mcp_servers/server.py` — `attach_auth_middleware()` (precedent pattern)
- `scripts/mcp_servers/audit.py` — `AuditRecord` (precedent pattern)
- `scripts/eventbus/app.py` — request-ID middleware registration and route dependencies
- `scripts/eventbus/config.py` — fail-closed validation
- Tests — `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_config.py`

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
- [x] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas (separate confirmation required)
