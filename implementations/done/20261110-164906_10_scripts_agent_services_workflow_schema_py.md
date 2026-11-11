## Goal

Replace `REQUIRED_WORKFLOW_TABLES` and the marker-table refusal in
`scripts/agent/services/workflow_schema.py` with the fingerprint check
(`REQ-003`, `REQ-004`). Keep the refusal text that tells the operator to archive and recreate.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current `check_workflow_schema()` compares a table-name set against `REQUIRED_WORKFLOW_TABLES`
  and refuses on legacy marker tables (`schema_migrations`, `workflow_schema_version`); the
  refusal message is `LEGACY_MARKER_REFUSAL_MESSAGE` (lines 52-120).
- Canonical workflow DDL comes from `db.schema_sql.build_workflow_schema_sql()`.

## Design decisions
- In `check_workflow_schema()`, open the existing database and call `assert_matches(conn, canonical_ddl, label="workflow.sqlite")`; return `SchemaCheckResult(valid=False, error=<archive-and-recreate message>)` on mismatch.
- Delete `REQUIRED_WORKFLOW_TABLES`, `LEGACY_MARKER_TABLES`, and `LEGACY_MARKER_REFUSAL_MESSAGE` once unused; keep the refusal wording (same text) as the fingerprint error.

## Alternatives considered
- Comparing table-name sets inline: rejected; reuse the one mechanism.

## Implementation
### Target file
`scripts/agent/services/workflow_schema.py`

### Procedure
1. Import `assert_matches` from `shared.schema_fingerprint` and the workflow accessor from `db.schema_sql`.
2. Replace the table-set + marker comparison with a fingerprint assertion wrapped in the existing try/except that returns `SchemaCheckResult`.
3. Remove the now-unused constants and message.

### Method
- The database already exists check (`os.path.exists`) stays; after opening read-only, fingerprint with `build_workflow_schema_sql()`.

### Details
- Preserve `SchemaCheckResult` shape so callers (`startup_component_init.py`, a Reference File) are unaffected.

## Compatibility considerations
Callers still get a `SchemaCheckResult`; workflow databases now match full shape, not just names.

## Security considerations
Read-only fingerprint.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/agent/test_repl_health.py -v` and `tests/agent/test_startup_workflow_preflight.py -v` (those rows add fingerprint cases); `uv run pytest tests/agent -v` passes.

## Completion criteria
`check_workflow_schema()` validates by fingerprint; `REQUIRED_WORKFLOW_TABLES`/marker removal complete; refusal text preserved.

## Out of Scope
Changing the workflow schema itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-122315 | fingerprint gate replaces REQUIRED_WORKFLOW_TABLES/marker checks; constants removed; refusal text is shared REFUSAL_MESSAGE |
| 2 | Add or update tests per Validation plan | Completed | — | 20261111-122315 | test_repl_health fixture migrated to canonical DDL + mutations; parity test python-gate-shape case replaced by constants-gone pin (paired row 22 test pulled in) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-122315 | tests/agent+tests/deploy 4270 passed, full suite 12061 passed, pre-commit 25 hooks pass |

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
- **Requirement ID**: `REQ-003` / `REQ-004` — workflow schema validated by fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/agent/services/workflow_schema.py`