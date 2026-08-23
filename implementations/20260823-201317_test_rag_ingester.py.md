## Goal
Add mocked-boundary regression coverage in `tests/rag/ingestion/test_rag_ingester.py`
proving that the plan's new cross-chunk group validation in `ingest_url_group()` runs
*before* any document lookup or database transaction is started — for a mismatch in
any of the 11 shared fields, a duplicate `chunk_index`, and a non-contiguous-from-zero
`chunk_index` set — and that a `sqlite3.IntegrityError` raised out of
`_insert_chunks_batch()` during commit propagates out of `ingest_url_group()` (mirroring
this file's existing `sqlite3.DatabaseError` propagation test) and is caught, not
re-raised, by `_process_url_groups()`'s per-URL-group exception handling so one bad
group does not abort the whole batch run.

## Scope
- In scope: `tests/rag/ingestion/test_rag_ingester.py` only — new tests added to
  `TestAtomicity` (call-order/no-DB-touch assertions) and a new test targeting
  `_process_url_groups()` directly (not currently exercised end-to-end anywhere in this
  file; `TestCacheInvalidation` mocks `_process_url_groups()` away entirely).
- Out of scope: the production changes themselves — `ingester.py`'s group-validation
  pass, duplicate/contiguous `chunk_index` check, `_insert_chunks_batch()`'s removed
  `except sqlite3.IntegrityError: pass`, and `_process_url_groups()`'s exception-tuple
  widening (own implementation documents). `tests/rag/ingestion/test_ingester.py` (own
  implementation document, `20260823-201317_test_ingester.py.md`; that file owns the
  real-database row-count/file-routing assertions for the same 11-field/duplicate/
  non-contiguous cases, using its real in-memory SQLite connection — this file
  deliberately does not duplicate those real-DB assertions, since every test here
  mocks `db`/`doc_mgr`). `scripts/db/schema_sql.py`, `scripts/db/store_impl.py`, and
  `tests/db/*.py` (own implementation documents; unrelated file).

## Assumptions
- Per the source plan's Assumptions/Risks: this plan's `ingester.py` changes are
  sequenced after `plans/20260820-094150_plan.md`/`plans/20260820-095054_plan.md`.
  These new tests must not be added until that dependency lands; re-verify
  `_normalize_chunk_index`/`_validate_artifact` absence in `ingester.py` at
  implementation time per the source plan's own falsifiable check before writing these
  tests, since a still-present `_validate_artifact()` means `ingest_url_group()`'s
  current shape (which this document's tests are written against) has not yet changed
  to the post-dependency form the source plan assumes.
- Confirmed by direct read: this file's `mock_db` fixture is a
  `MagicMock(spec=SQLiteHelper)` with `db.begin_immediate` returning a context-manager
  mock (`cm`) whose `__exit__.return_value = False` — i.e. it does not swallow
  exceptions raised inside the `with` block, so it is already suitable for asserting
  that an exception raised by a patched `_insert_chunks_batch` propagates out through
  `db.begin_immediate()`'s `with` block, exactly as `test_database_failure_during_replacement`
  already does for `sqlite3.DatabaseError`. No fixture change is needed for the
  IntegrityError-propagation test in this file (contrast with `test_ingester.py`, whose
  real-`sqlite3.Connection`-backed `_FakeSQLiteHelper.begin_immediate()` fixture needed
  a rollback-on-exception correctness fix — that fix is this file's sibling document's
  concern, not this file's).
- Confirmed by direct read: `_get_or_create_document()` calls
  `doc_mgr.handle_existing_document(...)` as its DB-adjacent lookup step, and this
  file's `mock_doc_mgr` fixture already stubs that exact method
  (`mock_doc_mgr.handle_existing_document.return_value = (None, False, False)` by
  default). Asserting `mock_doc_mgr.handle_existing_document.assert_not_called()` after
  a group-validation failure is therefore a direct, already-available way to prove
  validation ran and rejected the group *before* `_get_or_create_document()`'s own
  first DB-adjacent call — consistent with Design step 1's placement requirement
  ("before `_get_or_create_document()`/`_prepare_chunks()`").
- Confirmed by direct read: `_process_url_groups()` is not exercised by any existing
  test in this file with a real `url_groups` dict and a real (non-mocked)
  `ingest_url_group()` call chain — `TestCacheInvalidation`'s three tests patch
  `_process_url_groups` itself, so they cannot verify its internal
  `except (OSError, RuntimeError, ValueError, sqlite3.OperationalError):` catch clause
  or the plan's addition of `sqlite3.IntegrityError` to that tuple. A new test calling
  `ingester._process_url_groups(...)` directly, with `ingest_url_group` patched to
  raise, is needed to cover this — and this file's existing `mock_db`/`mock_doc_mgr`
  fixtures are sufficient for it (no real filesystem/DB state is needed at this level).

## Design decisions
- Add the 11-field/duplicate/non-contiguous group-validation tests to `TestAtomicity`
  (not a new class) — that class already exists specifically to assert
  "no DB modification when [a chunk] fails during preparation"
  (`test_partial_preparation_failure`) and "rollback happened ... no transaction
  started yet" (`test_forced_reingest_with_embedding_failure`); the new tests are the
  same shape one validation stage earlier (group validation instead of per-chunk
  embedding), so they belong with their sibling "verify nothing touched the DB" tests.
- Write real two-file chunk-JSON groups to `tmp_path / "chunk"` via `_make_chunk_json()`
  + `orjson.dumps(...)` (the same pattern `test_ingest_url_group_success` and
  `TestAtomicity`'s own tests already use for single files) and call
  `ingest_url_group()` **without** patching `_prepare_chunks` for these specific new
  tests — patching `_prepare_chunks` (as `TestRagIngester`/most of `TestAtomicity` does)
  would bypass the new group-validation pass entirely, since that pass reads
  `chunk_files` directly via `_read_chunk_json()` before `_prepare_chunks()` is ever
  called; the assertion target here is exactly "did validation run early enough to
  prevent `_prepare_chunks`/`_get_or_create_document` from being reached at all."
- Add the `_process_url_groups()`-level IntegrityError-tolerance test as a new,
  separate test (not inside `TestAtomicity`, which is about a single `ingest_url_group()`
  call) — name it under a class that reflects batch-level behavior, e.g. a new
  `TestProcessUrlGroups` class placed after `TestAtomicity`, since no existing class in
  this file exercises `_process_url_groups()` directly today.

## Alternatives considered
- Duplicating `test_ingester.py`'s real-in-memory-SQLite row-count assertions in this
  file as well — rejected: this file's `mock_db` is a `MagicMock`, not a real
  connection, so "assert zero rows inserted" has no real backing store to query here;
  the meaningful assertion this file's fixtures support is "the DB-touching mocks were
  never called," which is what the new tests assert instead. Duplicating the same
  logical case in two files with two different assertion styles is intentional
  (per-file fixture fit), not redundant.
- Testing group validation by patching `RagIngester._validate_artifact` or a
  yet-to-be-named group-validation helper directly — rejected: the helper's name/shape
  is a Design decision left open in the source plan (Design step 1 describes behavior,
  not a method name); asserting through the public `ingest_url_group()` entry point and
  `handle_existing_document`/`begin_immediate` call counts is stable regardless of how
  the validation is internally factored.
- Extending `test_database_failure_during_replacement` in place to parametrize over
  `sqlite3.DatabaseError` and `sqlite3.IntegrityError` — rejected: that test's docstring
  and setup ("Verify rollback when database operation fails during commit") is
  intentionally generic-`DatabaseError`-scoped already-passing coverage; adding a
  clearly-named sibling test for `IntegrityError` keeps this plan's new requirement
  (integrity errors specifically must propagate, not just any `DatabaseError`)
  independently traceable and independently revertable from the pre-existing test.

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingester.py`

### Procedure
1. **Add an 11-field mismatch test** in `TestAtomicity`, parametrized over the same 11
   fields as `test_ingester.py`'s document (`url`, `title`, `lang`, `fetched_at`,
   `etag`, `last_modified`, `source_file`, `chunking_strategy`, `schema_version`,
   `artifact_type`, `created_by`): write two chunk files under `tmp_path / "chunk"`
   using `_make_chunk_json()` with one field overridden on the second file (and
   `chunk_index=1` on the second so the only intended difference is the parametrized
   field), call `ingester.ingest_url_group(mock_doc_mgr, mock_db, url, [path0, path1],
   force=False)` with `mock_doc_mgr`/`mock_db` from the existing fixtures and
   **without** patching `_prepare_chunks`, and assert:
   `result.n_success == 0`; `mock_doc_mgr.handle_existing_document.assert_not_called()`;
   `mock_db.begin_immediate.assert_not_called()`.
2. **Add a duplicate-`chunk_index` test**: two chunk files both with `chunk_index=0`,
   same call and same three assertions as step 1.
3. **Add a non-contiguous-`chunk_index` test**: two chunk files with `chunk_index=0`
   and `chunk_index=2`, same call and same three assertions as step 1.
4. **Add `test_integrity_error_during_replacement`** in `TestAtomicity`, directly
   mirroring `test_database_failure_during_replacement`'s structure: same
   `mock_doc_mgr.handle_existing_document.return_value = (123, False, True)` setup,
   same `patch.object(ingester, "_prepare_chunks", return_value=(...))`, but
   `patch.object(ingester, "_insert_chunks_batch", side_effect=sqlite3.IntegrityError("integrity check failed"))`
   instead of `sqlite3.DatabaseError`; assert
   `pytest.raises(sqlite3.IntegrityError, match="integrity check failed")` around the
   `ingest_url_group(...)` call, and assert `mock_db.begin_immediate.called` afterward
   (same shape as the existing `DatabaseError` test, proving the transaction was
   entered before the integrity failure occurred).
5. **Add a new `TestProcessUrlGroups` class** with one test,
   e.g. `test_integrity_error_from_one_group_does_not_abort_batch`: build a
   `url_groups` dict with two URLs each mapped to one real chunk-file path (written via
   `_make_chunk_json()` + `orjson.dumps(...)`, so `_process_url_groups()`'s per-file
   read at the top of its loop — if any — has real files to read), patch
   `ingester.ingest_url_group` with `side_effect=[sqlite3.IntegrityError("bad group"),
   IngestUrlResult("http://ok.example", 1, 0, False)]` (first URL raises, second
   succeeds), call `ingester._process_url_groups(mock_doc_mgr, mock_db, url_groups,
   force=False)` directly, and assert: the call does not raise;
   the returned list has length 2; the first result's
   `failure_reason == IngestionFailureReason.UNEXPECTED_FAILURE` and `n_success == 0`
   (mirroring the existing `OSError`/`RuntimeError`/`ValueError`/`OperationalError`
   catch-and-continue shape already implemented); the second result is the literal
   `IngestUrlResult` supplied for the second URL, proving the batch continued past the
   failed group.

### Method
- Reuse this file's existing `_make_chunk_json()` helper and `mock_db`/`mock_doc_mgr`
  fixtures for every new test; no new fixture-construction helper is required.
- For steps 1-3, deliberately do **not** patch `_prepare_chunks` (unlike most existing
  tests in this file) so the real group-validation code path executes against the real
  on-disk JSON files.
- For step 4, follow `test_database_failure_during_replacement`'s exact mocking
  shape (only the `side_effect` exception type and match string differ).
- For step 5, import `IngestionFailureReason` (already imported indirectly via
  `rag.ingestion.ingester` in other test files in this package; add it to this file's
  `from rag.ingestion.ingester import (...)` import list if not already present) to
  assert on the fallback failure reason `_process_url_groups()` assigns today.

### Details
- Place the new `TestAtomicity` tests after `test_database_failure_during_replacement`
  and before `test_partial_preparation_failure`, grouping all "fails before/at commit"
  tests together in reading order.
- For the 11-field parametrize list, keep the mismatched value the same
  plausible-but-different-value choice as `test_ingester.py`'s document (e.g.
  `lang="en"` vs default `"en"`... concretely: since `_make_chunk_json()`'s own default
  `lang` is `"en"`, use `"ja"` as the mismatched value for that field) to keep both
  files' parametrize tables consistent if compared side by side.
- `TestProcessUrlGroups`'s test must not patch `_process_url_groups` itself (that would
  defeat the purpose) — only `ingester.ingest_url_group` is patched, so the real
  `_process_url_groups()` loop and its `except (...)` clause execute.
- Confirm at implementation time (after the target `ingester.py` change lands) that
  `sqlite3.IntegrityError` has actually been added to `_process_url_groups()`'s caught
  tuple; if it has not yet landed, step 5's test should fail with the real
  `sqlite3.IntegrityError` propagating out of `_process_url_groups()` uncaught — that
  failure is the expected pre-implementation signal, not a test bug.

## Compatibility considerations
- Test-only file; not imported by production code. No production compatibility impact.
- All new tests are additive; no existing test method in this file is modified.
- The new `TestProcessUrlGroups` class is new but uses only fixtures
  (`mock_db`, `mock_doc_mgr`) already defined at module scope in this file — no fixture
  scope or `conftest.py` change is needed.

## Security considerations
N/A: test-only file exercising mocked DB/HTTP objects and `tmp_path`-scoped temporary
files with locally-defined fixture values; no external or untrusted input is involved.

## Rollback considerations
- These test additions have no production-behavior dependency beyond the target
  `ingester.py` changes (own implementation document) — if that change is reverted,
  these new tests should fail loudly (group validation no longer short-circuits before
  `handle_existing_document`/`begin_immediate`; `_insert_chunks_batch`'s
  `IntegrityError` no longer propagates; `_process_url_groups()` no longer tolerates
  `IntegrityError`), which is the intended regression signal, not a reason to revert
  this test file.
- No schema/data migration or fixture-infrastructure change is introduced by this
  document (unlike its `test_ingester.py` sibling document, which fixes
  `_FakeSQLiteHelper.begin_immediate()`); rollback here is a pure, independent code
  revert of the new test methods/class with no cleanup step.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -v` — every existing test
  still passes; all new tests (11-field parametrize, duplicate-index,
  non-contiguous-index, `test_integrity_error_during_replacement`,
  `TestProcessUrlGroups`) pass.
- `uv run pytest tests/rag/ingestion/test_ingester.py tests/rag/ingestion/test_rag_ingester.py -v`
  — the combined command the source plan's Validation plan row specifies for
  `ingest_url_group()`; confirms this file's new tests are compatible with
  `test_ingester.py`'s own (separately documented) new tests.
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -k integrity -v` — confirms
  `test_integrity_error_during_replacement` and `TestProcessUrlGroups`'s test are
  discoverable by the source plan's `-k integrity` filter convention (name both new
  tests to include `integrity`).

## Out of scope
- `scripts/rag/ingestion/ingester.py`'s group-validation pass, duplicate/contiguous
  `chunk_index` check, `_insert_chunks_batch()` exception removal, and
  `_process_url_groups()` exception-tuple change (own implementation documents).
- `scripts/db/schema_sql.py`, `scripts/db/store_impl.py`, and the `tests/db/*.py`
  changes (own implementation documents; unrelated file).
- `tests/rag/ingestion/test_ingester.py`'s real-in-memory-SQLite row-count/file-routing
  tests for the same 11-field/duplicate/non-contiguous/IntegrityError cases (own
  implementation document, `20260823-201317_test_ingester.py.md`).
- `test_rag_ingester_callback.py` and other sibling files in `tests/rag/ingestion/`
  (confirmed by UNK-03's resolved enumeration to not construct multi-chunk-file URL
  groups; no change needed there per the source plan).

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
- Related target files: tests/rag/ingestion/test_rag_ingester.py
