---
title: "ADR-013: EventBus Authentication and Authorization"
area: governance
tags:
  - eventbus
  - authentication
  - authorization
related:
  - ADR-002-config-isolation.md
  - ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md
  - eventbus_01_system-overview.md
  - eventbus_06_persistence_schema_and_replay.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - security_01_architecture-and-trust-boundaries.md
  - governance_03_issue-and-uncertainty-management.md
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

EventBus API establishes a fail-closed security boundary by adding Bearer-token authentication resolved by per-route dependencies, a five-role authorization model (publisher/consumer/operator/monitoring/admin) bound to caller identity, structured audit logging of authorization failures and privileged actions, and fail-closed configuration-key validation — while leaving the already-strict loopback-only bind enforcement untouched.

## Context

### Problem

EventBus routes in `scripts/eventbus/` are intended to authenticate callers by Bearer token and authorize them by role. Roles are resolved by per-route dependencies and the HTTP middleware only assigns a request ID; `/health` and `/publish` are registered without a role dependency (EVENTBUS-016). Consumer identity validation is skipped for a token with no configured `consumer_id` allowlist entry (EVENTBUS-008; see Known Deviations). `load_config()` enforces fail-closed validation for unknown keys, missing required keys, and wrong-type keys, implemented locally, not via `ConfigLoader`.

### Current State

`attach_auth_middleware(app)` (request-ID assignment only) is attached in `scripts/eventbus/app.py`. Routes other than `/health` and `/publish` require role-based authentication via `Depends(require_role(...))`. Consumer-facing routes (/subscribe, /ack, /nack) additionally require `Depends(require_consumer_identity)` for consumer identity validation.

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

1. **Authentication mechanism**: Bearer token, resolved per route by FastAPI dependencies (`resolve_principal`, `require_role(...)`, `require_consumer_identity`): a missing or unknown token is rejected with 401 and a token whose roles do not include the route's role with 403. The HTTP middleware attached by `attach_auth_middleware()` only assigns `X-Request-Id`. Two kinds of token are accepted: the single shared `auth_token` (grants every role, suited to single-token deployments) and an optional per-role token (`publisher_token`/`consumer_token`/`operator_token`/`monitoring_token`, each granting exactly one role; `admin_token` grants every role, same as `auth_token`). A caller's actual role(s) are resolved from *which* configured token they presented (`scripts/eventbus/auth.py`'s `_TOKEN_PRINCIPAL_MAP`), not merely from having presented *a* valid token — `require_role(...)`'s `_check_role` rejects (403) a token whose resolved role(s) do not include the endpoint's required role, even when that token is otherwise valid. `auth_token` and `admin_token` are operator credentials and MUST NOT be distributed to publishers or consumers; role separation holds only for callers that hold a per-role token.
2. **Authorization model**: Five roles — publisher, consumer, operator, monitoring, admin — each granted a fixed subset of routes:
   - Publisher: POST `/publish`
   - Consumer: GET `/subscribe`, POST `/events/{event_id}/ack`, POST `/nack`
   - Operator: GET `/dlq`, POST `/dlq/{event_id}/requeue`, GET `/replay`
   - Monitoring: GET `/health`
   - Admin: POST `/admin/topics/authorization`
3. A consumer's authenticated identity is bound to allowed `consumer_id`s and topics — a caller cannot act as another consumer or access unauthorized topics.
4. DLQ administration (`/dlq`, `/dlq/{event_id}/requeue`) and privileged replay (`/replay`) require operator permission.
5. Audit logging of authorization failures and privileged actions, with no secret/token values recorded.
6. Fail-closed rejection of unknown, missing, and incorrectly-typed EventBus configuration keys in `load_config()` — implemented locally, not via `ConfigLoader`.
7. A missing or empty `auth_token` in `config/eventbus.toml` must fail closed at startup, not silently start unauthenticated.
8. EventBus configuration is not loaded through `ConfigLoader` for key validation (ADR-002 documents the local-invariant exception).

### Scope

- **Components**: `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/config.py`, `scripts/eventbus/audit.py`
- **Tests**: `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_config.py`
- **Documentation**: `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`

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

#### Advantages

Less code; simpler deployment; no token management overhead.

#### Disadvantages

No protection if loopback binding is bypassed (e.g., misconfiguration, container network changes); no accountability for who performs which action; no separation of concerns between roles.

#### Reason for Rejection

Violates the fail-closed security boundary principle adopted for other high-risk components; loopback-only binding alone is insufficient for a multi-tenant security model even on localhost.

### Alternative B: Use mutual TLS instead of Bearer tokens

#### Advantages

Stronger cryptographic guarantees; no token storage or rotation concerns.

#### Disadvantages

Overkill for loopback-only deployment; adds operational complexity (certificate management); no benefit over static token for single-operator use case.

#### Reason for Rejection

Static Bearer token sufficient for loopback-only deployment; mTLS would add unnecessary complexity without security benefit for this threat model.

### Alternative C: Migrate to `ConfigLoader` for configuration validation

#### Advantages

Consistent configuration validation across the project; centralized schema management.

#### Disadvantages

Key validation through a `ConfigLoader`-based schema conflicts with the local-invariant exception ADR-002 documents (EventBus loads its configuration through `ConfigLoader` without `restrict_to()`).

#### Reason for Rejection

ADR-002 documents the exception. Equivalent fail-closed validation is implemented locally in `load_config()` instead.

## Consequences

### Positive Consequences

- EventBus API has a fail-closed security boundary with authentication and authorization.
- Clear separation of concerns between roles (publisher/consumer/operator/monitoring/admin).
- Audit trail for security events without recording secrets.
- Configuration typos and unknown keys are rejected rather than silently accepted.
- Per-role tokens restrict a caller that holds only that token: a caller holding
  only a `consumer_token` cannot reach a `Role.PUBLISHER`/`Role.OPERATOR`-gated
  route. Because `auth_token` is mandatory and grants every role, role separation
  depends on keeping it operator-only (INV-07).

### Negative Consequences

- Reimplementation of Bearer-token and audit patterns locally (cannot import from `mcp_servers` per isolation contract); risk of silent behavioral drift between implementations over time.
- Requires `auth_token` to be populated in `config/eventbus.toml` before deployment.
- Added complexity in route handlers for identity binding checks.

### Ongoing Risks

- Token storage in TOML config requires careful handling (never commit to version control).
- Consumer identity binding assumes the token encodes the consumer identity; production deployments should use a proper identity store.
- Audit log format evolution must remain compatible with log aggregation tools.

### Operational Consequences

- Operators configuring EventBus must populate `auth_token` in `config/eventbus.toml` before starting.
- An empty/missing token causes startup failure (fail-closed), not silent unauthenticated operation.
- Operators may additionally configure `publisher_token`/`consumer_token`/
  `operator_token`/`monitoring_token`/`admin_token` to grant per-role access
  instead of distributing the single shared `auth_token` to every caller.
  `auth_token` and `admin_token` both remain broad, superuser-equivalent
  credentials (every role) — operators who want strict role separation should
  distribute only the specific per-role token each caller needs, not `auth_token`
  or `admin_token`.

### Security Consequences

- Closes the authentication gap on all EventBus routes.
- Authorization boundaries prevent role escalation.
- Audit records identify the affected caller and action without exposing secrets.

## Invariants

- INV-01: All EventBus routes MUST reject unauthenticated requests with HTTP 401.
- INV-02: A caller MUST NOT be able to act as another `consumer_id` or access an unauthorized topic.
- INV-03: DLQ administration and privileged replay MUST require operator authorization.
- INV-04: Unknown, missing, or incorrectly-typed configuration keys MUST be rejected by `load_config()`.
- INV-05: Audit records MUST never include secret/token values.
- INV-06: Loopback-only binding enforcement MUST remain unchanged.
- INV-07: A token that grants every role (`auth_token`, `admin_token`) is never distributed to a publisher or consumer process.

## Exceptions

None.

## Failure Policy

### Fail-Fast Conditions

- Missing or empty `auth_token` in `config/eventbus.toml` causes startup failure.
- Unauthenticated request to any protected route returns 401.
- Unauthorized role attempting a restricted route returns 403.
- Unknown or wrong-type configuration key raises `ValueError`.

### Fail-Open or Degraded Conditions

- None. `/health` is intended to require the Monitoring role (not enforced by the application today; EVENTBUS-016).

### Retry Policy

Not applicable for authentication failures.

### Fallback Policy

Not applicable — a rejected request MUST be reported as rejected, not silently downgraded to a no-op.

## Data Ownership and Persistence

Not applicable in the DB sense — this ADR governs a control-flow/validation boundary, not persisted state. The audit record (JSON lines, per-call) is the relevant persisted artifact and is covered by INV-05's requirement for no secret logging.

## Verification

### Automated Tests

- **Test**: Unauthenticated requests to protected routes return 401 (`test_publish_without_token`, `test_subscribe_without_token`, etc.) — **Verifies**: INV-01 — **Type**: Integration — **Blocking**: Yes (these tests build their own fixture app with the role dependencies; they do not cover the production wiring of `/health` and `/publish`, tracked as EVENTBUS-016)
- **Test**: Wrong-role caller rejected on restricted routes (`test_subscribe_as_wrong_role`, `test_nack_with_publisher_token_is_rejected`, `test_dlq_list_with_publisher_token_is_rejected`, `test_dlq_requeue_with_publisher_token_is_rejected`, `test_replay_with_publisher_token_is_rejected`) — **Verifies**: INV-03 (operator-gated routes) — **Type**: Integration — **Blocking**: Yes
- **Test**: consumer topic restriction is enforced and returned by `require_consumer_identity` (`test_non_empty_topic_restriction_is_enforced_and_returned`; `consumer_id` allowlist gap tracked as EVENTBUS-008) — **Verifies**: INV-02 (topic access) — **Type**: Unit — **Blocking**: Yes
- **Test**: `load_config()` rejects an empty `auth_token` (`test_load_config_rejects_empty_auth_token`) — **Verifies**: Decision Details #7 — **Type**: Unit — **Blocking**: Yes
- **Test**: `load_config()` rejects unknown TOML keys (`test_load_config_rejects_unknown_key`) — **Verifies**: INV-04 — **Type**: Unit — **Blocking**: Yes
- **Test**: `load_config()` rejects wrong-type keys (`test_load_config_rejects_wrong_type`) — **Verifies**: INV-04 — **Type**: Unit — **Blocking**: Yes
- **Test**: `EventBusConfig(host="0.0.0.0", ...)` raises ValueError (`test_non_loopback_host_raises_value_error`) — **Verifies**: INV-06 — **Type**: Regression — **Blocking**: Yes
- **Test**: audit records do not include token values (`test_no_credential_leakage_in_audit_records`) — **Verifies**: INV-05 — **Type**: Unit — **Blocking**: Yes
- **Test**: none — **Verifies**: INV-07 — **Type**: Manual Review (deployment configuration review) — **Blocking**: Yes

## Implementation Notes

See Implementation References for the current file/symbol list.

## Known Deviations

- **Known Issue**: EVENTBUS-008 — see `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1.
- **Known Issue**: EVENTBUS-015 — tracked in governance_03 Part 1 (`auth_token` and `admin_token` grant every role; INV-07 depends on operator discipline only)
- **Known Issue**: EVENTBUS-016 — tracked in governance_03 Part 1 (`/health` and `/publish` are registered without a role dependency; violates INV-01)

## Review Triggers

- EventBus is exposed to callers other than the single trusted Agent process.
- A legitimate operational need for token rotation is identified (triggers revisiting the static bearer-token mechanism in Decision Details #1).
- The `.importlinter` `eventbus-is-isolated` contract is relaxed to allow importing from `mcp_servers`.

## Approval

### Required Reviewers

- Architecture Owner
- Security Reviewer

### Approval Record

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
- **Decision Change (2026-10-08)**: The authentication description correction, INV-07, and the EVENTBUS-015 and EVENTBUS-016 deviations were approved as a task-level approval decision (repository administrator instruction); individual reviewer names are not recorded.

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
