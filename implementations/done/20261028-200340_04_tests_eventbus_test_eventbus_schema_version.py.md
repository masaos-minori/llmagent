## Goal
Pin the eventbus schema version to 2, prove a new database carries
`idx_events_redelivered_from` (new), and prove a database stamped 1 is refused, so the
version/index contract of seq 01 is locked by tests written first (REQ-001, REQ-003,
REQ-004).

## Scope
- Edit `tests/eventbus/test_eventbus_schema_version.py` only: three new test functions.
- Reference only: `scripts/eventbus/schema.sql` (seq 01), `scripts/eventbus/schema.py`
  (`_init_schema` refusal path), `scripts/db/schema_sql.py` (`eventbus_schema_version`).

## Assumptions
- All 5 existing tests read the version dynamically via `eventbus_schema_version()`
  (verified this cycle: lines 29, 35, 55); none pins a number, so the file needs
  additions, not edits — except this document adds the first pinned assertion.
- `test_mismatched_version_is_refused` stamps 99 (line 42), so the 1 → 2 bump does
  not break it.
- The three new tests fail before seq 01 lands (Plan Phase 1): the pinned assertion
  sees 1, the index query finds no such index, and a 1-stamped database currently
  passes the version gate.

## Design decisions
- Pin `eventbus_schema_version() == 2` as a literal in a new test rather than
  changing the dynamic tests: the dynamic tests stay robust against future bumps;
  the literal is the contract lock for this Plan (AC-1).
- The 1-stamped refusal test stamps an existing (current-shape) database down to 1
  rather than building old DDL: `_init_schema` compares the stamped version before
  any shape logic, so stamping 1 on a current file isolates exactly the version-gate
  contract of REQ-003 without duplicating legacy DDL in the test.
- Index assertion queries `sqlite_master` for the exact index name and checks
  `UNIQUE` and the partial `WHERE redelivered_from IS NOT NULL` clause in the stored
  SQL, not just presence, so a non-unique or non-partial mistake in seq 01 fails here.

## Alternatives considered
- Editing the dynamic assertions to hardcode 2: rejected — three tests would then
  need re-editing on the next version bump; one pinned test expresses the contract.
- Building a hand-written legacy v1 DDL in the refusal test: rejected — duplicates
  `schema.sql` text inside a test and drifts on every future change.

## Implementation
### Target file
`tests/eventbus/test_eventbus_schema_version.py`

### Procedure
1. Add `test_schema_version_is_pinned_to_two()` (new):
   `assert eventbus_schema_version() == 2`.
2. Add `test_new_database_has_redelivered_from_index(tmp_path)` (new):
   - `open_db(str(path)).close()` on a fresh file.
   - Reopen with `sqlite3.connect`, read
     `SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_events_redelivered_from'`.
   - Assert the row exists, `"UNIQUE" in sql`, and
     `"WHERE redelivered_from IS NOT NULL" in sql`.
3. Add `test_database_stamped_one_is_refused(tmp_path)` (new):
   - `open_db(str(path)).close()` (creates and stamps the current version).
   - `raw = sqlite3.connect(path); raw.execute("PRAGMA user_version = 1"); raw.close()`.
   - `with pytest.raises(RuntimeError, match="recreate the database"): open_db(str(path))`.
4. Extend the module docstring (lines 3-5) with one sentence naming the pinned
   version 2 and the refused 1-stamped legacy case.

### Method
Append the three functions after the existing tests, reusing the file's existing
helpers and import set (`sqlite3`, `Path`, `pytest`, `eventbus_schema_version`,
`open_db`) — no new imports are required.

### Details
- The refusal message comes from `scripts/eventbus/schema.py` `_init_schema`
  ("...recreate the database"), the same gate `open_db` runs; the test matches the
  stable substring `"recreate the database"` as `test_mismatched_version_is_refused`
  already does (line 44).
- `sqlite_master.sql` for a partial unique index contains the literal
  `CREATE UNIQUE INDEX ... WHERE redelivered_from IS NOT NULL` text as written in
  `schema.sql` (whitespace-normalized by SQLite); assert substrings, not full equality.

## Compatibility considerations
- Existing 5 tests stay byte-identical.
- `test_mismatched_version_is_refused` (stamps 99) and
  `test_unstamped_old_shape_is_refused_and_left_unstamped` (stamps 0, old DDL) stay
  green across the bump.

## Security considerations
N/A: fixed SQL in tests, parameterless statements.

## Rollback considerations
N/A: delete the three added test functions on revert; the pinned assertion then
matches the reverted version 1 automatically.

## Validation plan
- Before seq 01: `uv run pytest tests/eventbus/test_eventbus_schema_version.py -q`
  shows the three new tests failing (Plan Phase 1 "fail before the change").
- After seq 01: same command all green.
- Regression: `uv run pytest tests/eventbus tests/db tests/deploy -q`.

## Completion criteria
- `eventbus_schema_version() == 2` is asserted as a literal.
- A fresh `open_db` database provably carries the unique partial index.
- A 1-stamped database raises with "recreate the database" from `open_db`.
- The 5 pre-existing tests are untouched and green.

## Out of Scope
`schema.sql` itself (seq 01), the fingerprint missing-index test
(`tests/db/test_create_schema.py`, seq 05), dlq behavior tests (seq 03), docs (seq 06-08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-210500 | 20261028-210600 | 3 pinned/index/refusal tests added; docstring extended |
| 2 | Add or update tests per Validation plan | Completed | 20261028-210500 | 20261028-210600 | This document's change IS the tests This document's change IS the tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-210600 | 20261028-210630 | Run red before seq 01, green after Phase-1 red as planned: 3 new tests fail before seq 01, existing 5 pass; ruff+format+mypy clean. Green re-run after seq 01 lands |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Docs handled by seq 06-08 Out of scope: docs handled by seq 06-08 |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-004 (pinned version 2, index presence, 1-stamped refusal)
- **Source issue**: issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-200340
- **Related target files**: tests/eventbus/test_eventbus_schema_version.py