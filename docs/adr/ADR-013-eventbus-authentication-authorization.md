---
title: "ADR-013: EventBus Authentication and Authorization"
area: adr
tags:
  - eventbus
  - authentication
  - authorization
decision_scope:
  - eventbus/api
related:
  - ADR-002
  - ADR-006
---

# ADR-013: EventBus Authentication and Authorization

## Status

Accepted

使用可能なStatusは次のとおりとする。

- `Proposed`: 提案中、レビューまたは承認前
- `Accepted`: 採用済みであり、現行設計として有効

Accepted後に現在の判断を変更する場合は、本ADR本文を直接更新する。同じ変更の中で、影響を受けるSpecification、Reference、Operations文書および検証要件を更新する。

## Summary

EventBus API establishes a fail-closed security boundary by adding Bearer-token authentication middleware, a four-role authorization model (publisher/consumer/operator/monitoring) bound to caller identity, structured audit logging of authorization failures and privileged actions, and fail-closed configuration-key validation — while leaving the already-strict loopback-only bind enforcement untouched.

## Context

### Problem

No route in `scripts/eventbus/` authenticates or authorizes callers. Every route accepts unauthenticated requests, allowing any caller to act as any `consumer_id`, access any topic, administer the DLQ, and trigger replay without any permission check. Additionally, `load_config()` bypasses fail-closed validation for anything beyond the fixed removed-key list: an unknown key is silently ignored, and no key's type is checked before being handed to `EventBusConfig`.

### Constraints

- The `.importlinter` `eventbus-is-isolated` contract forbids importing `shared`/`mcp_servers` from `eventbus` — confirmed via `PYTHONPATH=scripts uv run lint-imports`, contract `KEPT`.
- The existing `scripts/mcp_servers/server.py::attach_auth_middleware()` and `scripts/mcp_servers/audit.py::AuditRecord` patterns must be mirrored conceptually but reimplemented locally, not imported.
- Migrating EventBus configuration loading to `scripts/shared/config_loader.py`'s `ConfigLoader` is architecturally prohibited (ADR-002 already documented and accepted this local-invariant exception).
- Loopback-only binding (`EventBusConfig.__post_init__`, `_LoopbackVerifyingServer`) is already implemented; this ADR does not re-implement or weaken it.

### Assumptions

- The next unused ADR number is `ADR-013` (not the vacated `ADR-011` slot) — inferred from this repository's Known-Issue ID-non-reuse convention applied by analogy to ADRs, since no explicit ADR-numbering-reuse policy was found in `docs/adr-index.md`.
- "Privileged replay" means all `/replay` calls require operator permission (simplest interpretation consistent with the Issue's Required Changes and Acceptance Criteria).
- The token is stored as a plain string in config (following the existing `auth_token = "${ENV:...}"` convention used by every `*_mcp_server.toml` file).
- Empty/missing `auth_token` must fail closed at startup, per `REQ-005`.

## Decision

### Decision Details

1. **Authentication mechanism**: Static Bearer token, mirroring `scripts/mcp_servers/server.py::attach_auth_middleware()` pattern — a FastAPI `@app.middleware("http")` function checking `request.headers.get("Authorization", "")` against a configured token.
2. **Authorization model**: Four roles — publisher, consumer, operator, monitoring — each granted a fixed subset of routes:
   - Publisher: POST `/publish`
   - Consumer: GET `/subscribe`, POST `/events/{event_id}/ack`, POST `/nack`
   - Operator: GET `/dlq`, POST `/dlq/{event_id}/requeue`, GET `/replay`
   - Monitoring: GET `/health`
3. A consumer's authenticated identity is bound to allowed `consumer_id`s and topics — a caller cannot act as another consumer or access unauthorized topics.
4. DLQ administration (`/dlq`, `/dlq/{event_id}/requeue`) and privileged replay (`/replay`) require operator permission.
5. Audit logging of authorization failures and privileged actions, with no secret/token values recorded.
6. Fail-closed rejection of unknown, missing, and incorrectly-typed EventBus configuration keys in `load_config()` — implemented locally, not via `ConfigLoader`.
7. A missing or empty `auth_token` in `config/eventbus.toml` must fail closed at startup (per REQ-005), not silently start unauthenticated.
8. The ConfigLoader migration question is already resolved by ADR-002's local-invariant exception (its own embedded CI-001 note, lines 363-375) — no new decision needed there.

### Scope

- **Components**: `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/config.py`, `scripts/eventbus/audit.py`
- **Tests**: `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_config.py`
- **Documentation**: `docs/adr/ADR-013-eventbus-authentication-authorization.md`, `docs/00_security_01_architecture-and-trust-boundaries.md`

### Out of Scope

- Re-implementing or weakening loopback-only binding (`EventBusConfig.__post_init__`, `_LoopbackVerifyingServer`) — already implemented; this Plan only adds a regression test confirming it.
- Transactional ACK/offset redesign, backpressure handling, and DLQ requeue redesign — each tracked by a separate Issue/Plan in this batch (`eb_h01`, `eb_h02`, `eb_h03`).
- Migrating EventBus configuration loading to `scripts/shared/config_loader.py`'s `ConfigLoader` — architecturally prohibited (ADR-002 already resolved this via a documented local-invariant exception).
- Correcting the stale `CI-001` status/Recommended-Action text in `docs/00_governance_03_issue-and-uncertainty-management.md` (pre-existing documentation inconsistency unrelated to this Issue's stated Target Files).
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

Architecturally prohibited by `.importlinter` `eventbus-is-isolated` contract; ADR-002 already documented and accepted the local-invariant exception.

#### Reason for Rejection

ADR-002 explicitly documents this exception — EventBus cannot import ConfigLoader. Implement equivalent local validation instead.

## Consequences

### Positive Consequences

- EventBus API has a fail-closed security boundary with authentication and authorization.
- Clear separation of concerns between roles (publisher/consumer/operator/monitoring).
- Audit trail for security events without recording secrets.
- Configuration typos and unknown keys are rejected rather than silently accepted.

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

### Security Consequences

- Closes the authentication gap on all EventBus routes.
- Authorization boundaries prevent role escalation.
- Audit records identify the affected caller and action without exposing secrets.

## Traceability

### Implementation Procedures

- `implementations/20260910-171554_01_docs_adr_ADR-013-eventbus-authentication-authorization.md`: Create ADR document
- `implementations/20260910-171554_02_scripts_eventbus_auth_py.md`: Create auth module
- `implementations/20260910-171554_03_scripts_eventbus_app_py.md`: Modify app.py
- `implementations/20260910-171554_04_scripts_eventbus_subscribe_route_py.md`: Modify subscribe_route.py
- `implementations/20260910-171554_05_scripts_eventbus_ack_route_py.md`: Modify ack_route.py
- `implementations/20260910-171554_06_scripts_eventbus_dlq_route_py.md`: Modify dlq_route.py
- `implementations/20260910-171554_07_scripts_eventbus_replay_route_py.md`: Modify replay_route.py
- `implementations/20260910-171554_08_scripts_eventbus_config_py.md`: Modify config.py
- `implementations/20260910-171554_09_scripts_eventbus_audit_py.md`: Create audit module
- `implementations/20260910-171554_10_docs_00_security_01_architecture-and-trust-boundaries_md.md`: Modify security doc
- `implementations/20260910-171554_11_tests_eventbus_test_eventbus_config_py.md`: Modify config tests
- `implementations/20260910-171554_12_tests_eventbus_test_eventbus_auth_py.md`: Create auth tests

### Source Documents

- Source issue: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- Source plan: plans/20260909-101237_plan.md

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
- **Resolved**: ConfigLoader migration question — already resolved by ADR-002's embedded CI-001 note (lines 363-375).

## Implementation Notes

- Implementation files: `scripts/eventbus/auth.py` (Bearer-token verification, permission model), `scripts/eventbus/app.py` (middleware registration), `scripts/eventbus/config.py` (fail-closed validation), `scripts/eventbus/audit.py` (structured audit logging)
- Key symbols: `verify_bearer_token()`, `require_role()`, `require_consumer_identity()`, `log_auth_failure()`, `log_privileged_action()`
- Corresponding tests: `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_config.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

`docs/00_governance_03_issue-and-uncertainty-management.md`'s EVENTBUS-008 (No Production Authentication Model for Event Bus HTTP API, High severity, open) and CI-001 (EventBus process reads configuration directly instead of using ConfigLoader, High severity, open) are both registered and marked `open`. Whether any further deviation remains open after Phase 2's implementation lands is tracked in row 4 of that document.

ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。

## Review Triggers

- EventBus is exposed to callers other than the single trusted Agent process.
- A legitimate operational need for token rotation is identified (triggers designing the separate administrative capability referenced in Decision Details #1).
- The `.importlinter` `eventbus-is-isolated` contract is relaxed to allow importing from `shared`/`mcp_servers`.

## Approval

### Required Reviewers

- Architecture Owner
- Security Reviewer

### Approval Record

- **Approved By**: タスクレベル承認判断(リポジトリ管理者。個別レビュアー名は記録しない)
- **Approval Date**: 記録なし(タスクレベル承認判断のため個別の承認日は記録しない)
- **Approval Reference**: `docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

本ADRの`Accepted`ステータスは、上記ガバナンス文書が定めるタスクレベル承認判断を受理証跡とする。個別レビュアー名・承認日による正式なApproval Recordは作成していない。

## Related Documents

### Specifications

- [EventBus System Overview](../06_eventbus_01_system-overview.md)
- [EventBus DLQ Offsets and Delivery Semantics](../06_eventbus_04_dlq_offsets_and_delivery_semantics.md)
- [Architecture and Trust Boundaries](../00_security_01_architecture-and-trust-boundaries.md)

### Known Issues

- [Issue and Uncertainty Management](../00_governance_03_issue-and-uncertainty-management.md) — EVENTBUS-008 (No Production Authentication Model) and CI-001 (ConfigLoader migration) addressed by this ADR.

### Implementation References

- `scripts/eventbus/auth.py` — `verify_bearer_token()`, `require_role()`, `require_consumer_identity()`
- `scripts/eventbus/audit.py` — `AuditRecord`, `log_auth_failure()`, `log_privileged_action()`
- `scripts/mcp_servers/server.py` — `attach_auth_middleware()` (precedent pattern)
- `scripts/mcp_servers/audit.py` — `AuditRecord` (precedent pattern)

## Keywords

eventbus
authentication
authorization
bearer-token
security-boundary
four-role-model

## Completion Checklist

ADRをAcceptedへ変更する前に確認する。

- [x] 解決する問題が明確である
- [x] Decisionが1つの主要な設計判断に絞られている
- [x] Decisionが必須、禁止、正本、Fallback条件などの明確な表現で記載されている
- [x] 採用理由が現在の実装以外の観点で説明されている
- [x] 実質的な代替案と不採用理由が記載されている
- [x] Positive Consequencesが記載されている
- [x] Negative Consequencesが記載されている
- [x] Securityへの影響が評価されている
- [x] Operations、Monitoring、Recoveryへの影響が評価されている
- [x] 検証可能なInvariantsが定義されている
- [x] Exceptionsまたは適用対象外が明確である
- [x] 各InvariantにVerificationが対応している
- [x] 自動化可能な検証がManual Reviewだけになっていない
- [x] 現行実装との差異がKnown Issueへ登録されている
- [x] Ownerと必要なReviewerが定義されている（`docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standardが定めるタスクレベル承認判断を受理証跡とする。個別のApproval Record［承認者・承認日・承認参照］は作成していない）
- [x] Review Triggersが記載されている
- [ ] ADR索引と関係領域のDocument Guideへ登録されている（別途確認が必要）
