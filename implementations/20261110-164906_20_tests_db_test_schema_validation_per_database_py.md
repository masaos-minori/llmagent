## Goal

Add per-database drift tests in `tests/db/test_schema_validation_per_database.py` showing that
for each of workflow, eventbus, mcp_dedup, mdq, session, rag the four drift cases fail startup
with the explicit archive-and-recreate error (`REQ-003`, `REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Each domain exposes a create/fingerprint entry point (create_schema, open paths, db_tools.ensure, etc.) and canonical DDL.

## Design decisions
- Parameterize over the six domains; for each, build a baseline database, then apply each of four drifts (missing CHECK, extra legacy table, extra column, missing index) and assert the open/startup path raises the archive-and-recreate error and leaves the file unchanged.

## Alternatives considered
- One test per domain file: rejected; a single parameterized file keeps the four-drift matrix uniform (Plan).

## Implementation
### Target file
`tests/db/test_schema_validation_per_database.py` (new)

### Procedure
1. For each domain, register: the entry callable, the canonical DDL source, and the "existing database" detection.
2. Generate a baseline DB, then four mutated copies; assert each mutation is refused with the explicit error.
3. Assert a clean baseline passes.

### Method
- Use temp files per case; call the real open/startup entry so the test exercises the actual gate.

### Details
- Keep sqlite-vec shadow tables required-by-name so rag/session baselines build without the extension shape.

## Compatibility considerations
New file.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/db/test_schema_validation_per_database.py -v` — four drift cases fail per database with the explicit error.

## Completion criteria
All six databases × four drifts fail with the explicit archive-and-recreate error; clean baselines pass.

## Out of Scope
Unit tests for the fingerprint itself (`tests/shared/test_schema_fingerprint.py`, its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-144344 | test matrix implemented |
| 2 | Add or update tests per Validation plan | Completed | — | 20261111-144344 | 30 cases (6 domains x (4 drifts + clean baseline)) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-144345 | full suite 12097 passed, pre-commit green |

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
- **Requirement ID**: `REQ-003` / `REQ-005` — per-database four-drift tests
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/db/test_schema_validation_per_database.py`