## Goal
In `tests/db/test_db_store_impl.py`: add an explicit `fetched_at` argument to every
`SQLiteDocumentStore.doc_upsert()` call site (currently positional, 5 args, no
`fetched_at`), matching the mandatory 6th parameter added to
`DocumentStore.doc_upsert()` / `SQLiteDocumentStore.doc_upsert()` in
`scripts/db/store_protocols.py` / `scripts/db/store_impl.py`; extend the existing
round-trip test to assert the supplied value is what comes back (not a "now"-derived
value); and add one new test proving `doc_upsert()`'s `ON CONFLICT ... DO UPDATE`
path writes the caller-supplied `fetched_at` literally, not `strftime('now')`.

## Scope
- In scope: `tests/db/test_db_store_impl.py` only — the `TestSQLiteDocumentStore`
  class's `doc_upsert()` call sites, its private `_DOCUMENT_SCHEMA` fixture constant,
  and the two test-assertion additions described in Goal.
- Out of scope: `scripts/db/store_protocols.py` / `scripts/db/store_impl.py` (own
  implementation documents; this file's edits depend on their `doc_upsert()` signature
  change landing first); `TestSQLiteSessionStore`, `TestSQLiteVectorStore`,
  `TestSQLiteMemoryDeleteStore` classes in the same file (no `doc_upsert()` calls,
  untouched); `scripts/db/schema_sql.py` (own implementation document; this file's
  `_DOCUMENT_SCHEMA` is a private in-memory fixture, not the production schema).

## Assumptions
- Confirmed by direct `grep -n "doc_upsert(" tests/db/test_db_store_impl.py`: **13**
  call sites across 10 test methods, not the 12 the source plan's Assumptions and
  Affected-areas sections state — **correction, recorded here for the implementer**:
  `test_doc_list_returns_inserted_documents`, `test_doc_list_filtered_by_lang`, and
  `test_doc_list_returns_lang_as_str` each call `doc_upsert()` twice (one per URL
  fixture: `http://a.com`, `http://b.com`), which brings the total to 13. All 13 must
  receive the new argument; the plan's "12" figure appears to be an off-by-one count.
- The plan's Affected-areas table describes this file's "1 existing `fetched_at`
  reference" as a "return-row assertion" — confirmed by reading the file this is
  inaccurate: the only existing `fetched_at` text in the file is the
  `_DOCUMENT_SCHEMA` constant's column definition (`fetched_at TEXT DEFAULT
  (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))`), not an assertion. No test in this file
  currently asserts on a `fetched_at` value.
- `SQLiteDocumentStore.doc_upsert()`'s new mandatory `fetched_at: str` parameter is
  appended after `last_modified` (the store's own implementation document defines the
  exact position); this document assumes call sites pass it either as a trailing
  positional argument or as `fetched_at=...` keyword — either is acceptable Python,
  keyword form is used below for readability at call sites that already read
  awkwardly with 5 positional args.
- `DocumentRow.fetched_at` is already returned by `doc_get()`/`doc_list()` (confirmed
  by reading `_row_to_document()` in `store_impl.py`), so asserting on
  `result.fetched_at` in this file requires no new plumbing.

## Design decisions
- Introduce two module-level string constants (e.g. `_FETCHED_AT` and
  `_FETCHED_AT_UPDATED`) instead of repeating a literal timestamp string at all 13
  call sites — a single canonical value used by default keeps the diff readable and
  gives one place to change the literal format later; a second, distinct constant is
  needed only for the new update-path test.
- Extend the existing `test_doc_upsert_and_get_roundtrip` test with one additional
  assertion (`result.fetched_at == _FETCHED_AT`) rather than adding a new "insert
  stores fetched_at" test — the round-trip mechanics this test already exercises
  (upsert, then get, then assert on the returned fields) are exactly what an
  insert-path fetched_at assertion needs; adding the one assertion line is smaller
  than a parallel new test.
- Add exactly one new test for the `ON CONFLICT ... DO UPDATE` path
  (`fetched_at = ?`, no `strftime(...)` substitution) — this is the one behavior in
  the plan's Validation plan row for `store_impl.py` ("stored value equals the
  supplied value, not 'now'") that no existing test in this file covers even after
  the 13 call sites gain an argument, since none of them upsert the same URL twice
  with two different `fetched_at` values.
- Also remove the `DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))` clause from the
  file's private `_DOCUMENT_SCHEMA` constant (keep the column, keep it nullable — this
  fixture does not otherwise enforce `NOT NULL` on any column) — this is the file's
  one flagged existing `fetched_at` reference, and leaving a stale `DEFAULT` clause
  that no longer reflects `schema_sql.py`'s post-change shape would misdescribe
  production behavior to a future reader of this fixture, even though the clause is
  never exercised once every `doc_upsert()` call supplies the column explicitly.

## Alternatives considered
- Hardcoding the same literal timestamp string inline at each of the 13 call sites
  instead of a shared constant — rejected: 13 duplicated literals with no shared name
  make a future format change (e.g. adjusting the canonical UTC pattern) an
  error-prone find-and-replace across the file.
- Leaving `_DOCUMENT_SCHEMA`'s `DEFAULT (strftime(...))` clause in place on the
  reasoning that it is now unreachable dead code and therefore harmless — rejected:
  the plan explicitly flags this exact clause as this file's one pre-existing
  `fetched_at` touchpoint, and `scripts/db/schema_sql.py`'s sibling implementation
  document removes the equivalent clause from the production schema; leaving this
  fixture out of sync invites a reader to believe the production default still exists.
- Adding a brand-new, separate test class or module purely for the update-path
  assertion — rejected: one additional method inside the existing
  `TestSQLiteDocumentStore` class, next to `test_doc_upsert_and_get_roundtrip`, is
  sufficient; no new fixtures or helpers are needed beyond the existing
  `_make_doc_db()`/`SQLiteDocumentStore` pattern already used throughout the class.

## Implementation
### Target file
`tests/db/test_db_store_impl.py`

### Procedure
1. Near the top of the file (after the `_DOCUMENT_SCHEMA`/`_SESSION_SCHEMA` constants,
   before `_FakeDB`), add two module-level constants:
   `_FETCHED_AT = "2026-01-01T00:00:00Z"` and
   `_FETCHED_AT_UPDATED = "2026-02-02T00:00:00Z"`.
2. In `_DOCUMENT_SCHEMA`, change the `fetched_at` column definition from
   `fetched_at   TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))` to
   `fetched_at   TEXT` (drop the `DEFAULT` clause; no other column in this fixture is
   `NOT NULL` either, so leave `fetched_at` nullable at the fixture level — the
   Python-level mandatory parameter is what enforces presence in practice).
3. In `TestSQLiteDocumentStore`, add `fetched_at=_FETCHED_AT` (or the equivalent
   positional value in the new parameter position) to the `doc_upsert()` call in each
   of the following methods: `test_doc_upsert_new_url_returns_positive_id`,
   `test_doc_upsert_and_get_roundtrip`, `test_doc_get_returns_lang_as_str`,
   `test_chunk_insert_increments_count`,
   `test_chunk_insert_stores_chunk_type_and_source_file`,
   `test_chunk_insert_defaults_to_empty_strings`,
   `test_doc_delete_removes_document_and_returns_true`.
4. In `test_doc_list_returns_inserted_documents`, `test_doc_list_filtered_by_lang`,
   and `test_doc_list_returns_lang_as_str`, add `fetched_at=_FETCHED_AT` to **both**
   `doc_upsert()` calls in each method (the `http://a.com` and `http://b.com`
   fixtures) — 6 call sites total across these three methods.
5. In `test_doc_upsert_and_get_roundtrip`, add one assertion after the existing
   `assert isinstance(result.lang, str)` line: `assert result.fetched_at ==
   _FETCHED_AT`.
6. Add a new test method to `TestSQLiteDocumentStore`, e.g.
   `test_doc_upsert_conflict_updates_fetched_at_to_supplied_value`: create a store,
   call `doc_upsert("http://example.com", "Title", "en", None, None,
   fetched_at=_FETCHED_AT)`, then call `doc_upsert()` again for the same URL with
   `fetched_at=_FETCHED_AT_UPDATED`, then `doc_get("http://example.com")` and assert
   `result.fetched_at == _FETCHED_AT_UPDATED` — proving the `ON CONFLICT ... DO UPDATE
   SET fetched_at = ?` clause writes the caller's second value, not a
   `strftime('now')` substitution.

### Method
- Pure test-fixture edit: no new test infrastructure, no new fixtures beyond the two
  module-level string constants; reuse the existing `_make_doc_db()` /
  `SQLiteDocumentStore` construction pattern already used by every method in
  `TestSQLiteDocumentStore`.

### Details
- Run `rg -n "doc_upsert\(" tests/db/test_db_store_impl.py` at implementation time to
  re-confirm the 13-call-site count before starting, since this document's Assumptions
  section already found the plan's own "12" figure to be off by one.
- Keep the two new constants distinct in value (not e.g. both using the same date) so
  the new conflict-update test's assertion cannot pass by coincidence if the update
  clause were accidentally left as `COALESCE(?, fetched_at)` or similar.
- Do not add `NOT NULL` to `_DOCUMENT_SCHEMA`'s `fetched_at` column as part of this
  edit — no test in this file currently exercises a raw, `doc_upsert()`-bypassing
  INSERT against this schema, so the constraint would be untested dead weight; the
  production `NOT NULL` behavior is covered in `scripts/db/schema_sql.py`'s own
  implementation document and its own tests, not here.

## Compatibility considerations
- Test-only file; not imported by other modules. No production compatibility impact.
- Any future test added to this file that calls `doc_upsert()` positionally without
  supplying `fetched_at` will now fail with `TypeError: missing 1 required
  positional argument` (or the keyword equivalent) — this is the intended fail-fast
  signal the source plan requires, not a regression.

## Security considerations
N/A: test-only file: exercises an in-memory `sqlite3` connection with fixture-supplied
literal string constants; no external input, no new trust boundary.

## Rollback considerations
- Revert this file's diff together with `scripts/db/store_protocols.py` and
  `scripts/db/store_impl.py` (their own implementation documents) as one atomic unit
  — if `doc_upsert()`'s production signature reverts to 5 parameters while this file
  still passes a 6th, every call site raises `TypeError: takes 5 positional arguments
  but 6 were given` (or the keyword-argument equivalent); the reverse (this file
  reverted, production signature kept mandatory) fails every call site with a missing
  required argument.
- No schema/data migration is involved in this file's own change (in-memory SQLite,
  recreated per test); rollback is a pure code revert with no cleanup step.

## Validation plan
- `uv run pytest tests/db/test_db_store_impl.py -v` — all 13 `doc_upsert()` calls pass
  an explicit `fetched_at`; `test_doc_upsert_and_get_roundtrip`'s new assertion
  passes; the new conflict-update test passes.
- `rg -n "doc_upsert\(" tests/db/test_db_store_impl.py` — manually confirm every
  matched line supplies `fetched_at` (13/13).
- `rg -n "strftime\('%Y-%m-%dT%H:%M:%SZ', 'now'\)" tests/db/test_db_store_impl.py` —
  confirm zero matches after `_DOCUMENT_SCHEMA`'s `DEFAULT` clause is removed.
- `uv run pytest tests/db/test_db_store_impl.py::TestSQLiteSessionStore
  tests/db/test_db_store_impl.py::TestSQLiteVectorStore
  tests/db/test_db_store_impl.py::TestSQLiteMemoryDeleteStore -v` — confirm the
  unrelated store classes in the same file remain unaffected (no `fetched_at`
  coupling).

## Out of scope
- `scripts/db/store_protocols.py` / `scripts/db/store_impl.py`'s own `doc_upsert()`
  signature and SQL changes (own implementation documents).
- `scripts/db/schema_sql.py`'s production `DEFAULT`-clause removal (own
  implementation document; this file's `_DOCUMENT_SCHEMA` is a separate, private
  fixture, not the production schema).
- Any other test file in `tests/db/` or elsewhere that references `doc_upsert()`; per
  this plan's Assumptions, `tests/db/test_db_store_impl.py` is the only caller in the
  repository.

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
- Source plan: plans/20260820-095054_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-200056
- Related target files: tests/db/test_db_store_impl.py
