## Goal
Replace the sentence about idempotent schema migrations in the EventBus persistence document with the create-only statement (REQ-006).

## Scope
- The sentence "Schema migrations for existing databases are idempotent." in the Schema section.

## Assumptions
- After the code change a database at the current schema is left unchanged and an older one is recreated.

## Design decisions
- New sentence: the schema is created from `schema.sql` when the database is new, an existing database at the current schema is not modified, and an older database is recreated.

## Alternatives considered
N/A: one-sentence docs edit.

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. Replace the sentence with the new create-only statement.

### Method
- Minimal in-place edit; no history wording, no counts.

### Details
- Do not touch the surrounding schema description.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- The document no longer says migrations apply to existing databases; docs checkers pass.

## Out of Scope
- Other sections; the offset-import wording handled by another procedure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the migration sentence | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (docs describe a create-only EventBus schema)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md
