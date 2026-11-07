## Goal

- Delete `tests/db/test_migrations_workflow.py` (1322 lines) — the self-test module of the deleted Workflow migration registry (REQ-007: replace migration tests, delete migration test modules).

## Scope
**Release unit**: current-schema-only-cutover

- Whole-file test deletion, Phase 2. It has its own document (not a companion) because the Plan cites this test path in two rows' Related Tests cells (rows 2 and 5).

## Assumptions

- Its coverage (registry steps, baseline, backup gate, CLI ledger status) has no replacement: rejection coverage lives in sibling documents 18 and 10 test work (REQ-007 replaces migration-success tests with rejection tests, not with registry tests).

## Design decisions

- Delete outright rather than port cases: every test in the module drives deleted framework behavior (Plan row: "Tests the deleted workflow registry").

## Alternatives considered

- Keeping `verify_backup_by_path` tests against `scripts/db/recovery.py`: rejected — the helper under test is deleted (document 02); `recovery.py` has its own existing tests.

## Implementation
### Target file
`tests/db/test_migrations_workflow.py`

### Procedure
1. `git rm tests/db/test_migrations_workflow.py` in the Phase 2 commit, together with document 02 deleting the module it tests (Plan Phase 2).

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

- `grep -rn "test_migrations_workflow" tests/ tools/ .github/` — no residual reference.
- `uv run pytest tests/` — collection succeeds after Phases 2-3 land.

## Completion criteria

- The file is absent and the full suite collects without it (AC-003).

## Out of Scope

- Deleting the module under test — sibling document 02.
- Legacy-marker rejection coverage — documents 10, 14, 18.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git rm tests/db/test_migrations_workflow.py` with document 02 (Plan Phase 2) | Pending | — | — | Release unit "current-schema-only-cutover" |
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
- **Related target files**: `tests/db/test_migrations_workflow.py`
