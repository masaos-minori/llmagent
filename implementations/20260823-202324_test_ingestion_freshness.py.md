# Implementation Procedure: tests/rag/ingestion/test_ingestion_freshness.py

## Goal

Add a new regression test to `TestGetOrCreateDocumentFreshness` that exercises the
"changed SHA-256 -> replace" outcome through the real (non-mocked)
`DocumentManager.handle_existing_document()`, closing a genuine, pre-existing coverage
gap before `_handle_existing_file()` is deleted from `document_manager.py`.

## Scope

**In-Scope**
- Add one new test mirroring `test_unchanged_file_skips_reingest`'s use of a real
  `DocumentManager(db)`, but with a stored etag/sha that differs from the new one, and
  assert the replace tuple (`skip=False`, `replace=True`).

**Out-of-Scope**
- `TestIsFileUnchanged` and `TestCrawlFilePayload` — unrelated to this gap.
- `test_changed_sha256_triggers_reingest` — already exists and covers the same scenario
  via a `MagicMock`; left as-is (it verifies `_get_or_create_document()`'s call-through
  behavior at the mock-boundary level, a different and still-useful concern from the new
  real-object test).
- This file's separate, already-processed update from `plans/done/20260820-095054_plan.md`
  (adding a `fetched_at` keyword argument to the four `_get_or_create_document()` calls
  in this same class — see `implementations/20260823-200056_test_ingestion_freshness.py.md`).
  That change and this one are independent additions to the same file and can land in
  either order; if that procedure runs first, this new test must also include the
  `fetched_at` keyword argument to match the other four calls' updated signature.

## Assumptions

- `test_unchanged_file_skips_reingest` is the correct template to mirror — confirmed by
  reading it in full: it is the one existing test in this class that already constructs
  a real `DocumentManager(db)` (not a `MagicMock`), via the same `_make_fake_db(url, sha,
  last_modified)` helper this new test will reuse.
- No existing test in this file currently exercises the replace outcome through a real
  `DocumentManager` — confirmed by reading all four `TestGetOrCreateDocumentFreshness`
  tests: `test_changed_sha256_triggers_reingest` and
  `test_non_file_url_uses_etag_update_path` both use `MagicMock()` for `doc_mgr`, and
  `test_force_true_skips_freshness_check` also uses a mock.

## Design decisions

- Reuse `_make_fake_db(url, sha, last_modified)` to seed a stored row with one SHA-256,
  then call `_get_or_create_document()` with a *different* `etag` (the new SHA-256) via
  a real `DocumentManager(db)` instance (matching `test_unchanged_file_skips_reingest`'s
  pattern exactly except for the differing etag).
- Assert the returned tuple has `skip=False` and `replace=True` (i.e., the second and
  third elements are `False`/`True`), matching `handle_existing_document()`'s documented
  contract for "force=False and file changed."

## Alternatives considered

- Extend `test_changed_sha256_triggers_reingest` in place to use a real `DocumentManager`
  instead of adding a new test — rejected: that test's own purpose (verifying
  `_get_or_create_document()` correctly calls through to whatever `doc_mgr` it is given)
  is still valuable as a mock-based unit test; replacing it would lose that narrower
  guarantee in favor of the new broader one. Keeping both is more coverage, not
  duplication, since they test different boundaries.

## Implementation

### Target file
`tests/rag/ingestion/test_ingestion_freshness.py`

### Procedure
1. Add a new test method to `TestGetOrCreateDocumentFreshness`, e.g.
   `test_changed_sha256_triggers_reingest_via_real_document_manager`.
2. Seed `_make_fake_db(url, "old_sha", "2024-01-01")` (same helper, same shape as
   `test_unchanged_file_skips_reingest`).
3. Construct a real `DocumentManager(db)` (not a mock).
4. Call `ingester._get_or_create_document(doc_mgr, db, url, "test.txt", "en",
   force=False, etag="new_sha", last_modified="2024-01-02")`.
5. Assert the result's `skip` element is `False` and `replace` element is `True`.
6. Run this test against the current (pre-deletion) `document_manager.py` to confirm it
   passes before `_handle_existing_file()` is removed (per the source plan's Phase 1
   ordering — this test must pass first, independently of the deletion).

### Method
Direct new test function, following the file's existing `pytest` style (plain functions
inside a test class, no fixtures beyond the existing `tmp_path` and helper functions
already used by sibling tests in the same class).

### Details
- This test intentionally exercises the real `_is_file_unchanged()` comparison path
  inside `handle_existing_document()`, not a mocked outcome — that is the entire point
  of the gap being closed.
- No changes needed to `_make_fake_db()` or `_make_ingester()` — both already support
  this scenario as-is (confirmed by their use in the existing `test_unchanged_file_skips_reingest`
  and `test_changed_sha256_triggers_reingest`).

## Compatibility considerations

N/A: pure test addition, no production code touched by this procedure.

## Security considerations

N/A: test-only file, no security-relevant logic changed.

## Rollback considerations

- Independently revertable: removing this one new test has no effect on any other test
  or on `document_manager.py`. However, this test must remain in place (and pass) before
  `_handle_existing_file()` is deleted — do not revert this addition without also
  reverting the companion `document_manager.py` deletion, or the coverage gap the source
  plan identified reopens silently.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/rag/ingestion/test_ingestion_freshness.py | Unit | `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -v` | New test passes against both pre- and post-deletion `document_manager.py` |

## Out of scope

- Any change to the three other existing `TestGetOrCreateDocumentFreshness` tests —
  none require modification for this specific gap.

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
- Source plan: plans/20260820-100528_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-202324
- Related target files: tests/rag/ingestion/test_ingestion_freshness.py
