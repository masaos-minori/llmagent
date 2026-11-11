## Goal

Replace the table-name-only `REQUIRED_WORKFLOW_TABLES` check in
`deploy/setup_services.sh` with the fingerprint gate (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current script checks workflow table names only (`setup_services.sh:55-57`) using
  `REQUIRED_WORKFLOW_TABLES`; no shape comparison.

## Design decisions
- Replace the table-name check with a fingerprint call against the canonical workflow DDL via the generalized module; refuse drift with the archive-and-recreate message.

## Alternatives considered
- Comparing table names inline: rejected; reuse the one mechanism.

## Implementation
### Target file
`deploy/setup_services.sh`

### Procedure
1. Locate the `REQUIRED_WORKFLOW_TABLES` table-name check (lines 55-57).
2. Replace it with a fingerprint assertion against `build_workflow_schema_sql()` via `shared.schema_fingerprint.assert_matches`.
3. Keep the fail-closed deploy contract.

### Method
- Call the fingerprint through the venv (`uv run`) as the rest of the deploy script does; on mismatch abort setup.

### Details
- Ensure the check runs against the deployed workflow.sqlite path read-only.

## Compatibility considerations
Deploy tightening: a workflow DB that passes name-check but not shape is now refused.

## Security considerations
Read-only inspection.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/deploy/test_required_workflow_tables_parity.py -v` (that row re-expresses parity through the canonical DDL); deploy smoke test.

## Completion criteria
`deploy/setup_services.sh` gates workflow by fingerprint; table-name-only check removed.

## Out of Scope
Changing which services deploy.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-141604 | REQUIRED_WORKFLOW_TABLES name-loop replaced by a read-only uv-run fingerprint gate (assert_matches vs build_workflow_schema_sql); fail-closed abort kept |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-141605 | bash -n clean; sandbox integration test fixture now seeds from canonical DDL (build_workflow_schema_sql); tests/deploy 36 passed, full suite 12067 passed (uv run), pre-commit green |

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
- **Requirement ID**: `REQ-003` — workflow deploy gate by fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `deploy/setup_services.sh`