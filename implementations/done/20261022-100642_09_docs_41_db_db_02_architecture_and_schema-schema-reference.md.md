## Goal
Update the workflow paragraph of the schema reference so the version-record behavior and the recovery wording match the create-only bootstrap (REQ-007).

## Scope
- The sentences on `create_workflow_schema()` version insertion and "Recovery" in the workflow paragraph only.

## Assumptions
- After the code change `create_workflow_schema()` records the version when the log is empty, does nothing at the current version, and refuses to record over a different latest version.
- Recovery for a mismatch is recreating the database (documented in `db_07` section 11).

## Design decisions
- Describe behavior, not code: version log is append-only; creation refuses to overwrite a different version; recovery is recreation.

## Alternatives considered
N/A: one-paragraph docs edit.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure
1. Replace "`create_workflow_schema()` inserts only when the latest version differs from the `WORKFLOW_SCHEMA_VERSION` constant (idempotent)" with the new behavior.
2. Replace "Recovery: re-run deploy/init_db.sh or call create_workflow_schema() directly." with a pointer to recreating the database (link to the `db_07` section 11 recreation procedure).

### Method
- Minimal in-place edit of those two sentences; keep the rest of the paragraph.
- Re-read the file before editing: the EventBus removal procedure edits another paragraph of it.

### Details
- Use an existing valid anchor for the `db_07` link (`#11-db-recreation-procedure`, as used in `db_03`).

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- The paragraph no longer says the initializer inserts on any difference or that recovery is re-running the initializer, and the link resolves.

## Out of Scope
- The EventBus paragraph and other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the version-record and recovery sentences | Completed | 20261022-105311 | 20261022-105311 | Changed: docs/41_db/db_02_architecture_and_schema-schema-reference.md |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-105311 | 20261022-105311 | validated; docs checkers pass; full suite 9690 passed |

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
- **Requirement ID**: `REQ-007` (docs describe recreate-on-mismatch)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: docs/41_db/db_02_architecture_and_schema-schema-reference.md