# Procedure: add the version-1 refusal test and assert the index on a new database

## Goal

Prove a version-1 database is refused and a new database carries the index at version 2 (Plan REQ-003, REQ-004).

## Scope

- Modify only `tests/eventbus/test_eventbus_schema_version.py`.
- Test-only change; no source file is edited.

## Assumptions

- Ordering note: apply this row before the source rows (tests first).
- Overlap (compatible): `plans/done/20261028-093931_adrgate005_enforce-adr-evidence-checks.md` (archived, procedures pending) also targets the ADR-006 file; it renames two stale test citations in the Verification table while this procedure edits Implementation Notes only. Any citation added here must resolve to an existing test node once that Plan's node validation is in force.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_schema_version.py`

### Procedure

- Add `test_version_one_database_is_refused` (new): create a database with `open_db`, then in a raw connection `DROP INDEX idx_events_redelivered_from` and `PRAGMA user_version = 1`; assert `open_db` raises `RuntimeError` matching "recreate the database".
- Extend `test_new_database_is_stamped` (or add `test_new_database_has_the_redelivery_unique_index` (new)) to assert `sqlite_master` lists `idx_events_redelivered_from` as a unique index and the stamp equals `eventbus_schema_version()` (2).

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Write before row 1; both fail on the unmodified schema.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_schema_version.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_schema_version.py`; `uv run ruff check tests/eventbus/test_eventbus_schema_version.py` | No finding |

## Completion criteria

- The version gate and index assertions fail before row 1 and pass after.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-004 (version gate)
- **Source issue**: issues/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120147
- **Related target files**: tests/eventbus/test_eventbus_schema_version.py
