## Goal

State the migration contract, the pre-migration backup requirement, and the failure behavior in the DB migration document (`REQ-009`, registered upgrades preserve rows; unregistered paths keep the refusal).

## Scope

- Modify only `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`.

## Assumptions

- Verified (Step 3a): section 8 and 8a/8b state create-only DDL for workflow and eventbus, 8e (`Supported Upgrade Baseline`) says no migration code exists for them, and the recreation-impact table says backups are required before recreation; section 9 says evolution is by recreation. Write in English; state intent, boundaries, constraints, and failure behavior only, not implementation detail (`skills/DESIGN.md` Docs content policy). Edit only the sections named below (`docs/00_index.md` task scope: DB layer spec and the ADR index).
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Rewrite 8a, 8b, 8e, and 9 for the two migrating databases; keep the recreate wording for `session`, `rag`, and `mdq`.

## Alternatives considered

- N/A: documentation row.

## Implementation

### Target file

`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure

1. Update 8a and 8b: a registered forward path is migrated behind a verified backup (WAL checkpoint, backup, integrity check); the ledger `schema_migrations` records applied migrations; version and fingerprint prove the state; unknown paths and downgrades are refused.
2. Update 8e's table rows for workflow and eventbus (migration code now exists, removal condition, owner) and section 9.
3. Describe failure behavior: a failed or interrupted migration leaves the original database intact and the ledger unchanged.

### Method

- Link to db_07 section 11 for the operator procedure instead of repeating it.

### Details

- Do not copy function names or flags beyond what the docs content policy allows; point to the CLI modules by path.

## Compatibility considerations

- N/A: documentation.

## Security considerations

- N/A: documentation.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_consistency.py --domain deployment`
- `uv run python tools/check_docs_consistency.py --domain db`

## Completion criteria

- Sections 8a, 8b, 8e, and 9 state the migration contract and failure behavior; the checkers pass.

## Out of Scope

- The drill runbook (row 23) and the ADR (row 20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Procedure | Pending | — | — | Plan Phase 6; after code phases 1-5 |
| 2 | Run the documentation checkers (`routing.md` Tools) | Pending | — | — |  |

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
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md
