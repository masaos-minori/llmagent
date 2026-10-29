# Implementation Procedure: tests/eventbus/test_eventbus_schema_version.py (Published-at ownership procedure 7)

## Goal

Pin the new schema version: update the `user_version` pin test from 2 to 3.

## Scope

- Update `test_schema_version_is_pinned_to_two` (and its comment) in
  `tests/eventbus/test_eventbus_schema_version.py` to assert `user_version = 3`.

## Assumptions

- The file pins 2 at `:71-73` (`test_schema_version_is_pinned_to_two`, whose docstring
  reads "schema.sql must stamp PRAGMA user_version = 2"); the version 3 reason is the
  enforced `date-time` format check (`rfc3339-validator`).
- Row 3 raises `PRAGMA user_version` in `schema.sql` to 3 in the same cycle.
- `eventbus_schema_version()` (`scripts/db/schema_sql.py:227`) and
  `_expected_schema_version()` (`scripts/eventbus/schema.py`) both parse the PRAGMA line
  from `schema.sql`, so no constant edit is needed outside the test.

## Design decisions

- Rename the test to `test_schema_version_is_pinned_to_three` (new) so the name matches the
  pinned value.

## Alternatives considered

- Keep the test name and only change the number (rejected: the name would state a false
  value).

## Implementation
### Target file
`tests/eventbus/test_eventbus_schema_version.py`

### Procedure
1. Rename `test_schema_version_is_pinned_to_two` to `test_schema_version_is_pinned_to_three` (new).
2. Change `assert eventbus_schema_version() == 2` to `== 3` and update the test docstring
   to state version 3.
3. Update the module docstring (`:7-8`): version 2 was the
   `idx_events_redelivered_from` unique index bump; version 3 records the enforced
   `date-time` format check (`rfc3339-validator`) and the removal of the dead
   `published_at` schema default.

### Method
Inline edit; keep the tmp_path database fixtures unchanged.

### Details
- The other tests in the file derive expectations from `eventbus_schema_version()` and
  need no changes.

## Compatibility considerations

- Tests that create databases via `schema.sql` will report 3 automatically once row 3
  lands; this test is the pin that catches drift.

## Security considerations

- None specific.

## Rollback considerations

- Restore the 2 pin together with the row 3 rollback.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_schema_version.py -q`

## Completion criteria

- Fresh database reports and pins version 3; all schema-version tests green.

## Out of Scope

- Migration of existing databases (operational, plan Step 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261029-154000 | 20261029-160102 | Module docstring also updated per Procedure step 3. |
| 2 | Add or update tests per Validation plan | Completed | 20261029-154000 | 20261029-160102 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-154000 | 20261029-160102 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261029-154000 | 20261029-160102 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261028-122454_ebpubat006_published-at-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-233320_ebpubat006_published-at-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-103639
- **Related target files**: tests/eventbus/test_eventbus_schema_version.py