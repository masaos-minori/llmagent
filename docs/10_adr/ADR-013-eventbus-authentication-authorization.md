---
title: "ADR-013: EventBus Authentication and Authorization"
area: governance
tags:
  - eventbus
  - authentication
  - authorization
decision_scope:
  - eventbus/api
related:
  - ADR-002-config-isolation.md
  - ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md
  - eventbus_01_system-overview.md
  - eventbus_07_persistence_schema_and_replay.md
  - eventbus_06_dlq_offsets_and_delivery_semantics.md
  - security_01_architecture-and-trust-boundaries.md
  - governance_03_issue-and-uncertainty-management.md
---

# ADR-013: EventBus Authentication and Authorization

## Status

Accepted

## Summary

EventBus API establishes a fail-closed security boundary by adding Bearer-token authentication middleware, a five-role authorization model (publisher/consumer/operator/monitoring/admin) bound to caller identity, structured audit logging of authorization failures and privileged actions, and fail-closed configuration-key validation — while leaving the already-strict loopback-only bind enforcement untouched.

## Context

### Problem

Several routes in `scripts/eventbus/` authenticate and authorize callers via Bearer-token middleware and role-based authorization, but the authentication model has gaps: consumer identity validation can fail-open when no `consumer_id` allowlist is configured for a token, and audit logging of privileged actions is incomplete. Additionally, `load_config()` enforces fail-closed validation for unknown keys, missing required keys, and wrong-type keys — implemented locally, not via `ConfigLoader`.

### Current State

Auth middleware (`attach_auth_middleware(app)`) is now attached to all routes in `scripts/eventbus/app.py`. Each route requires role-based authentication via `Depends(require_role(...))`. Consumer-facing routes (/subscribe, /ack, /nack) additionally require `Depends(require_consumer_identity)` for consumer identity validation. The Problem section above describes the pre-auth state; see the Known Deviations section below for residual gaps.

### Constraints

- The `.importlinter` `eventbus-is-isolated` contract forbids importing `agent`/`mcp_servers`/`rag`/`db` from `eventbus` — confirmed via `PYTHONPATH=scripts uv run lint-imports`, contract `KEPT`.
- The existing `scripts/mcp_servers/server.py::attach_auth_middleware()` and `scripts/mcp_servers/audit.py::AuditRecord` patterns must be mirrored conceptually but reimplemented locally, not imported.
- EventBus configuration loading uses `scripts/shared/config_loader.py`'s `ConfigLoader` without `restrict_to()` (ADR-002 already documented and accepted this local-invariant exception); validating keys through a `ConfigLoader`-based schema is not adopted here.
- Loopback-only binding (`EventBusConfig.__post_init__`, `_LoopbackVerifyingServer`) is already implemented; this ADR does not re-implement or weaken it.

### Assumptions

- The next unused ADR number is `ADR-013` (not the vacated `ADR-011` slot) — inferred from this repository's Known-Issue ID-non-reuse convention applied by analogy to ADRs, since no explicit ADR-numbering-reuse policy was found in `docs/10_adr/adr-index.md`.
- "Privileged replay" means all `/replay` calls require operator permission (simplest interpretation consistent with the Issue's Required Changes and Acceptance Criteria).
- The token is stored as a plain string in config (following the existing `auth_token = "${ENV:...}"` convention used by every `*_mcp_server.toml` file).
- Empty/missing `auth_token` must fail closed at startup, per `REQ-005`.

## Decision

### Decision Details

1. **Authentication mechanism**: Bearer token, mirroring `scripts/mcp_servers/server.py::attach_auth_middleware()` pattern — a FastAPI `@app.middleware("http")` function checking `request.headers.get("Authorization", "")` against a configured token. Two kinds of token are accepted: the single shared `auth_token` (grants every role, for backward compatibility with the original single-token deployment model) and an optional per-role token (`publisher_token`/`consumer_token`/`operator_token`/`monitoring_token`, each granting exactly one role; `admin_token` grants every role, same as `auth_token`). A caller's actual role(s) are resolved from *which* configured token they presented (`scripts/eventbus/auth.py`'s `_TOKEN_PRINCIPAL_MAP`), not merely from having presented *a* valid token — `require_role(...)`'s `_check_role` rejects (403) a token whose resolved role(s) do not include the endpoint's required role, even when that token is otherwise valid.
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
7. A missing or empty `auth_token` in `config/eventbus.toml` must fail closed at startup (per REQ-005), not silently start unauthenticated.
8. The ConfigLoader migration question is already resolved by ADR-002's local-invariant exception (its own embedded CI-001 note in Known Deviations) — no new decision needed there.

### Scope

- **Components**: `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/config.py`, `scripts/eventbus/audit.py`
- **Tests**: `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_config.py`
- **Documentation**: `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Out of Scope

- Re-implementing or weakening loopback-only binding (`EventBusConfig.__post_init__`, `_LoopbackVerifyingServer`) — already implemented; this Plan only adds a regression test confirming it.
- Transactional ACK/offset redesign, backpressure handling, and DLQ requeue redesign — each tracked by a separate Issue/Plan in this batch (`eb_h01`, `eb_h02`, `eb_h03`).
- Migrating EventBus configuration loading to `scripts/shared/config_loader.py`'s `ConfigLoader` for key validation — not adopted (ADR-002 already resolved this via a documented local-invariant exception).
- Correcting the stale `CI-001` status/Recommended-Action text in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (pre-existing documentation inconsistency unrelated to this Issue's stated Target Files).
- Choosing between static bearer token / rotatable service token / mutual TLS / reverse-proxy authentication as an open research question — this Plan resolves it to static bearer token.

## Rationale

### 1. Correctness / Security

An HTTP API with no authentication or authorization is exposed to unrestricted access regardless of loopback-only binding. Adding authentication identifies the caller; adding authorization limits what they can do. Fail-closed configuration validation prevents silent misconfiguration.

### 2. Defense in Depth

Loopback-only binding remains the first layer; authentication/authorization is the second. They are independent controls — neither replaces the other.

### 3. Auditability

A security boundary with this risk profile requires an audit trail that identifies which caller performed which action and whether it was authorized.

### 4. Consistency with Existing Patterns

The Bearer-token middleware mirrors `scripts/mcp_servers/server.py::attach_auth_middleware()`, and the audit record structure mirrors `scripts/mcp_servers/audit.py::AuditRecord` — both reimplemented locally per the isolation contract.

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

ADR-002 already documented and accepted the local-invariant exception (EventBus loads its configuration through `ConfigLoader` without `restrict_to()`).

#### Reason for Rejection

ADR-002 explicitly documents this exception. Implement equivalent local validation instead.

## Consequences

### Positive Consequences

- EventBus API has a fail-closed security boundary with authentication and authorization.
- Clear separation of concerns between roles (publisher/consumer/operator/monitoring/admin).
- Audit trail for security events without recording secrets.
- Configuration typos and unknown keys are rejected rather than silently accepted.
- Per-role tokens make the five-role model actually enforceable: a caller holding
  only a `consumer_token` cannot reach a `Role.PUBLISHER`/`Role.OPERATOR`-gated
  route, closing a gap where any caller holding the single shared token could
  previously reach every endpoint regardless of role.

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

## Traceability

### Implementation Procedures

- `implementations/done/20260910-171554_01_docs_adr_ADR-013-eventbus-authentication-authorization.md`: Create ADR document
- `implementations/done/20260910-171554_02_scripts_eventbus_auth_py.md`: Create auth module
- `implementations/done/20260910-171554_03_scripts_eventbus_app_py.md`: Modify app.py
- `implementations/done/20260910-171554_04_scripts_eventbus_subscribe_route_py.md`: Modify subscribe_route.py
- `implementations/done/20260910-171554_05_scripts_eventbus_ack_route_py.md`: Modify ack_route.py
- `implementations/done/20260910-171554_06_scripts_eventbus_dlq_route_py.md`: Modify dlq_route.py
- `implementations/done/20260910-171554_07_scripts_eventbus_replay_route_py.md`: Modify replay_route.py
- `implementations/done/20260910-171554_08_scripts_eventbus_config_py.md`: Modify config.py
- `implementations/done/20260910-171554_09_scripts_eventbus_audit_py.md`: Create audit module
- `implementations/done/20260910-171554_10_docs_00_security_01_architecture-and-trust-boundaries_md.md`: Modify security doc
- `implementations/done/20260910-171554_11_tests_eventbus_test_eventbus_config_py.md`: Modify config tests
- `implementations/done/20260910-171554_12_tests_eventbus_test_eventbus_auth_py.md`: Create auth tests

### Source Documents

- Source issue: issues/done/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- Source plan: plans/done/20260909-101237_plan.md

## Invariants

- INV-01: All EventBus routes MUST reject unauthenticated requests with HTTP 401.
- INV-02: A caller MUST NOT be able to act as another `consumer_id` or access an unauthorized topic.
- INV-03: DLQ administration and privileged replay MUST require operator authorization.
- INV-04: Unknown, missing, or incorrectly-typed configuration keys MUST be rejected by `load_config()`.
- INV-05: Audit records MUST never include secret/token values.
- INV-06: Loopback-only binding enforcement MUST remain unchanged.

## Exceptions

None.

## Failure Policy

### Fail-Fast Conditions

- Missing or empty `auth_token` in `config/eventbus.toml` causes startup failure.
- Unauthenticated request to any protected route returns 401.
- Unauthorized role attempting a restricted route returns 403.
- Unknown or wrong-type configuration key raises `ValueError`.

### Fail-Open or Degraded Conditions

- None for the authentication/authorization checks themselves; health endpoint (`/health`) remains accessible for monitoring.

### Retry Policy

Not applicable for authentication failures.

### Fallback Policy

Not applicable — a rejected request MUST be reported as rejected, not silently downgraded to a no-op.

## Data Ownership and Persistence

Not applicable in the DB sense — this ADR governs a control-flow/validation boundary, not persisted state. The audit record (JSON lines, per-call) is the relevant persisted artifact and is covered by INV-05's requirement for no secret logging.

## Verification

### Automated Tests

- **Test**: Unauthenticated requests to protected routes return 401 (`test_publish_without_token`, `test_subscribe_without_token`, etc.) — **Verifies**: INV-01 — **Type**: Integration — **Blocking**: Yes
- **Test**: Wrong-role caller rejected on restricted routes (`test_subscribe_as_wrong_role`, `test_nack_as_wrong_role`, `test_dlq_requeue_as_wrong_role`) — **Verifies**: INV-02, INV-03 — **Type**: Integration — **Blocking**: Yes
- **Test**: `load_config()` rejects unknown TOML keys (`test_load_config_rejects_unknown_key`) — **Verifies**: INV-04 — **Type**: Unit — **Blocking**: Yes
- **Test**: `load_config()` rejects wrong-type keys (`test_load_config_rejects_wrong_type`) — **Verifies**: INV-04 — **Type**: Unit — **Blocking**: Yes
- **Test**: `EventBusConfig(host="0.0.0.0", ...)` raises ValueError (`test_non_loopback_host_raises_value_error`) — **Verifies**: INV-06 — **Type**: Regression — **Blocking**: Yes
- **Test**: audit records do not include token values (verified by inspection of audit implementation) — **Verifies**: INV-05 — **Type**: Code Review — **Blocking**: Yes

### Resolved Items

- **Resolved**: Privileged-replay scope ambiguity (UNK-01) — resolved by this ADR's Decision Details #4 (all `/replay` calls require operator permission).
- **Resolved**: ConfigLoader migration question — already resolved by ADR-002's embedded CI-001 note.

## Implementation Notes

See Related Documents > Implementation References for the current file/symbol list.

This chapter is not a basis for design decisions. List detailed APIs, Classes, and Functions in the Implementation References.

Do not record line numbers; reference by File Path and Symbol name.

## Known Deviations

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s CI-001 (EventBus process reads configuration directly instead of using ConfigLoader, High severity, resolved 2026-09-15) is resolved and intentionally no longer tracked there. The residual gap EVENTBUS-008 (token with no configured consumer_id allowlist entry has consumer-identity validation skipped — fail-open) is open and registered in that document.

Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.

## Review Triggers

- EventBus is exposed to callers other than the single trusted Agent process.
- A legitimate operational need for token rotation is identified (triggers designing the separate administrative capability referenced in Decision Details #1).
- The `.importlinter` `eventbus-is-isolated` contract is relaxed to allow importing from `mcp_servers`.

## Approval

### Required Reviewers

- Architecture Owner
- Security Reviewer

### Approval Record

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related Documents

### Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-006: EventBus SQLite Persistence and SSE Delivery

### Specifications

- [EventBus System Overview](../24_eventbus/eventbus_01_system-overview.md)
- [EventBus Persistence Schema and Replay](../24_eventbus/eventbus_07_persistence_schema_and_replay.md)
- [EventBus DLQ Offsets and Delivery Semantics](../24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md)
- [Architecture and Trust Boundaries](../91_security/security_01_architecture-and-trust-boundaries.md)

### Known Issues

- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md) — CI-001 (ConfigLoader migration) addressed by this ADR.

### Implementation References

- `scripts/eventbus/auth.py` — `attach_auth_middleware()`, `require_role()`, `require_consumer_identity()`
- `scripts/eventbus/audit.py` — `AuditRecord`, `log_auth_failure()`, `log_privileged_action()`
- `scripts/mcp_servers/server.py` — `attach_auth_middleware()` (precedent pattern)
- `scripts/mcp_servers/audit.py` — `AuditRecord` (precedent pattern)
- `scripts/eventbus/app.py` — middleware registration
- `scripts/eventbus/config.py` — fail-closed validation
- Tests — `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_config.py`

## Keywords

eventbus
authentication
authorization
bearer-token
security-boundary
five-role-model

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
