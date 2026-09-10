## Goal

Create `docs/adr/ADR-013-eventbus-authentication-authorization.md` recording the EventBus authentication mechanism (static Bearer token), the four-role authorization model (publisher/consumer/operator/monitoring), the privileged-replay scope decision (UNK-01), and an explicit note that the ConfigLoader migration question is already resolved by ADR-002's local-invariant exception.

## Scope

- Document-only: no code changes. This document records design decisions before implementation begins.
- Covers: authentication mechanism choice, authorization model definition, privileged-replay scope boundary, and ConfigLoader exception reference.

## Assumptions

- The next unused ADR number is `ADR-013` (not the vacated `ADR-011` slot) — inferred from this repository's Known-Issue ID-non-reuse convention applied by analogy to ADRs, since no explicit ADR-numbering-reuse policy was found in `docs/adr-index.md`.
- ADR-002's embedded CI-001 note (lines 363-375) already documents and accepts the EventBus cannot import ConfigLoader exception — this Plan's Design section confirms this.
- "Privileged replay" means all `/replay` calls require operator permission (simplest interpretation consistent with the Issue's Required Changes and Acceptance Criteria).

## Design decisions

- **Authentication mechanism**: Static Bearer token, mirroring `scripts/mcp_servers/server.py::attach_auth_middleware()` pattern — a FastAPI `@app.middleware("http")` function checking `request.headers.get("Authorization", "")` against a configured token.
- **Authorization model**: Four roles — publisher, consumer, operator, monitoring — each granted a fixed subset of routes. Consumer identity bound to allowed `consumer_id`s and topics.
- **Privileged replay scope**: All `/replay` calls require operator permission (resolves UNK-01).
- **ConfigLoader migration**: Explicitly not pursued; already resolved by ADR-002's local-invariant exception.

## Alternatives considered

- Rotatable service tokens: Would require token rotation infrastructure; static token sufficient for loopback-only deployment.
- Mutual TLS: Overkill for loopback-only binding; adds operational complexity without security benefit.
- Reverse-proxy authentication: Would shift trust boundary; loopback-only makes this unnecessary.
- Migrating to `ConfigLoader`: Architecturally prohibited by `.importlinter` `eventbus-is-isolated` contract; ADR-002 already accepted this exception.

## Implementation

### Target file

`docs/adr/ADR-013-eventbus-authentication-authorization.md`

### Procedure

Create a new Architecture Decision Record documenting the authentication/authorization design decisions for the EventBus API.

### Method

1. Create the ADR file following the repository's ADR format conventions (see `docs/adr/` existing files for style).
2. Include sections covering: context, decision, consequences, and references to related ADRs.
3. Cross-reference `ADR-002-config-isolation.md`'s embedded CI-001 note as the resolution for the ConfigLoader migration question.
4. Document the four-role authorization model with a table showing which role can access which route category.
5. Record the privileged-replay scope decision (all `/replay` requires operator permission) as the resolution to UNK-01.

### Details

The ADR should include:

- **Context**: No authentication/authorization exists on any EventBus route; every caller can act as any `consumer_id`, access any topic, administer the DLQ, and trigger replay.
- **Decision**: Adopt static Bearer-token authentication + four-role authorization model.
- **Consequences**:
  - Positive: Fail-closed security boundary; clear separation of concerns between roles.
  - Negative: Reimplementation of Bearer-token and audit patterns locally (cannot import from `mcp_servers` per isolation contract); risk of silent behavioral drift between implementations over time.
- **References**: `EVENTBUS-008`, `CI-001`, `ADR-002-config-isolation.md`, `ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`.

## Compatibility considerations

- This ADR does not change runtime behavior; it only records decisions that will be implemented later.
- The ConfigLoader exception reference must explicitly cite ADR-002's own embedded CI-001 note (lines 363-375) as the authoritative resolution.

## Security considerations

- The ADR must note that a missing or empty `auth_token` in `config/eventbus.toml` could silently disable authentication if the middleware follows `attach_auth_middleware()`'s exact empty-token-means-skip fallback.
- Mitigation: `REQ-005` makes `auth_token` a required, non-empty key in `load_config()` (fail-closed at config-load time, before the middleware ever runs).
- Audit logging must never record secret/token values — documented explicitly.

## Rollback considerations

- Rolling back this ADR would mean reverting to no authentication/authorization, which is the current state.
- The ADR itself is documentation-only; rollback is simply deleting the file.
- Runtime rollback of the implementation (if needed) would involve removing the auth middleware, reverting route-level permission checks, and restoring the original `load_config()` behavior.

## Validation plan

- Verify the ADR follows the repository's ADR format conventions (section headers, status, tags).
- Confirm cross-references to ADR-002, EVENTBUS-008, and CI-001 are accurate.
- Confirm the four-role authorization model table is complete and unambiguous.
- Run `uv run python tools/check_docs_quality.py` against the file to ensure no quality issues.

## Completion criteria

- [ ] File created at `docs/adr/ADR-013-eventbus-authentication-authorization.md`
- [ ] Authentication mechanism (static Bearer token) clearly documented
- [ ] Four-role authorization model defined with route-to-role mappings
- [ ] Privileged-replay scope decision recorded (all `/replay` requires operator permission)
- [ ] ConfigLoader exception explicitly referenced to ADR-002's CI-001 note
- [ ] Cross-references to related ADRs and Known Issues present
- [ ] ADR format matches repository conventions (verified via comparison with existing ADRs)

## Out of scope

- Implementing the authentication/authorization code (covered by subsequent implementation procedures).
- Choosing between static bearer token / rotatable service token / mutual TLS / reverse-proxy authentication as an open research question — this Plan resolves it to static bearer token.
- Correcting the stale `CI-001` status/Recommended-Action text in `docs/00_governance_03_issue-and-uncertainty-management.md` (pre-existing documentation inconsistency unrelated to this Issue's stated Target Files).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the ADR document | Completed | — | — | |
| 2 | Validate ADR format and cross-references | Completed | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: docs/adr/ADR-013-eventbus-authentication-authorization.md
