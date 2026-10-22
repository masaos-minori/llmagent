## Goal
Remove the `_migrate()` clause and the incremental-migration decision-target mention from the EventBus paragraph of the schema reference (REQ-006).

## Scope
- The EventBus paragraph only; the workflow paragraph is edited by a sibling procedure.

## Assumptions
- The Canonical Source Registry entry for `eventbus.persistence-schema.incremental-migration` is removed by the registry procedure of this Plan, so no document may cite it afterwards (verified: this paragraph is the only citation).
- The bootstrap decision target (`eventbus.persistence-schema.bootstrap-ddl`) stays.

## Design decisions
- Keep the statement that `schema.sql` is the only DDL definition read by the bootstrap and by the service when `events` is missing; delete the clause naming `_migrate()` and its decision target.

## Alternatives considered
N/A: one-paragraph docs edit.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure
1. In the EventBus paragraph delete "and `scripts/eventbus/schema.py::_migrate()` (incremental migration at service startup, reached via `open_db()` ...; Decision Target `eventbus.persistence-schema.incremental-migration`)" and fix the grammar of the remaining sentence.

### Method
- Minimal edit; keep links to ADR-008 and `eventbus_06`.
- Re-read the file before editing: the workflow procedure edits another paragraph.

### Details
- Do not add a history sentence.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`; `rg "persistence-schema.incremental-migration" docs config` returns no match after the registry procedure lands.

## Completion criteria
- The paragraph names no `_migrate()` and no removed decision target; docs checkers pass.

## Out of Scope
- The workflow paragraph and other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `_migrate()` clause and decision-target mention | Pending | — | — | |
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
- **Related target files**: docs/41_db/db_02_architecture_and_schema-schema-reference.md
