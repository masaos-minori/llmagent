## Goal

Update `docs/00_security_01_architecture-and-trust-boundaries.md` to document the EventBus authentication/authorization model as canonical, cross-referencing the new ADR (REQ-001), and noting that loopback-only binding predates this work.

## Scope

- Modify `docs/00_security_01_architecture-and-trust-boundaries.md`:
  - Add a new section documenting the EventBus authentication/authorization model
  - Cross-reference `ADR-013-eventbus-authentication-authorization.md`
  - Note that loopback-only binding predates this work
- No other documentation changes beyond what's listed in the Plan's Implementation Target Files.

## Assumptions

- The current file (287 lines) mentions EventBus only once, in passing (line 59, DB-file protection), with no per-API authn/authz section for it yet.
- The ADR will be created first (REQ-001) before this documentation update.
- Loopback-only binding is already documented elsewhere; this update should note it predates the authentication/authorization work.

## Design decisions

- **Section placement**: Add a new top-level section for EventBus authentication/authorization after existing sections, following the repository's documentation conventions.
- **Cross-references**: Link to `ADR-013-eventbus-authentication-authorization.md` for detailed design decisions.
- **Loopback-only note**: Explicitly state that loopback-only binding predates the authentication/authorization work to avoid confusion about which security boundary was added when.

## Alternatives considered

- Embedding the full authorization model in this document: Would duplicate the ADR; cross-referencing preferred.
- Updating the loopback-only binding description: Would conflate two separate security boundaries; keep them distinct.

## Implementation

### Target file

`docs/00_security_01_architecture-and-trust-boundaries.md`

### Procedure

Modify `docs/00_security_01_architecture-and-trust-boundaries.md` to document the EventBus authentication/authorization model as canonical.

### Method

1. Add a new top-level section `## EventBus Authentication and Authorization`.
2. Document the four-role authorization model (publisher/consumer/operator/monitoring).
3. Cross-reference `ADR-013-eventbus-authentication-authorization.md` for detailed design decisions.
4. Note that loopback-only binding predates this work.

### Details

```markdown
# In docs/00_security_01_architecture-and-trust-boundaries.md — add after existing sections:

## EventBus Authentication and Authorization

The EventBus API enforces authentication and authorization as a fail-closed security boundary.

### Authentication

All EventBus routes require Bearer-token authentication. Requests without a valid
`Authorization: Bearer <token>` header receive HTTP 401 Unauthorized.

See [ADR-013-eventbus-authentication-authorization](adr/ADR-013-eventbus-authentication-authorization.md)
for the authentication mechanism decision and configuration details.

### Authorization

Four roles control access to EventBus routes:

| Role | Access |
|------|--------|
| Publisher | POST `/publish` |
| Consumer | GET `/subscribe`, POST `/events/{event_id}/ack`, POST `/nack` |
| Operator | GET `/dlq`, POST `/dlq/{event_id}/requeue`, GET `/replay` |
| Monitoring | GET `/health` |

A consumer's authenticated identity is bound to allowed `consumer_id`s and topics —
a caller cannot act as another consumer or access unauthorized topics.

DLQ administration (`/dlq`, `/dlq/{event_id}/requeue`) and privileged replay
(`/replay`) require operator permission.

See [ADR-013-eventbus-authentication-authorization](adr/ADR-013-eventbus-authentication-authorization.md)
for the authorization model decision and role definitions.

### Loopback-only Binding

**Note**: The EventBus process already enforces loopback-only binding via
`EventBusConfig.__post_init__` and `_LoopbackVerifyingServer` — both confirmed by
direct read. This predates the authentication/authorization work described above
and remains in effect as defense-in-depth.
```

## Compatibility considerations

- The documentation must follow the repository's documentation conventions (section headers, tags, related front matter).
- Cross-references to the ADR must use the correct relative path from this document's location.

## Security considerations

- **Accurate representation**: The documentation must accurately represent the security model as implemented, not as designed.
- **Loopback-only note**: Must explicitly state that loopback-only binding predates the authentication/authorization work to avoid confusion.

## Rollback considerations

- Rolling back this documentation change means removing the new section and reverting to the previous state where EventBus had no documented authentication/authorization model.

## Validation plan

- Verify the documentation follows the repository's documentation conventions (section headers, tags, related front matter).
- Confirm cross-references to ADR-013 are accurate.
- Run `uv run python tools/check_docs_quality.py` against the file to ensure no quality issues.
- Run `uv run python tools/check_docs_structure.py` against the file to ensure no structural issues.

## Completion criteria

- [ ] New section `## EventBus Authentication and Authorization` added
- [ ] Four-role authorization model documented with route mappings
- [ ] Cross-reference to ADR-013 present
- [ ] Loopback-only binding noted as predating this work
- [ ] Documentation format matches repository conventions
- [ ] No quality issues (verified via `tools/check_docs_quality.py`)
- [ ] No structural issues (verified via `tools/check_docs_structure.py`)

## Out of scope

- Implementing the authentication/authorization code (covered by subsequent implementation procedures).
- Correcting the stale `CI-001` status/Recommended-Action text in `docs/00_governance_03_issue-and-uncertainty-management.md` (pre-existing documentation inconsistency unrelated to this Issue's stated Target Files).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add new section for EventBus authentication/authorization | Pending | — | — | |
| 2 | Document four-role authorization model | Pending | — | — | |
| 3 | Add cross-reference to ADR-013 | Pending | — | — | |
| 4 | Note loopback-only binding predates this work | Pending | — | — | |
| 5 | Validate documentation quality and structure | Pending | — | — | |

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: docs/00_security_01_architecture-and-trust-boundaries.md
