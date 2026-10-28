## Goal
Keep the hand-written eventbus DDL copy in `tests/db/test_create_schema.py` in sync
with seq 01's new index, and add the missing-index fingerprint assertion for
`idx_events_redelivered_from` (new) itself (REQ-001, REQ-004).

## Scope
- Edit `tests/db/test_create_schema.py` only: one line added to
  `_EVENTBUS_SCHEMA_NO_VEC0` and one new test method in
  `TestEventbusSchemaFingerprint`.
- Reference only: `scripts/eventbus/schema.sql` (seq 01),
  `scripts/shared/eventbus_schema_fingerprint.py` (no code change),
  `scripts/db/create_schema.py` (no code change).

## Assumptions
- `_EVENTBUS_SCHEMA_NO_VEC0` (line 117) carries no `PRAGMA user_version` line today
  (verified this cycle), and its two consumers — `test_eventbus_schema_timestamps`
  (patched at line 908 via `return_value`) and
  `test_create_eventbus_schema_produces_new_tables` (patched at line 953 via
  `side_effect = lambda: _EVENTBUS_SCHEMA_NO_VEC0 + extra_ddl`) — assert table
  presence and column defaults only, never the version stamp; therefore the sync
  needed is the index line, and no version line is introduced (adding one would
  change what the patched create-flow tests exercise).
- `test_missing_index_raises` (line 1131) already removes `idx_events_dlq_seq` from
  `_CANONICAL_EVENTBUS_DDL` and expects `events: indexes differ` — verified this
  cycle; the new test adds the same proof for the new index, not a new mechanism.
- `_CANONICAL_EVENTBUS_DDL` (line 1077) is `build_eventbus_schema_sql()`, i.e. the
  raw `schema.sql` text; `str.replace` targets must match the statement as seq 01
  writes it (one line, exact spacing).

## Design decisions
- New test `test_missing_redelivered_from_index_raises` (new) clones the shape of the
  existing `test_missing_index_raises` (DDL text removal + `_apply_eventbus_ddl` +
  `pytest.raises(RuntimeError, match="events: indexes differ")`): the assertion
  proves the fingerprint layer sees the new index, satisfying AC-1's "fingerprint
  validation fails when the index is removed" without touching
  `eventbus_schema_version()`-dynamic tests.
- No `PRAGMA user_version` line added to `_EVENTBUS_SCHEMA_NO_VEC0`: the copy's
  unstamped behavior is what the two patched tests already tolerate
  (`create_eventbus_schema()` runs `assert_matches` only when the events table
  already exists — verified in `scripts/db/create_schema.py` lines 104-129).

## Alternatives considered
- Asserting the new index inside `test_missing_index_raises` itself: rejected — one
  test removing one index keeps failures specific; a separate named test also names
  the constraint this Plan introduces.
- Extending `_EVENTBUS_SCHEMA_NO_VEC0` into a byte-copy of schema.sql: rejected —
  the copy exists precisely to be a minimal shape for the patched tests; only the
  new index is required to keep it from building a stale shape.

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. In `_EVENTBUS_SCHEMA_NO_VEC0` (line 117), after
   `CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);` add the
   exact statement seq 01 adds to `schema.sql`:
   `CREATE UNIQUE INDEX IF NOT EXISTS idx_events_redelivered_from ON events(redelivered_from) WHERE redelivered_from IS NOT NULL;`
2. In `class TestEventbusSchemaFingerprint`, after `test_missing_index_raises`
   (lines 1131-1139), add `test_missing_redelivered_from_index_raises` (new):
   - `ddl = _CANONICAL_EVENTBUS_DDL.replace("<the exact one-line statement from step 1>", "")`
   - `conn = _apply_eventbus_ddl(ddl)`
   - `with pytest.raises(RuntimeError, match="events: indexes differ"): assert_matches(conn, label="test-missing-redelivered-index")`
   - `finally: conn.close()`

### Method
Two localized text edits; reuse the file's existing helpers
(`_apply_eventbus_ddl`, `_CANONICAL_EVENTBUS_DDL`, `assert_matches`) — no new
imports.

### Details
- `_CANONICAL_EVENTBUS_DDL` is built dynamically, so this test passes only after
  seq 01 lands (Plan Phase 2 ordering: seq 01 precedes this test's first green run).
- `build_fingerprint` reads index facts from the applied database
  (`PRAGMA index_list`/`index_info` semantics, including unique and partial flags),
  so the removal shows up as an index-set difference with the existing
  `events: indexes differ` message.

## Compatibility considerations
- The two patched create-flow tests keep their current assertions and stay green
  once the copy carries the new index; their `extra_ddl` concat at line 953 is
  untouched.
- `TestEventbusSchemaFingerprint`'s canonical tests (`test_canonical_database_matches_expected_fingerprint`,
  `test_in_memory_apply_matches_disk_apply`) build from `schema.sql` dynamically and
  pick up the new index automatically from seq 01 — no edits.

## Security considerations
N/A: fixed DDL strings in tests.

## Rollback considerations
N/A: revert the two edits with the commit; the dynamic `_CANONICAL_EVENTBUS_DDL`
tracks the reverted `schema.sql` automatically.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py -q` — before seq 01 the new test
  fails (the replace target text is absent, so nothing is removed and
  `assert_matches` passes unexpectedly: a red phase); after seq 01 it passes.
- `uv run pytest tests/eventbus tests/db tests/deploy -q`.
- `uv run python tools/check_db_separation.py`.

## Completion criteria
- `_EVENTBUS_SCHEMA_NO_VEC0` contains the `idx_events_redelivered_from` (new) statement
  identical to the one seq 01 adds to `schema.sql`.
- `test_missing_redelivered_from_index_raises` (new) raises with
  `events: indexes differ` when the index line is removed.
- All pre-existing tests in the file stay green.

## Out of Scope
`schema.sql` (seq 01), `scripts/shared/eventbus_schema_fingerprint.py` and
`scripts/db/create_schema.py` (no change), version-pin tests (seq 04), docs (seq 06-08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-213500 | 20261028-213600 | Land after seq 01 index line added to _EVENTBUS_SCHEMA_NO_VEC0; test_missing_redelivered_from_index_raises added |
| 2 | Add or update tests per Validation plan | Completed | 20261028-213600 | 20261028-213700 | This document's change IS the tests This document's change IS the tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-213600 | 20261028-213700 | seq 01 already landed: 68/68 green including the new fingerprint test; ruff+format clean; check_db_separation ran green in the seq 01 cycle |
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
- **Requirement ID**: REQ-001 (DDL copy sync), REQ-004 (missing-index fingerprint proof)
- **Source issue**: issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-200340
- **Related target files**: tests/db/test_create_schema.py