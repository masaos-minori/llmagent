## Goal

- Delete `tests/eventbus/test_eventbus_migrations.py` (769 lines) — the self-test module of the deleted EventBus registry and migration CLI (REQ-007: replace migration tests, delete migration test modules).

## Scope
**Release unit**: current-schema-only-cutover

- Whole-file test deletion, Phase 2. It has its own document (not a companion) because the Plan cites this test path in two rows' Related Tests cells (rows 3 and 4).

## Assumptions

- Its registry-step, ledger-status, and CLI behavior coverage has no replacement; EventBus rejection coverage is owned by the companion tests in document 07 (REQ-007).

## Design decisions

- Delete outright rather than port cases: every test drives deleted framework behavior (Plan row: "Tests the deleted eventbus registry").

## Alternatives considered

- Keeping CLI refusal-class tests: rejected — the CLI is deleted (document 04); refusal behavior is covered through `_init_schema` in document 07's companions.

## Implementation
### Target file
`tests/eventbus/test_eventbus_migrations.py`

### Procedure
1. `git rm tests/eventbus/test_eventbus_migrations.py` in the Phase 2 commit, together with documents 03 and 04 deleting what it tests (Plan Phase 2).

### Method
- No content is preserved or ported.

### Details
- N/A: deletion only.

## Compatibility considerations

- N/A: test-only deletion.

## Security considerations

- N/A: test-only deletion.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `grep -rn "test_eventbus_migrations" tests/ tools/ .github/` — no residual reference.
- `uv run pytest tests/` — collection succeeds after Phases 2-3 land.

## Completion criteria

- The file is absent and the full suite collects without it (AC-003).

## Out of Scope

- Deleting `scripts/eventbus/migrations.py` / `scripts/eventbus/migrate.py` — sibling documents 03, 04.
- EventBus rejection matrix — document 07 companions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git rm tests/eventbus/test_eventbus_migrations.py` with documents 03/04 (Plan Phase 2) | Pending | — | — | Release unit "current-schema-only-cutover" |
| 2 | Verify no residual reference and suite collection (grep + pytest) | Pending | — | — | |

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
- **Related target files**: `tests/eventbus/test_eventbus_migrations.py`
