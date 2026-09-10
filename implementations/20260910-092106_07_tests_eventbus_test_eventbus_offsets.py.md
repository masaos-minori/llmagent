## Goal
Add tests for the new SQLite-backed offset read/write path and legacy-file migration
idempotency, including a synthetic multi-consumer legacy directory and a legacy file
with no `.map` companion (REQ-002, REQ-004).

## Scope
In scope: new test functions/classes in this file only. Out of scope: modifying
existing tests that exercise today's file-based `read_offset()`/`write_offset()`
directly (`test_ack_writes_offset`, `TestConsumerIdSanitization`,
`TestOffsetMonotonicity`) — these continue to test the retained legacy functions and
must keep passing unmodified.

## Assumptions
- `make_eventbus_client()` (from `tests/eventbus/eventbus_helpers.py`, a Reference
  File) provides per-test `tmp_path`-based `offsets_dir`/`db_path` isolation, reused as
  is — no helper change needed since migration tests can pre-populate `tmp_path /
  "offsets"` before client creation.
- `get_consumer_offset()`/`migrate_legacy_offsets()` (row 03) are importable from
  `eventbus.db` for direct unit-style assertions, in addition to HTTP-level assertions
  via the test client.

## Design decisions
Add:
1. A test asserting `get_consumer_offset()` returns `0` for an unmigrated consumer and
   the correct value after `migrate_legacy_offsets()` runs against a synthetic
   `offsets_dir` containing one offset file + its `.map` companion.
2. A test asserting monotonic enforcement at the SQL level: two sequential calls to
   the offset-advancement path with a decreasing `seq` leave the higher value in place
   (mirrors `TestOffsetMonotonicity`'s existing intent, but against the new table).
3. A test asserting `migrate_legacy_offsets()` is idempotent: running it twice against
   the same `offsets_dir` produces the same `consumer_offsets` row count and values
   (AC-5).
4. A test covering a legacy offset file with no `.map` companion: `migrate_legacy_offsets()`
   falls back to the sanitized filename as `consumer_id` and logs a warning, without
   raising (UNK-02).
5. A test with a synthetic multi-consumer legacy directory (multiple `.map`/offset
   file pairs) confirming every consumer is migrated correctly in one pass.

## Alternatives considered
Parametrizing all new cases into the existing `TestOffsetMonotonicity`/
`TestConsumerIdSanitization` classes was considered and rejected: those classes test
the legacy file-based functions specifically (by name and by their existing docstring
intent); mixing new SQLite-path assertions into them would blur which functions each
class is regression-testing.

## Implementation
### Target file
`tests/eventbus/test_eventbus_offsets.py`

### Procedure
1. Add a new test class (e.g. `TestConsumerOffsetsTable`) covering
   `get_consumer_offset()`/the new atomic advancement path directly against a
   `sqlite3.Connection` (no HTTP layer needed for these).
2. Add a new test class (e.g. `TestLegacyOffsetMigration`) covering
   `migrate_legacy_offsets()`: idempotency, multi-consumer directory, and the
   no-`.map`-companion fallback.
3. Reuse `make_eventbus_client()`'s `tmp_path`-based isolation pattern already used by
   the existing tests in this file for any test needing a real `offsets_dir` on disk.

### Method
`pytest` test functions/classes, following this file's existing style (plain
`def test_*` functions and grouped `class Test*` blocks).

### Details
```python
class TestConsumerOffsetsTable:
    def test_get_consumer_offset_defaults_to_zero(self, eventbus_db_conn):
        assert get_consumer_offset(eventbus_db_conn, "consumer-a") == 0

    def test_ack_event_for_consumer_advances_offset(self, eventbus_db_conn):
        ...  # insert an event, call ack_event_for_consumer, assert offset advanced

    def test_offset_does_not_regress_on_older_seq(self, eventbus_db_conn):
        ...  # advance to seq=5, then attempt seq=3, assert still 5


class TestLegacyOffsetMigration:
    def test_migration_is_idempotent(self, tmp_path):
        ...  # populate offsets_dir, run migrate_legacy_offsets twice, assert same result

    def test_migration_multi_consumer(self, tmp_path):
        ...  # multiple .map/offset file pairs, assert all migrated

    def test_migration_missing_map_companion_falls_back(self, tmp_path, caplog):
        ...  # offset file with no .map, assert fallback consumer_id + warning logged
```
Fixture names (`eventbus_db_conn`, etc.) must match whatever conftest/fixture pattern
this test module and `tests/eventbus/eventbus_helpers.py` already establish — confirm
the exact fixture name at implementation time rather than inventing a new one.

## Compatibility considerations
No existing test in this file is modified — only new tests are added, preserving the
regression coverage for the retained legacy `read_offset()`/`write_offset()` path.

## Security considerations
Test-only file; no production security surface.

## Rollback considerations
Revert this file's diff to remove the new tests; no production behavior depends on
this file.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_offsets.py -v` — all existing and new
tests pass.

## Completion criteria
All five new test cases (offset defaults to zero, advancement, monotonic
non-regression, migration idempotency, multi-consumer migration, no-`.map`-companion
fallback) pass, and all pre-existing tests in this file continue to pass unmodified.

## Out of scope
Any change to the production code these tests exercise (rows 01-06) — this row is
test-only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestConsumerOffsetsTable` (defaults, advancement, non-regression) | Pending | — | — | |
| 2 | Add `TestLegacyOffsetMigration` (idempotency, multi-consumer, no-.map fallback) | Pending | — | — | |
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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: tests/eventbus/test_eventbus_offsets.py
