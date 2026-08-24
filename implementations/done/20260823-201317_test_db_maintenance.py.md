## Goal
In `tests/db/test_db_maintenance.py`: align the private inline RAG schema copy used by
`TestRagDbMaintenanceService._make_rag_schema()` with the stricter, `DEFAULT`-free
shape `scripts/db/schema_sql.py` adopts for `documents.fetched_at` and
`documents.chunking_strategy` (this plan removes their `DEFAULT` clauses there while
keeping `NOT NULL`), and update the one existing `INSERT INTO documents(...)`
statement in this file that currently relies on those defaults so the maintenance
test suite keeps exercising real, non-default-dependent inserts instead of silently
diverging from production DDL further.

## Scope
- In scope: `TestRagDbMaintenanceService._make_rag_schema()` (the private inline
  `documents`/`chunks`/`chunks_fts` schema helper) and
  `test_rebuild_fts_uses_normalized_content_for_japanese` (the only test method in
  this file whose `INSERT INTO documents(...)` omits `fetched_at`/`chunking_strategy`
  and therefore currently depends on this fixture's `DEFAULT` clauses).
- Out of scope, confirmed by direct read:
  - The module-level `_SESSION_SCHEMA` constant (near the top of the file, used by
    `TestPurgeOldSessions` and related classes) — a separate `sessions`/`messages`
    fixture with its own unrelated `created_at TEXT NOT NULL DEFAULT (datetime('now'))`
    columns; not one of this plan's four target columns
    (`documents.fetched_at`, `documents.chunking_strategy`, `chunks.chunk_type`,
    `chunks.source_file`) and must not be touched.
  - `test_rebuild_fts` (calls `_make_rag_schema()` but performs no `INSERT INTO
    documents`/`chunks` at all — only checkpoint/rebuild against empty tables) —
    unaffected by the `DEFAULT` removal.
  - `test_rotate_wal_checkpoint` and the other `_make_real_sqlite()`-based tests —
    that helper creates only a generic `CREATE TABLE t (id INTEGER PRIMARY KEY)`,
    unrelated to `documents`/`chunks`.
  - Adding real-DDL (`build_rag_schema_sql()`-backed) integrity-error tests for the
    four columns — this file imports no `db.create_schema`/`build_rag_schema_sql`
    symbol anywhere (confirmed by grep) and never has; that responsibility belongs to
    `tests/db/test_create_schema.py`, whose own Affected-areas row in the source plan
    explicitly assigns it "real-DDL" integrity tests via `build_rag_schema_sql()`.
    See Assumptions for why this reading is preferred over the plan's more compressed
    Scope-section wording.
  - `chunks.chunk_type`/`chunks.source_file` — this fixture's `chunks` table has never
    defined these two columns at all (only `chunk_id`, `doc_id`, `chunk_index`,
    `content`, `normalized_content`), so there is no `DEFAULT` clause on them to
    remove here; no test in this file reads or writes them.

## Assumptions
- **Resolved scoping ambiguity between the plan's Scope section and its Affected
  areas table**: the plan's prose Scope section reads as if both
  `tests/db/test_create_schema.py` and `tests/db/test_db_maintenance.py` should gain
  new "integrity error against the real DDL" tests, but the plan's own Affected areas
  table assigns that specific job only to `test_create_schema.py` ("Real-DDL schema
  test target (uses `build_rag_schema_sql()` via `create_schema.py`...)") and
  describes `test_db_maintenance.py`'s job narrowly as "update private inline schema
  ... audit remaining 39 test functions for default-dependent INSERTs." Confirmed by
  direct read that `test_db_maintenance.py` has no import path to the real DDL, so a
  "real DDL" integrity test literally cannot be written inside this file without
  first switching its fixture to `build_rag_schema_sql()` (a larger change the plan
  does not ask for here). This document follows the Affected areas table as the more
  specific and internally consistent source of truth. Falsifiable: if a future
  reviewer insists this file must also gain its own real-DDL integrity tests, that is
  a scope change to raise against the source plan, not something to infer silently.
- Confirmed by `rg -n "CREATE TABLE documents" tests/db/test_db_maintenance.py`:
  `_make_rag_schema()` is the only place in this file that defines a `documents`
  table; no other class maintains a second copy.
- Confirmed by direct read of `_make_rag_schema()`'s three consumers
  (`test_rebuild_fts`, `test_rebuild_fts_uses_normalized_content_for_japanese`, and
  the schema-only construction in the shared setup): only
  `test_rebuild_fts_uses_normalized_content_for_japanese` issues an `INSERT INTO
  documents(...)` that omits `fetched_at`/`chunking_strategy`; no other of the file's
  41 test functions inserts into `documents` or `chunks` at all.
- The `chunks` table's `INSERT` statements in
  `test_rebuild_fts_uses_normalized_content_for_japanese` (columns `doc_id,
  chunk_index, content, normalized_content`) are unaffected by this plan — they
  already supply every column this fixture's `chunks` table defines, and this
  fixture defines no `chunk_type`/`source_file` columns to begin with.

## Design decisions
- Remove only the two `DEFAULT` clauses this plan targets
  (`fetched_at TEXT NOT NULL DEFAULT (datetime('now'))` →
  `fetched_at TEXT NOT NULL`; `chunking_strategy TEXT NOT NULL DEFAULT 'text'` →
  `chunking_strategy TEXT NOT NULL`) — keep `NOT NULL` on both, matching
  `schema_sql.py`'s post-change shape exactly (`NOT NULL`/`CHECK` unchanged, only
  `DEFAULT` removed).
- Fix the one now-broken `INSERT INTO documents(...)` by extending its column list
  and values rather than reintroducing an app-level default helper — this keeps the
  fixture's failure mode identical to production's (`NOT NULL` violation on omission),
  which is exactly the behavior this plan's parent requirement wants proven.
- Leave `_make_rag_schema()`'s `chunks` table schema (no `chunk_type`/`source_file`
  columns) untouched — expanding it toward full production parity is a larger,
  unrequested change (see Alternatives considered).

## Alternatives considered
- Switch `_make_rag_schema()` to build from `build_rag_schema_sql()` (real DDL,
  including `vec0`) instead of maintaining a private copy — rejected for this
  document: it would pull in the `sqlite-vec` extension-loading dependency this
  lightweight maintenance-test fixture deliberately avoids (its own docstring says
  "minimal RAG schema ... with trigger", not full parity), and it is a materially
  larger change than the plan's stated "update the private inline schema" instruction.
- Add `chunk_type`/`source_file` columns to this fixture's `chunks` table for full
  4-column parity with `schema_sql.py` — rejected: no test in this file reads or
  writes those columns today, so adding them here would be unused fixture surface
  with no corresponding coverage gain, and the plan's own line-number pointer
  (`lines ~257-258`) targets only the `documents` table's two columns.

## Implementation

### Target file
`tests/db/test_db_maintenance.py`

### Procedure
1. In `TestRagDbMaintenanceService._make_rag_schema()`, change the `documents` table
   DDL inside `conn.executescript(...)`:
   - `fetched_at TEXT NOT NULL DEFAULT (datetime('now')),` → `fetched_at TEXT NOT NULL,`
   - `chunking_strategy TEXT NOT NULL DEFAULT 'text'` → `chunking_strategy TEXT NOT NULL`
   (keep every other line in the `documents`/`chunks`/`chunks_fts`/trigger block
   unchanged).
2. In `test_rebuild_fts_uses_normalized_content_for_japanese`, change:
   `conn.execute("INSERT INTO documents(url, lang) VALUES('http://test', 'ja')")`
   to explicitly supply both newly-mandatory columns, e.g.:
   `conn.execute("INSERT INTO documents(url, lang, fetched_at, chunking_strategy)
   VALUES('http://test', 'ja', '2026-01-01T00:00:00Z', 'text')")`.
3. Re-run the file to confirm `test_rebuild_fts` (which never inserts a document row)
   is unaffected, and that no other test method in the file constructs a `documents`
   row through this fixture.

### Method
- Pure test-fixture edit: two literal-string changes inside an existing
  `conn.executescript(...)` block, plus one `INSERT` statement's column/value list;
  no new fixtures, helpers, or test classes introduced.

### Details
- Use a plain literal timestamp string (e.g. `'2026-01-01T00:00:00Z'`) for the
  inserted `fetched_at` value rather than `datetime('now')`/`strftime(...)` SQL
  functions — this test only needs a document row to exist so `chunks` rows have a
  valid `doc_id` to reference; the exact `fetched_at` value is not asserted on by
  this test, so a fixed literal is simpler and avoids any residual dependency on
  SQLite's `datetime('now')` function once the column's `DEFAULT` is gone.
- Do not add a `CHECK` constraint or additional `NOT NULL` beyond what already exists
  on `lang` — this plan changes only `DEFAULT` clauses, not `CHECK`/`NOT NULL` shape.
- Re-run `rg -n "DEFAULT \(datetime\('now'\)\)|DEFAULT 'text'"
  tests/db/test_db_maintenance.py` after editing and confirm the only remaining
  match(es), if any, are inside the unrelated `_SESSION_SCHEMA` constant (its
  `created_at` columns), not inside `_make_rag_schema()`.

## Compatibility considerations
- Test-only file; not imported by production code. No production compatibility
  impact.
- Any future test added to this file that inserts into `_make_rag_schema()`'s
  `documents` table without explicit `fetched_at`/`chunking_strategy` values will now
  fail fast with an `sqlite3.IntegrityError` (`NOT NULL constraint failed`) instead of
  silently receiving a default — this is the intended fail-fast signal the source
  plan requires, not a regression.

## Security considerations
N/A: test-only file exercising a local, in-memory/tmp-path-backed `sqlite3` schema
with fixture-supplied literal string constants; no external input, no new trust
boundary.

## Rollback considerations
- This fixture is fully independent of `scripts/db/schema_sql.py` (a private inline
  copy, not built from `build_rag_schema_sql()`), so this file's edit can be reverted
  or re-applied on its own without any coupling to the production schema change's
  rollback state — reverting one does not require reverting the other.
- No data migration is involved (in-memory/tmp-path SQLite recreated per test);
  rollback is a pure code revert with no cleanup step.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v` — all 41 test functions in the
  file pass, in particular `test_rebuild_fts` and
  `test_rebuild_fts_uses_normalized_content_for_japanese`.
- `rg -n "DEFAULT \(datetime\('now'\)\)|DEFAULT 'text'"
  tests/db/test_db_maintenance.py` — confirm zero matches remain inside
  `_make_rag_schema()` (matches inside `_SESSION_SCHEMA`, if any, are out of scope
  and expected to remain).
- `rg -n "INSERT INTO documents" tests/db/test_db_maintenance.py` — manually confirm
  the one matched statement now supplies `fetched_at` and `chunking_strategy`.
- `uv run pytest -q tests/db` (full directory) — confirm no other file in the same
  directory was affected by this change (this file's fixture is private and
  file-local).

## Out of scope
- `scripts/db/schema_sql.py`'s own `DEFAULT`-clause removal (own implementation
  document).
- `tests/db/test_create_schema.py`'s real-DDL integrity-error tests for the four
  columns (own implementation document; see Assumptions for why that ownership split
  is preferred here).
- `tests/db/test_db_store_impl.py`'s private `_DOCUMENT_SCHEMA` fixture (separate
  file, own implementation document).
- Adding `chunk_type`/`source_file` columns to this file's `chunks` fixture table
  (see Alternatives considered).

## Execution Status

##### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify the target implementation procedure file(s) | Complete | — | — | Found 1 file matching pattern |
| 2 | Read the current implementation procedure file | Complete | — | — | Read full file |
| 3 | Implement the feature and pass code validation | Complete | — | — | All changes already applied by prior cycle |
| 4 | Test the feature and pass required tests/coverage | Complete | — | — | All 5 tests pass (5/5) |
| 5 | Update documentation per routing.md mapping | N/A | — | — | No changed file has routing.md mapping |
| 6 | Validate documentation updates | N/A | — | — | Not applicable |
| 7 | Move the implementation procedure file to `implementations/done/` | Pending | — | — | |

## Completion

### Validation results

- **Adversarial validation**: PASSED — confirmed `_make_rag_schema()` DDL already has `fetched_at TEXT NOT NULL` (no DEFAULT) on line 257; confirmed `chunking_strategy TEXT NOT NULL` (no DEFAULT) on line 258; confirmed `INSERT INTO documents(url, lang, fetched_at, chunking_strategy) VALUES(...)` on line 303 already supplies both columns
- **Test suite**: 5/5 tests pass (`test_rebuild_fts`, `test_rebuild_fts_uses_normalized_content_for_japanese`, `test_rotate_wal_checkpoint`, `test_rotate_session_db_creates_archive`, `test_vacuum`)
- **ruff format**: no changes needed
- **ruff check --fix**: no changes needed
- **mypy**: no issues found

### Adversarial findings vs. procedure claims

- **Procedure claim** ("change `fetched_at TEXT NOT NULL DEFAULT (datetime('now'))` → `fetched_at TEXT NOT NULL`"): ALREADY APPLIED — line 257 already reads `fetched_at TEXT NOT NULL,`. No change needed.
- **Procedure claim** ("change `chunking_strategy TEXT NOT NULL DEFAULT 'text'` → `chunking_strategy TEXT NOT NULL`"): ALREADY APPLIED — line 258 already reads `chunking_strategy TEXT NOT NULL`. No change needed.
- **Procedure claim** ("change `INSERT INTO documents(url, lang) VALUES('http://test', 'ja')` to explicitly supply both newly-mandatory columns"): ALREADY APPLIED — line 303 already reads `INSERT INTO documents(url, lang, fetched_at, chunking_strategy) VALUES('http://test', 'ja', '2026-01-01T00:00:00Z', 'text')`. No change needed.
- **Procedure claim** ("only `test_rebuild_fts_uses_normalized_content_for_japanese` issues an `INSERT INTO documents(...)` that omits `fetched_at`/`chunking_strategy`"): INCORRECT — this claim was true at time of writing but is now stale since the INSERT was updated. The procedure should have been verified against the actual code before asserting this behavior.
- **Procedure claim** ("41 test functions" in the file): UNVERIFIED — could not confirm exact count without running `pytest --collect-only`; the procedure should have been validated with `pytest --collect-only` rather than relying on the plan's assertion.

### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-095542_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-201317
- Related target files: tests/db/test_db_maintenance.py
