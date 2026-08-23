## Goal

In `tests/db/test_create_schema.py`: update the file's private
`_RAG_SCHEMA_NO_VEC0` fixture DDL string to drop the `DEFAULT` clauses for
`documents.fetched_at`, `chunks.chunk_type`, `chunks.source_file` and to add
the currently-missing `documents.chunking_strategy` column (also
`NOT NULL`, no `DEFAULT`), then add tests asserting that omitting any of
these four columns from an `INSERT` raises `sqlite3.IntegrityError`, while
`etag`/`last_modified`/`normalized_content` still accept `NULL`. Also fix
the one existing test that this DDL change breaks
(`TestTimestampDefaults.test_rag_schema_timestamps`'s `fetched_at`
assertion).

## Scope

- In scope: `tests/db/test_create_schema.py` — the `_RAG_SCHEMA_NO_VEC0`
  constant, the `rag_tmp_db` fixture that consumes it, new integrity-error
  test cases, and the one pre-existing test broken by this change.
- Out of scope: `tests/db/test_db_maintenance.py` and
  `tests/db/test_db_store_impl.py` — each has its own private inline
  schema copy with the same kind of drift; both are separate target files
  of this plan with their own implementation documents (not part of this
  batch's two assigned files).
- Out of scope: `scripts/db/schema_sql.py` itself (the real DDL source),
  `_SESSION_SCHEMA_NO_VEC0`, `_WORKFLOW_SCHEMA_NO_VEC0`,
  `_EVENTBUS_SCHEMA_NO_VEC0`, and every test class in this file that does
  not touch the `documents`/`chunks` tables (`TestCreateSessionSchema`,
  `TestCreateWorkflowSchema`, `TestSchemaDdlErrorPropagation`,
  `TestCreateSchemaWrapper`) — unaffected by this plan.

## Assumptions

- **Direct-read finding, not stated explicitly this way in the plan**: the
  plan's Affected areas table describes this file as a "Real-DDL schema
  test target (uses `build_rag_schema_sql()` via `create_schema.py`)".
  Reading the file shows this is only partially accurate: `rag_tmp_db`
  patches `db.create_schema.build_rag_schema_sql` to return this file's
  own hand-maintained `_RAG_SCHEMA_NO_VEC0` string (a vec0-stripped copy),
  not the real DDL text from `scripts/db/schema_sql.py` directly. This
  file therefore has the same class of private-inline-schema drift risk
  the plan's own Risks section calls out for `tests/db/test_db_maintenance.py`
  — confirmed here by direct comparison: `_RAG_SCHEMA_NO_VEC0`'s
  `documents` table is currently missing the `chunking_strategy` column
  entirely (present in real `schema_sql.py` today, with `DEFAULT 'text'`).
  This document's procedure treats fixing that drift (adding the column)
  as required, not optional, because the new omission tests need the
  column to exist in order to test its `NOT NULL` behavior at all.
- The four target columns' `CHECK` constraints in real `schema_sql.py`
  (`chunk_type IN ('text','code')`, `chunk_index >= 0`, `length(content) >
  0`, `lang IN ('ja','en')`) are not replicated in `_RAG_SCHEMA_NO_VEC0`
  today and this plan's scope (removing `DEFAULT` clauses only) does not
  require adding them; left as-is to avoid scope creep beyond the four
  `DEFAULT` removals plus the missing-column fix needed to test one of
  them.
- **Breaking-test finding, confirmed by direct read**:
  `TestTimestampDefaults.test_rag_schema_timestamps` currently asserts,
  for the `documents` table, `assert default is not None` for the
  `fetched_at` column (i.e., it currently requires `fetched_at` to *have* a
  `DEFAULT`). Once this document's DDL edit removes that `DEFAULT`
  entirely, `PRAGMA table_info(documents)` will report `default is None`
  for `fetched_at`, and this pre-existing assertion will fail. This is not
  mentioned explicitly in the plan's Implementation steps or Affected
  areas table; it was found by reading the test file's current body. This
  document's procedure updates that test as an in-scope, required part of
  the same change (not a separate follow-up), since leaving it would break
  the suite immediately.

## Design decisions

- Fix the `_RAG_SCHEMA_NO_VEC0` string in place (same constant, same
  fixture) rather than switching the fixture to build from the real
  `build_rag_schema_sql()` output with a vec0-stripping regex/filter —
  keeps this change minimal and consistent with how the sibling
  `_SESSION_SCHEMA_NO_VEC0`/`_WORKFLOW_SCHEMA_NO_VEC0`/
  `_EVENTBUS_SCHEMA_NO_VEC0` constants are already maintained in this same
  file (all hand-copied, not derived).
- Add the new integrity-error tests as real `INSERT` attempts against the
  `rag_tmp_db` fixture's live SQLite connection (not `PRAGMA table_info`
  introspection) — a `NOT NULL` constraint is only meaningfully verified by
  attempting to violate it, matching the plan's own stated expected
  outcome ("Omitting any of the 4 columns raises `sqlite3.IntegrityError`").
- Group the four new tests plus the "unaffected columns still accept NULL"
  test into one new test class (e.g. `TestRagSchemaColumnIntegrity`) in
  the same style as the file's existing `TestTimestampDefaults` and
  `TestSchemaDdlErrorPropagation` classes, rather than adding loose
  module-level functions.

## Alternatives considered

- Leave `TestTimestampDefaults.test_rag_schema_timestamps`'s `documents`
  loop untouched and let it fail, treating it as a "known break to fix
  later" — rejected: the plan's Phase 1 explicitly requires running
  `pytest -q tests/db/test_create_schema.py tests/db/test_db_maintenance.py`
  and expects it to pass; a self-inflicted regression in the same file
  this plan edits is not acceptable.
- Derive `_RAG_SCHEMA_NO_VEC0` dynamically from `scripts/db/schema_sql.py`'s
  real `build_rag_schema_sql()` output via string-filtering out the
  `CREATE VIRTUAL TABLE ... vec0` statement — would eliminate this file's
  drift risk permanently, but is a larger refactor than this plan's scope
  (touches the fixture's construction strategy, not just its DDL text) and
  risks brittleness if the real DDL's vec0 statement text changes shape;
  rejected for this change, noted as a possible future improvement.
- Only remove the three `DEFAULT` clauses already present
  (`fetched_at`, `chunk_type`, `source_file`) and skip adding
  `chunking_strategy` to the fixture (treating it as pre-existing,
  unrelated drift) — rejected: the plan explicitly requires testing
  omission of `chunking_strategy` too, which is impossible if the column
  does not exist in the fixture at all.

## Implementation

### Target file

`tests/db/test_create_schema.py`

### Procedure

1. In `_RAG_SCHEMA_NO_VEC0`'s `documents` table definition:
   - Change `fetched_at TEXT NOT NULL DEFAULT (datetime('now'))` to
     `fetched_at TEXT NOT NULL` (drop the `DEFAULT` clause; keep
     `NOT NULL`).
   - Add a new column, `chunking_strategy TEXT NOT NULL` (no `DEFAULT`),
     matching the column real `schema_sql.py` already has for `documents`
     (there with `DEFAULT 'text'`, here with no default per this plan).
2. In `_RAG_SCHEMA_NO_VEC0`'s `chunks` table definition:
   - Change `chunk_type TEXT NOT NULL DEFAULT 'text'` to
     `chunk_type TEXT NOT NULL`.
   - Change `source_file TEXT NOT NULL DEFAULT ''` to
     `source_file TEXT NOT NULL`.
   - Leave `normalized_content TEXT` (nullable, no `DEFAULT`) unchanged.
3. Leave `documents.etag`, `documents.last_modified` (both nullable, no
   `DEFAULT`) unchanged.
4. Add a new test class, e.g. `TestRagSchemaColumnIntegrity`, using the
   `rag_tmp_db` fixture, with:
   - Four tests, one per target column (`fetched_at`, `chunking_strategy`,
     `chunk_type`, `source_file`): attempt an `INSERT INTO documents`/
     `INSERT INTO chunks` that omits the column under test (supplying
     valid values for every other `NOT NULL` column) and assert
     `pytest.raises(sqlite3.IntegrityError)`.
   - One test confirming `etag`, `last_modified` (via `INSERT INTO
     documents` with those two columns passed as `NULL`) and
     `normalized_content` (via `INSERT INTO chunks` with it passed as
     `NULL`) still insert successfully with `NULL` values — i.e., these
     three remain nullable and unaffected by this plan.
5. Fix the now-breaking assertion in
   `TestTimestampDefaults.test_rag_schema_timestamps`: remove the
   `for table in ("documents",):` loop's `fetched_at`-specific
   `assert default is not None` expectation, since `fetched_at` no longer
   has any `DEFAULT` after step 1. Either drop the `documents` table from
   this test's loop entirely (since `fetched_at` was the only `_at`-suffixed
   column on that table this loop was checking) or keep the loop but skip
   asserting a non-`None` default for `fetched_at` specifically, with a
   comment explaining that `fetched_at` intentionally has no `DEFAULT` as
   of this plan. Do not simply delete the test class — it still has
   meaningful coverage for `sessions`/`messages`/`memories`/
   `session_diagnostics`/workflow/eventbus tables.
6. Optional, low-risk addition: extend the existing
   `test_documents_columns` test's expected column set to include
   `chunking_strategy` (it currently asserts a subset via `<=`, so this is
   additive and does not change existing behavior); not required by the
   plan's explicit text but keeps this test's documented column list
   accurate.

### Method

Direct edits to the module-level DDL string constant plus new
`pytest`-style test functions/class in the same file; no new imports
needed beyond what is already imported (`sqlite3`, `pytest`).

### Details

- The new omission tests must supply valid, constraint-satisfying values
  for every column *other* than the one under test, including
  `documents.url` (`UNIQUE NOT NULL`) and `documents.lang` — the fixture's
  `_RAG_SCHEMA_NO_VEC0` does not replicate the real DDL's `CHECK (lang IN
  ('ja','en'))`, so any non-null string is accepted by this fixture, but
  using a realistic value (e.g. `'en'`) keeps the test forward-compatible
  if the fixture is later tightened.
- `sqlite3.IntegrityError` is the correct exception for a `NOT NULL`
  constraint violation in Python's `sqlite3` module (not
  `sqlite3.OperationalError`); this matches the plan's stated expected
  outcome and the module's existing use of `sqlite3.IntegrityError` in
  `TestCreateWorkflowSchema.test_tasks_idempotency_key_unique`.
- After this change, `_RAG_SCHEMA_NO_VEC0` and the real
  `scripts/db/schema_sql.py` DDL are aligned only for the four columns
  this plan touches, plus the pre-existing `chunking_strategy` gap this
  document also closes. Other latent drift between the fixture and the
  real DDL (e.g. missing `CHECK` constraints) is out of scope and remains
  a known risk, consistent with the plan's own Risk on private schema
  copies.

## Compatibility considerations

- `rag_tmp_db` is used by every test in `TestCreateRagSchema` — adding a
  `NOT NULL` column with no `DEFAULT` to the fixture's `documents` table
  does not by itself break any existing `TestCreateRagSchema` test, since
  none of them perform an `INSERT`; they only inspect table/column
  existence via `sqlite_master`/`PRAGMA table_info`.
- `TestTimestampDefaults.test_rag_schema_timestamps` is the one exception
  (see Assumptions/Procedure step 5) — it must be updated in the same
  change, not separately, to avoid landing a self-breaking commit.
- No interaction with `TestCreateSessionSchema`, `TestCreateWorkflowSchema`,
  `TestSchemaDdlErrorPropagation`, or `TestCreateSchemaWrapper` — none use
  `_RAG_SCHEMA_NO_VEC0`.

## Security considerations

N/A: this is a test-only file exercising DDL and parameterized test
fixtures against a temporary on-disk SQLite file (`tmp_path`); no
production code path, external input, or credential handling is involved.

## Rollback considerations

- Revert is self-contained to this one file; no other file's tests depend
  on `_RAG_SCHEMA_NO_VEC0`'s shape.
- Reverting this file's DDL edit while `scripts/db/schema_sql.py`'s real
  `DEFAULT` removal (separate target file in this plan) has already landed
  would leave this file's fixture *more* permissive than the real schema
  (accepting `NULL` fetched_at/chunking_strategy where the real DB would
  reject it) — meaning the fixture would stop giving accurate regression
  coverage for the plan's acceptance criteria, though it would not error.
  Revert both together if reverting either.
- No production data or migration implications — this file only creates
  and drops temporary SQLite files under `tmp_path`.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py -v` — all existing tests
  pass (including the fixed `test_rag_schema_timestamps`), and the new
  `TestRagSchemaColumnIntegrity` tests confirm: omitting any of
  `fetched_at`/`chunking_strategy`/`chunk_type`/`source_file` raises
  `sqlite3.IntegrityError`; `etag`/`last_modified`/`normalized_content`
  still accept `NULL`.
- `uv run pytest -q tests/db/test_create_schema.py tests/db/test_db_maintenance.py`
  — the plan's own Phase 1 combined verification command.
- Manual cross-check: `rg -n "chunking_strategy" tests/db/test_create_schema.py`
  should show the new column in both the fixture DDL and at least one new
  test after this change (zero matches today, confirmed before this edit).

## Out of scope

- `tests/db/test_db_maintenance.py`'s own private inline schema copy
  (separate target file, own implementation document).
- `tests/db/test_db_store_impl.py`'s `_DOCUMENT_SCHEMA` fixture (separate
  target file, own implementation document).
- Replacing `_RAG_SCHEMA_NO_VEC0` with a derived-from-real-DDL fixture
  (noted as a rejected alternative above, not this plan's scope).
- Adding the real DDL's `CHECK` constraints to the fixture — not required
  by this plan's stated column-omission tests.

## Execution Status

##### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created
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
- Related target files: tests/db/test_create_schema.py
