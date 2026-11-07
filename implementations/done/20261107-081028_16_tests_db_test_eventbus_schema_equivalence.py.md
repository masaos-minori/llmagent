## Goal

- Delete `tests/db/test_eventbus_schema_equivalence.py` (199 lines) — the runner/ledger equivalence test that pins the deleted EventBus framework (REQ-007: delete migration test modules).

## Scope
**Release unit**: current-schema-only-cutover

- Whole-file test deletion, Phase 2. Own document: the Plan names no other row's Related Tests for this file.

## Assumptions

- Canonical-shape equivalence after the cutover is covered by the regenerated fingerprint path (`shared.eventbus_schema_fingerprint`, REQ-008) and document 07's companion matrix — no replacement equivalence harness is needed (Plan Design: "the fingerprint module defines no `MigrationRefusalError`... consolidating refusals onto the single fingerprint validator").

## Design decisions

- The file's remaining value (equivalence of runner output vs ledger) disappears with the framework; its generic DDL-shape assertions are already enforced by `test_init_db_eventbus_schema.py` (dynamic fingerprint derivation, Plan Assumptions).

## Alternatives considered

- Keeping the module minus the framework imports: rejected — the Plan row classifies the whole file as testing the deleted framework (Repository Evidence: imports `eventbus.migrations.REGISTRY`, `shared.db_migrations`).

## Implementation
### Target file
`tests/db/test_eventbus_schema_equivalence.py`

### Procedure
1. `git rm tests/db/test_eventbus_schema_equivalence.py` in the Phase 2 commit (Plan Phase 2).

### Method
- The file imports `from eventbus.migrations import REGISTRY` (line 17) and uses `from db.schema_sql import EVENTBUS_SCHEMA_SQL_PATH, build_eventbus_schema_sql` (line 15) and `from eventbus.schema import _SCHEMA_PATH` (line 18) — the latter two survive, but every test body drives the registry comparison (persisted-schema checklist item 6: this pin test is deleted with the framework, Plan Design).

### Details
- No content is preserved or ported.

## Compatibility considerations

- N/A: test-only deletion.

## Security considerations

- N/A: test-only deletion.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `grep -rn "test_eventbus_schema_equivalence" tests/ tools/ .github/` — no residual reference.
- `uv run pytest tests/` — collection succeeds after Phases 2-3 land.

## Completion criteria

- The file is absent and the full suite collects without it (AC-003).

## Out of Scope

- Deleting `scripts/eventbus/migrations.py` — sibling document 03.
- Fingerprint re-derivation checks — document 09 validation steps.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git rm tests/db/test_eventbus_schema_equivalence.py` (Plan Phase 2) | Completed | — | 20261107-130007 | Release unit "current-schema-only-cutover" git rm executed; grep: no residual references in tests/ tools/ .github/; tests/db+tests/eventbus full run 871 passed (collection errors from these modules gone). |
| 2 | Verify no residual reference and suite collection (grep + pytest) | Completed | — | 20261107-130007 | git rm executed; grep: no residual references in tests/ tools/ .github/; tests/db+tests/eventbus full run 871 passed (collection errors from these modules gone). |

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
- **Requirement ID**: REQ-007 (delete migration test modules)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `tests/db/test_eventbus_schema_equivalence.py`