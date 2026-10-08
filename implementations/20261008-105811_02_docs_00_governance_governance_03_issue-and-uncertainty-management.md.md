## Goal
Register EVENTBUS-016 in the Known Issue ledger so ADR-013 can cite it (REQ-006 of the Plan: new Known Issue).

## Scope
- Add one row to the Active Items table and one detail section, both directly after the EVENTBUS-015 entries.
- No other ledger entry changes.

## Assumptions
- The ID EVENTBUS-016 is still free (re-check immediately before editing; the `kiledger01` issue may also allocate IDs).
- Owner stays `Unassigned`; First Found is the date `2026-10-08`, matching the entries registered earlier in this series.
- The defect is described from route introspection of the production app and the absence of authentication calls in the two handlers.

## Design decisions
- Severity High (security-sensitive: publish and health reachable without a token); Type implementation-bug.
- Related points to EVENTBUS-015 (both concern the EventBus authorization model).

## Alternatives considered
- Fold the finding into EVENTBUS-008: rejected; it concerns consumer-identity allowlists, not missing route dependencies.

## Implementation
### Target file
docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Procedure
1. Confirm `EVENTBUS-016` is absent and EVENTBUS-015 exists.
2. Insert the table row after the EVENTBUS-015 row.
3. Insert the detail section after the EVENTBUS-015 section (before the closing sentence "Other Known Issue IDs are not tracked here").
4. Run the validation commands.

### Method
Two targeted insertions; no restructuring.

### Details
Table row: `| EVENTBUS-016 | /health and /publish are registered without a role dependency | open | High | EventBus | implementation-bug |`.
Detail section fields: Title "/health and /publish are registered without a role dependency"; Status open; Severity High; Area EventBus; Type implementation-bug; Source `scripts/eventbus/app.py`; Owner Unassigned; First Found 2026-10-08; Target `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`; Related `EVENTBUS-015`; Summary: every EventBus route except these two has a role dependency, while these two accept requests without a token; Current Description: ADR-013 INV-01 requires every route to reject unauthenticated requests and the health reference requires the Monitoring role; Observed Implementation: the route registration attaches no dependency to either route, their handlers call no authentication helper, and the authentication tests use a fixture app that adds the dependencies itself; Impact: any local process that can reach the loopback port can publish events and read health state without a token; Recommended Action: add the Publisher and Monitoring role dependencies to the two routes and test them against the production app; Resolution Target: both routes reject missing or wrong-role tokens in a test against the production app.

## Compatibility considerations
- ADR-013 will cite this ID; the sync checker requires it to exist. The file size grows beyond the current ceiling; procedure 03 raises the ceiling.

## Security considerations
- Describes a missing control without exploit steps or secrets.

## Rollback considerations
- Documentation only; revert the commit.

## Validation plan
- `uv run python tools/check_issue_inventory_conformance.py`; `uv run python tools/check_known_deviation_sync.py`; after procedure 03, `uv run python tools/check_docs_structure.py`.

## Completion criteria
- EVENTBUS-016 exists with all 17 fields in table and detail form, after EVENTBUS-015, and the inventory checker passes (REQ-006).

## Out of scope
- Fixing the defect in code; other entries; Owner assignment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the EVENTBUS-016 row and section | Completed | 20261008-110226 | 20261008-110226 |  |
| 2 | Run the inventory and sync checkers | Completed | 20261008-110226 | 20261008-110226 |  |

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
- **Requirement ID**: REQ-006 (register EVENTBUS-016)
- **Source issue**: issues/20261008-094500_adr013fix_fix-adr-013-role-token-model-and-auth-description.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-103440_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-105811
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md