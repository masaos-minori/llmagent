## Goal

Make `scripts/db/create_schema.py` validate-first for every database: a fresh file receives
the canonical DDL, an existing one is checked by fingerprint and refused unchanged on any
difference (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current `create_rag_schema`/`create_session_schema`/`create_workflow_schema` only execute
  DDL on a fresh file and never fingerprint an existing one (verified: they call
  `_execute_schema_ddl` then return). The workflow marker-table refusal lives in
  `workflow_schema.py`, not here.
- Canonical DDL comes from `scripts/db/schema_sql.py` accessors (its row).

## Design decisions
- After opening each database in write mode, if the domain's primary table already exists, call the generalized `assert_matches(conn, canonical_ddl, label=...)` before committing; on refusal raise the archive-and-recreate error and leave the file unchanged (no partial write).
- Keep the fresh-file path (execute DDL) unchanged.

## Alternatives considered
- Leaving existence-only checks for session/rag: replaced by fingerprint (see those rows, REQ-003).

## Implementation
### Target file
`scripts/db/create_schema.py`

### Procedure
1. Import `assert_matches` from `shared.schema_fingerprint` and the domain accessors from `db.schema_sql`.
2. In each `create_*_schema()`: after opening, detect an existing database (primary table present) and fingerprint it with the canonical DDL before executing anything; refuse on mismatch.
3. On refusal, do not commit and re-raise so the caller exits non-zero with the file untouched.

### Method
- For rag: primary table `documents`; session: `sessions`; workflow: `tasks`. Use presence of the domain table as the "existing" signal (matches how `eventbus/schema.py` keys off `events`).
- Pass the canonical DDL text from `build_<domain>_schema_sql()` as the fingerprint input.

### Details
- The fingerprint runs inside the open connection but before `db.commit()`; a raised `RuntimeError` aborts without persisting DDL.

## Compatibility considerations
Existing matching databases behave the same; mismatched ones are now refused (previously session/rag were existence-only).

## Security considerations
Read-only fingerprint before any write; refusal leaves data intact.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/db/test_create_schema.py -v` (that row replaces the eventbus `user_version` cases with fingerprint cases); `uv run pytest tests/db -v` passes.

## Completion criteria
Each `create_*_schema()` fingerprints an existing database with canonical DDL and refuses drift without writing.

## Out of Scope
Creating/changing the DDL objects; the workflow marker-table removal (its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` / `REQ-004` — validate-first for every database via fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/db/create_schema.py`
