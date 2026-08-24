## Goal
In `tests/db/test_db_store_impl.py`: add `chunking_strategy` to the private
`_DOCUMENT_SCHEMA` fixture (currently missing this column entirely) and supply it as
a new explicit argument on every `SQLiteDocumentStore.doc_upsert()` call site, to
match the mandatory `chunking_strategy: str` parameter this plan's own
`scripts/db/store_impl.py` implementation document adds to `doc_upsert()`; add one
new test proving the `ON CONFLICT ... DO UPDATE` path overwrites `chunking_strategy`
with the caller-supplied value (`chunking_strategy = excluded.chunking_strategy`, per
this plan's Design step 6); and confirm the disposition of
`test_chunk_insert_defaults_to_empty_strings`, which this plan's own Risks/Affected
areas sections flag as documenting silent-default behavior a sibling dependency plan
eliminates from `chunk_insert()`.

## Scope
- In scope: `_DOCUMENT_SCHEMA`'s `documents` table definition; every
  `TestSQLiteDocumentStore` method that calls `doc_upsert()`; one new test for
  `chunking_strategy`'s `ON CONFLICT` overwrite behavior.
- Out of scope: `scripts/db/store_impl.py` / `scripts/db/store_protocols.py`'s own
  `doc_upsert()` signature change (own implementation documents; this file's edits
  depend on that signature landing first); `_SESSION_SCHEMA`,
  `TestSQLiteSessionStore`, `TestSQLiteVectorStore`, `TestSQLiteMemoryDeleteStore`
  (no `doc_upsert()`/`chunking_strategy` coupling); `chunk_insert()`'s own
  `chunk_type`/`source_file` mandatory-argument work (owned by
  `plans/done/20260820-094150_plan.md`, see Assumptions); `fetched_at`'s own
  mandatory-argument work and its `ON CONFLICT` recompute-vs-overwrite semantics
  (owned by `plans/done/20260820-095054_plan.md`, see Assumptions — this document
  does not add, remove, or re-assert any `fetched_at`-only test).

## Assumptions
- **Sequencing, confirmed by directory location**: both
  `plans/done/20260820-094150_plan.md` (removes `chunk_insert()`'s
  `chunk_type: str = ""` / `source_file: str = ""` defaults) and
  `plans/done/20260820-095054_plan.md` (adds a mandatory `fetched_at: str` parameter
  to `doc_upsert()`) are filed under `plans/done/`, i.e. planning-approved ahead of
  this plan, consistent with this plan's own Assumptions section naming both as
  required predecessors. As of this document's writing, neither plan's *code* changes
  have actually landed yet (confirmed by direct read: `store_impl.py`'s `doc_upsert()`
  still has its original 5-parameter signature with no `fetched_at`, and
  `chunk_insert()` still has its original `chunk_type: str = ""` / `source_file: str =
  ""` defaults) — "done" here means the plan document, not the implementation. This
  document's procedure below is written against the *target* end-state (both
  predecessor plans' code changes landed), per this plan's own stated sequencing
  requirement; falsifiable at implementation time by re-checking `doc_upsert()`'s and
  `chunk_insert()`'s actual signatures before starting.
- **`test_chunk_insert_defaults_to_empty_strings` disposition**: this plan's own
  Affected-areas row for this file says to "remove/replace" this test. Cross-checked
  against `plans/done/20260820-094150_plan.md`'s own implementation document
  (`implementations/20260821-123341_test_db_store_impl.py.md`), which already
  specifies renaming it to `test_chunk_insert_requires_chunk_type_and_source_file`
  (asserting `TypeError` on omission) as part of that earlier plan's own scope. This
  document therefore treats that rename/rewrite as **owned by the 094150 predecessor,
  not by this plan** — this plan's only interest in that test method (under whichever
  name it carries by execution time) is that it, too, contains a `doc_upsert()` call
  needing `chunking_strategy=...` added, exactly like the file's other 12 call sites.
  Falsifiable: if at implementation time neither `test_chunk_insert_defaults_to_empty_strings`
  nor `test_chunk_insert_requires_chunk_type_and_source_file` exists under any name,
  or if the predecessor's rename has not landed, add `chunking_strategy=...` to
  whichever form of the test is present rather than re-deciding its disposition here.
- **13 `doc_upsert()` call sites**, confirmed by direct `grep -n "doc_upsert(" 
  tests/db/test_db_store_impl.py`: one each in
  `test_doc_upsert_new_url_returns_positive_id`,
  `test_doc_upsert_and_get_roundtrip`, `test_doc_get_returns_lang_as_str`,
  `test_chunk_insert_increments_count`,
  `test_chunk_insert_stores_chunk_type_and_source_file`,
  `test_chunk_insert_defaults_to_empty_strings` (or its post-094150 renamed form),
  `test_doc_delete_removes_document_and_returns_true`; two each (one per URL fixture,
  `http://a.com`/`http://b.com`) in `test_doc_list_returns_inserted_documents`,
  `test_doc_list_filtered_by_lang`, `test_doc_list_returns_lang_as_str`. All 13 need
  a `chunking_strategy` value added, independent of whatever `fetched_at` argument
  the 095054 predecessor's own document already adds to the same call sites.
- **Discrepancy flagged, not resolved here**: this plan's Design step 6 states
  `doc_upsert()`'s `ON CONFLICT` branch "keeps its existing `fetched_at =
  strftime(...)` recompute-on-update behavior" (i.e. `fetched_at` is *not*
  overwritten by the caller's value on conflict), whereas
  `plans/done/20260820-095054_plan.md`'s own implementation document
  (`implementations/20260823-200056_test_db_store_impl.py.md`) adds a test asserting
  the opposite — that `ON CONFLICT` **does** write the caller-supplied `fetched_at`
  value, not a `strftime('now')` recompute. This document takes no position on that
  conflict: it is a `fetched_at`-only question, owned entirely by the 095054
  predecessor's document, and does not affect this document's `chunking_strategy`
  work, whose own conflict-resolution ("Gap found during implementation-procedure
  review" in this plan's Design section) is unambiguous:
  `chunking_strategy = excluded.chunking_strategy` (always overwrite, like `title`/
  `lang`/`etag`/`last_modified`). Implementer must re-read both documents' final
  `doc_upsert()` SQL before writing any *new* `fetched_at`-asserting test in this
  file; this document adds none.
- `DocumentRow` already exposes whatever fields `doc_get()`/`doc_list()` select
  (confirmed by reading `_row_to_document()` in `store_impl.py`) — if
  `chunking_strategy` is not added to the `SELECT`/`_row_to_document()` projection by
  the sibling `store_impl.py` implementation document, this file cannot assert on
  `result.chunking_strategy` from a round-trip and must instead assert via a direct
  `SELECT chunking_strategy FROM documents WHERE ...` against `store._db`, mirroring
  the pattern `test_chunk_insert_stores_chunk_type_and_source_file` already uses for
  `chunk_type`/`source_file`.

## Design decisions
- Add `chunking_strategy` to `_DOCUMENT_SCHEMA` as a plain `TEXT` column with neither
  `NOT NULL` nor `DEFAULT` — mirrors this file's existing (post-095054) treatment of
  `fetched_at` in the same fixture (`fetched_at TEXT`, no `DEFAULT`, no `NOT NULL`):
  this private in-memory fixture does not otherwise enforce `NOT NULL` on any column,
  relying on the Python-level mandatory parameter to guarantee presence in practice;
  keeping the new column consistent with that established pattern avoids introducing
  a one-off enforcement style for a single column in an already-permissive fixture.
- Introduce one module-level string constant for the chunking-strategy literal used
  across the 13 call sites (e.g. `_CHUNKING_STRATEGY = "text"`), plus a second,
  distinct value for the new conflict-overwrite test (e.g.
  `_CHUNKING_STRATEGY_UPDATED = "semantic"`) — same rationale as the sibling
  `_FETCHED_AT`/`_FETCHED_AT_UPDATED` constants already introduced by the 095054
  predecessor's document: one canonical literal per concept, one place to change it.
- Add exactly one new test for `chunking_strategy`'s `ON CONFLICT` overwrite
  behavior, next to (not merged into) whatever conflict-path test the 095054
  predecessor's document adds for `fetched_at` — the two columns have different,
  independently-specified conflict semantics (per the Assumptions discrepancy above),
  so asserting them in one shared test would couple two independently-resolvable
  behaviors into a single pass/fail signal.

## Alternatives considered
- Switching `_DOCUMENT_SCHEMA` to build from `db.schema_sql.build_rag_schema_sql()`
  instead of maintaining a private copy — rejected for this document: it is the
  larger of the two options this plan's own Affected-areas row explicitly offers
  ("Add `chunking_strategy` to this fixture schema (**or** switch it to build from
  `build_rag_schema_sql()`)"), would pull in the `vec0`/`chunks_fts` virtual-table
  dependencies this file's tests do not need, and would require every one of this
  file's existing `chunk_insert()`/`doc_upsert()` tests to be re-verified against the
  full real DDL rather than the narrower fixture change actually required here.
- Adding `NOT NULL` to `_DOCUMENT_SCHEMA`'s new `chunking_strategy` column for closer
  production parity — rejected: inconsistent with this same fixture's existing,
  already-established choice not to enforce `NOT NULL` on `fetched_at` either; mixing
  enforcement styles within one fixture would make the schema harder to reason about
  for no additional test coverage (no test in this file constructs a raw,
  `doc_upsert()`-bypassing `INSERT` against this schema).
- Merging the new `chunking_strategy` conflict-overwrite test into the same test
  method the 095054 predecessor's document adds for `fetched_at`'s conflict path —
  rejected: the two columns' conflict-resolution designs come from two different
  planning documents with a currently-unresolved discrepancy noted above; keeping the
  assertions in separate tests means either one can be corrected independently
  without touching the other's test body.

## Implementation

### Target file
`tests/db/test_db_store_impl.py`

### Procedure
1. Before starting, run `rg -n "doc_upsert\(" tests/db/test_db_store_impl.py` and
   `rg -n "class SQLiteDocumentStore" -A 30 scripts/db/store_impl.py` to reconfirm
   the current call-site count and the landed `doc_upsert()` signature (per
   Assumptions, both predecessor plans' code changes must already be present).
2. Add a `chunking_strategy` column to `_DOCUMENT_SCHEMA`'s `documents` table
   definition (no `NOT NULL`, no `DEFAULT`, consistent with the fixture's existing
   `fetched_at` column — see Design decisions).
3. Near the top of the file, alongside any `_FETCHED_AT`-style constants already
   present from the 095054 predecessor's document, add:
   `_CHUNKING_STRATEGY = "text"` and `_CHUNKING_STRATEGY_UPDATED = "semantic"`.
4. Add `chunking_strategy=_CHUNKING_STRATEGY` to the `doc_upsert()` call in each of
   the 13 call sites listed in Assumptions (7 methods with one call, 3 methods with
   two calls each for the `http://a.com`/`http://b.com` fixtures).
5. Add a new test method to `TestSQLiteDocumentStore`, e.g.
   `test_doc_upsert_conflict_updates_chunking_strategy_to_supplied_value`: call
   `doc_upsert(..., chunking_strategy=_CHUNKING_STRATEGY)` for a URL, then call
   `doc_upsert()` again for the same URL with
   `chunking_strategy=_CHUNKING_STRATEGY_UPDATED`, then read back the stored
   `chunking_strategy` (via `doc_get()` if the sibling `store_impl.py` document adds
   it to `DocumentRow`'s projection, otherwise via a direct `SELECT chunking_strategy
   FROM documents WHERE url = ?` against `store._db`, per the fallback noted in
   Assumptions) and assert it equals `_CHUNKING_STRATEGY_UPDATED` — proving the
   `ON CONFLICT ... DO UPDATE SET chunking_strategy = excluded.chunking_strategy`
   clause overwrites with the caller's second value.
6. Confirm `test_chunk_insert_defaults_to_empty_strings` (or its post-094150 renamed
   form, `test_chunk_insert_requires_chunk_type_and_source_file`) received
   `chunking_strategy=_CHUNKING_STRATEGY` on its own `doc_upsert()` call in step 4;
   do not otherwise alter this test's body, name, or assertions — its disposition is
   owned by the 094150 predecessor's document (see Assumptions).

### Method
- Pure test-fixture edit: one new schema column, two new module-level constants, 13
  call-site edits, and one new test method reusing the existing
  `_make_doc_db()`/`SQLiteDocumentStore` construction pattern already used throughout
  `TestSQLiteDocumentStore`. No new test infrastructure required.

### Details
- Keep `_CHUNKING_STRATEGY` and `_CHUNKING_STRATEGY_UPDATED` distinct values (not the
  same string) so the new conflict-overwrite test's assertion cannot pass by
  coincidence if the `ON CONFLICT` clause were accidentally left as
  `COALESCE(?, chunking_strategy)` or omitted entirely.
- Do not touch `_SESSION_SCHEMA`, `TestSQLiteSessionStore`,
  `TestSQLiteVectorStore`, or `TestSQLiteMemoryDeleteStore` — none call
  `doc_upsert()` or reference `chunking_strategy`.
- If, at implementation time, the 095054 predecessor's `fetched_at` work has not yet
  landed in this file (contradicting the Assumptions' sequencing expectation), stop
  and treat that as a blocking predecessor gap rather than adding `fetched_at`
  handling here — this document's scope is `chunking_strategy` only.

## Compatibility considerations
- Test-only file; not imported by other modules. No production compatibility impact.
- Any future test in this file calling `doc_upsert()` without `chunking_strategy`
  will fail with a missing-argument `TypeError` once the production signature is
  mandatory — the intended fail-fast signal, not a regression.

## Security considerations
N/A: test-only file exercising an in-memory `sqlite3` connection with fixture-supplied
literal string constants; no external input, no new trust boundary.

## Rollback considerations
- Revert this file's `chunking_strategy`-related diff together with
  `scripts/db/store_impl.py` / `scripts/db/store_protocols.py`'s own
  `chunking_strategy` parameter addition (their own implementation documents) as one
  atomic unit — if the production signature reverts to omitting
  `chunking_strategy` while this file still supplies it, every call site raises a
  `TypeError` for an unexpected keyword argument; the reverse (this file reverted,
  production kept mandatory) fails every call site with a missing required argument.
- This file's `chunking_strategy` edits are independent of, and separately
  revertible from, whatever `fetched_at` edits the 095054 predecessor's document
  applies to the same call sites — the two are additive, non-overlapping arguments
  on the same call sites, not a shared code path.
- No schema/data migration involved (in-memory SQLite, recreated per test); rollback
  is a pure code revert with no cleanup step.

## Validation plan
- `uv run pytest tests/db/test_db_store_impl.py -v` — all 13 `doc_upsert()` calls
  pass an explicit `chunking_strategy`; the new conflict-overwrite test passes.
- `rg -n "doc_upsert\(" tests/db/test_db_store_impl.py` — manually confirm every
  matched line supplies `chunking_strategy` (13/13).
- `rg -n "chunking_strategy" tests/db/test_db_store_impl.py` — spot-check the fixture
  column, the two constants, and all call sites appear.
- `uv run pytest tests/db/test_db_store_impl.py::TestSQLiteSessionStore
  tests/db/test_db_store_impl.py::TestSQLiteVectorStore
  tests/db/test_db_store_impl.py::TestSQLiteMemoryDeleteStore -v` — confirm the
  unrelated store classes in the same file remain unaffected.
- `uv run pytest -q tests/db` — full-directory regression check alongside the
  sibling `schema_sql.py`/`store_impl.py`/`test_db_maintenance.py`/
  `test_create_schema.py` changes landing in the same plan.

## Out of scope
- `scripts/db/store_protocols.py` / `scripts/db/store_impl.py`'s own `doc_upsert()`
  signature and SQL changes, including the `ON CONFLICT` clause for both
  `fetched_at` and `chunking_strategy` (own implementation documents).
- `scripts/db/schema_sql.py`'s production `DEFAULT`-clause removal (own
  implementation document; this file's `_DOCUMENT_SCHEMA` is a separate, private
  fixture).
- `chunk_insert()`'s `chunk_type`/`source_file` mandatory-argument change and
  `test_chunk_insert_defaults_to_empty_strings`'s rename/rewrite (owned by
  `plans/done/20260820-094150_plan.md`'s own implementation document).
- `fetched_at`'s mandatory-argument change, its `ON CONFLICT` semantics, and any
  `fetched_at`-asserting test (owned by `plans/done/20260820-095054_plan.md`'s own
  implementation document, `implementations/20260823-200056_test_db_store_impl.py.md`).
- Any other test file referencing `doc_upsert()`; per this plan's own Assumptions,
  `tests/db/test_db_store_impl.py` is the only caller in the repository.

## Execution Status

##### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify the target implementation procedure file(s) | Complete | — | — | Found 5 files matching pattern |
| 2 | Read the current implementation procedure file | Complete | — | — | Read full file |
| 3 | Implement the feature and pass code validation | Complete | — | — | Added constants + ON CONFLICT test; replaced inline "text" with _CHUNKING_STRATEGY |
| 4 | Test the feature and pass required tests/coverage | Complete | — | — | All 36 tests pass (14 DocumentStore + 22 other stores) |
| 5 | Update documentation per routing.md mapping | N/A | — | — | No changed file has routing.md mapping |
| 6 | Validate documentation updates | N/A | — | — | Not applicable |
| 7 | Move the implementation procedure file to `implementations/done/` | Pending | — | — | |

##### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Completion

### Validation results

- **Adversarial validation**: PASSED — confirmed `_DOCUMENT_SCHEMA` already had `chunking_strategy TEXT NOT NULL` from File2's implementation; confirmed all 13 call sites already supplied `chunking_strategy` as positional argument; confirmed `ON CONFLICT ... DO UPDATE SET chunking_strategy = excluded.chunking_strategy` clause exists in production `store_impl.py` (verified by direct read at line ~180-200); confirmed no `except sqlite3.IntegrityError` suppression in `doc_upsert()`'s conflict branch
- **Test suite**: 36/36 tests pass (14 DocumentStore + 22 other stores)
- **ruff format**: applied
- **ruff check --fix**: applied (import sorting)
- **mypy**: no issues found

### Key changes

1. **Module-level constants** (new): Added `_CHUNKING_STRATEGY = "text"` and `_CHUNKING_STRATEGY_UPDATED = "semantic"` near top of file, alongside existing `_FETCHED_AT`-style constants from the 095054 predecessor's document. This provides one canonical literal per concept, one place to change it.

2. **Replaced inline `"text"` literals with `_CHUNKING_STRATEGY` constant** (refactoring): Replaced all 12 remaining inline `"text"` values in `doc_upsert()` call sites with `_CHUNKING_STRATEGY` for consistency with the new constant approach. The 095054 predecessor's document already introduced `_FETCHED_AT`-style constants; this brings the same pattern to `chunking_strategy`.

3. **New test: `test_doc_upsert_conflict_updates_chunking_strategy_to_supplied_value`** (new): Calls `doc_upsert()` twice for the same URL — first with `chunking_strategy=_CHUNKING_STRATEGY`, then with `chunking_strategy=_CHUNKING_STRATEGY_UPDATED` — and asserts via direct `SELECT chunking_strategy FROM documents WHERE url = ?` against `store._db` that the second value overwrites the first. Proves the `ON CONFLICT ... DO UPDATE SET chunking_strategy = excluded.chunking_strategy` clause works correctly.

### Adversarial findings vs. procedure claims

- **Procedure claim** ("13 doc_upsert() call sites"): CORRECT — confirmed by grep at implementation time; all 13 call sites were verified to supply `chunking_strategy` as a positional argument.
- **Procedure claim** ("_DOCUMENT_SCHEMA currently missing chunking_strategy column"): INCORRECT — the column was already present from File2's implementation (`chunking_strategy TEXT NOT NULL` on line 30). The procedure should have been verified against the actual schema before asserting this behavior.
- **Procedure claim** ("test_chunk_insert_defaults_to_empty_strings disposition: remove/replace"): PARTIALLY CORRECT — the test still exists under its post-094150 renamed name `test_chunk_insert_requires_chunk_type_and_source_file`; adding `chunking_strategy=_CHUNKING_STRATEGY` to its `doc_upsert()` call was done as part of the blanket replacement.
- **Procedure claim** ("DocumentRow already exposes whatever fields doc_get()/doc_list() select"): UNVERIFIED — could not confirm this without reading `store_impl.py`'s `_row_to_document()` function; the new test uses a direct `SELECT` fallback rather than relying on `DocumentRow`'s projection.
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-095542_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-201317
- Related target files: tests/db/test_db_store_impl.py
