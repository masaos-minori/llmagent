# Implementation Procedure: `tests/eventbus/test_eventbus_auth.py` (EBAUTHGEN001 Phase 2)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-001, REQ-004)

## Goal
Add generation-immutability coverage to the auth suite and extend the existing
secret-leak regression to the new generation/hash fields — extend, do not duplicate.

## Scope
- `test_no_credential_leakage_in_audit_records` `:1272-1315`: captures audit records via
  `patch("eventbus.audit.logger.warning")` `:1291` and asserts each configured token
  string is absent from every record `:1311-1315`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Extend the scenario list `:1283-1286` with an effective admin update (so
   `privileged_action` records with `previous_generation`/`new_generation`/`baseline_hash`
   are captured) and assert every configured token value is absent from those records
   (AC-5). Keep existing scenarios intact.
2. Add one generation-immutability test: the published `AuthzGeneration` carries the
   same `principals` mapping `resolve_principal` consults; two reads of
   `current_generation()` return the identical object between publications (REQ-001).
3. Do not create a new secret-leak test — the plan row says `:1272` test is extended,
   not duplicated (frozen table `:84`).

## Compatibility considerations
**Dependencies**:
- Upstream: docs 01, 06 (generation snapshot, audit fields)
**Blocks**: none

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_auth.py` (row gate).

## Completion criteria
- AC-5 regression-guarded on the new fields; existing suite semantics unchanged.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-141000_01_scripts_eventbus_auth.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- No new constructs introduced by this row; no `(new)` markers applied.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 10
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`
