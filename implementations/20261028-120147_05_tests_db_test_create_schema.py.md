# Procedure: add the missing-unique-index fingerprint test and update the DDL copy

## Goal

Add a fingerprint test for the removed unique index and add the index to the hand-written `_EVENTBUS_SCHEMA_NO_VEC0` copy (Plan REQ-004).

## Scope

- Modify only `tests/db/test_create_schema.py`.
- Test-only change; no source file is edited.

## Assumptions

- Ordering note: write the new test before row 1; the DDL-copy edit lands with it.
- Overlap (compatible): `plans/done/20261028-093931_adrgate005_enforce-adr-evidence-checks.md` (archived, procedures pending) also targets the ADR-006 file; it renames two stale test citations in the Verification table while this procedure edits Implementation Notes only. Any citation added here must resolve to an existing test node once that Plan's node validation is in force.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/db/test_create_schema.py`

### Procedure

- In `TestEventbusSchemaFingerprint`, add `test_missing_unique_redelivery_index_raises` (new): replace `CREATE UNIQUE INDEX IF NOT EXISTS idx_events_redelivered_from ON events(redelivered_from) WHERE redelivered_from IS NOT NULL;` with an empty string in `_CANONICAL_EVENTBUS_DDL`, apply it and assert `assert_matches` raises `RuntimeError` matching `events: indexes differ`.
- In `_EVENTBUS_SCHEMA_NO_VEC0`, add the same `CREATE UNIQUE INDEX ...` statement after the `idx_events_dlq_seq` line so the tests that patch `build_eventbus_schema_sql` with this copy still satisfy `assert_matches`.
- Read the consumers of `_EVENTBUS_SCHEMA_NO_VEC0` (the patched tests near `TestEventbusSchemaCreation` and the redelivered-from column test) and confirm none asserts an index list that would now differ (UNK-03).

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- `_CANONICAL_EVENTBUS_DDL` is read from `schema.sql`, so it picks up the index automatically once row 1 lands.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/db/test_create_schema.py -q` | Pass |
| 2 | `uv run ruff format tests/db/test_create_schema.py`; `uv run ruff check tests/db/test_create_schema.py` | No finding |

## Completion criteria

- The fingerprint test passes and every test that uses the DDL copy still passes.

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
- **Requirement ID**: REQ-001, REQ-004 (fingerprint detects the index; test DDL copy)
- **Source issue**: issues/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120147
- **Related target files**: tests/db/test_create_schema.py
