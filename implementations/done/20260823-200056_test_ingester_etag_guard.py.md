## Goal
Update `tests/rag/ingestion/test_ingester_etag_guard.py` so it exercises
`ETagManager.update()`'s fail-closed behavior once `new_fetched_at` becomes a
mandatory `str` (Phase 3 of the plan): delete tests that lock in the
now-deleted `_update_null_fill()`/COALESCE-fill branch, replace the
both-null-early-return test with its inverse, replace the fail-open
malformed-timestamp test with fail-closed equivalents, and add the two
missing scenarios (equal-timestamp, timezone-naive incoming) so all six
behaviors required by the plan's Validation plan row for `etag_manager.py`
have one dedicated passing test each.

## Scope
- In scope: `tests/rag/ingestion/test_ingester_etag_guard.py` only.
- Out of scope: `scripts/rag/ingestion/etag_manager.py` production code
  (own implementation document, Phase 3 of the plan).

## Assumptions
- Confirmed by reading `scripts/rag/ingestion/etag_manager.py`: `update()`'s
  `new_fetched_at` parameter currently defaults to `None`; `_is_stale_update()`
  currently catches `ValueError` from `datetime.fromisoformat()` and returns
  `False` ("treat invalid timestamps as non-stale") for both the incoming and
  the stored value; `update()` currently opens with
  `if etag is None and last_modified is None: return`; `_update_with_freshness()`'s
  SQL currently reads `fetched_at = COALESCE(?, fetched_at)`; `_update_null_fill()`
  is a separate method dispatched when `new_fetched_at is None`. All five of
  these are the exact code sites the plan's Phase 3 removes/rewrites.
- UNK-01 (plan's stated resolution): equal (`new_dt == stored_dt`) is treated
  as "fresh" — `_is_stale_update()` keeps its `<` (strict) comparison, so an
  equal timestamp is not stale and the update proceeds (idempotent re-write).
- UNK-02 (plan's stated resolution): a malformed *incoming* timestamp
  re-raises the underlying parse error (`ValueError`, from
  `datetime.fromisoformat()`); a malformed *stored* timestamp raises a
  distinct error signaling a DB-consistency problem. Confirmed by reading
  `scripts/rag/exceptions.py`: no existing type there
  (`EmbeddingSchemaError`, `PipelineValidationError`, `SearchQueryError`,
  `ChunkFormatError`, `TokenizationError`, `UnknownMetadataError`) fits a
  DB-read consistency failure, so the plan's fallback is `RuntimeError`. The
  exact class is an `etag_manager.py`-side implementation decision made at
  Phase 3 time, not decided by this document.
- The `_update_with_freshness()` SQL rewrite (`COALESCE(?, fetched_at)` ->
  `fetched_at = ?`) does not change the parameter tuple's shape or order
  (still `(etag, last_modified, fetched_at, doc_id)`), so the three currently
  passing tests that assert on that tuple (`test_newer_incoming_updates_etag`,
  `test_stale_incoming_skips_update`, `test_datetime_comparison_with_z_suffix`)
  need no change.
- `_make_etag_mgr(stored_fetched_at, doc_id=42)`'s `stored_fetched_at: str | None`
  parameter still models two distinct cases that must not be conflated: `None`
  (no existing row / `db.fetchall` returns `[]`) versus a malformed non-empty
  string (e.g. `"not-a-date"`, an existing row with corrupt data). Only the
  malformed-string case is the UNK-02 "malformed stored value" scenario.

## Design decisions
- Assert observable behavior (whether `db.execute` is called, and what
  exception class propagates) rather than pinning new SQL substrings beyond
  the existing `"UPDATE documents" in sql` check, so the tests detect the
  behavior change without overcoupling to `etag_manager.py`'s exact SQL text.
- Keep one behavior per test function, matching this file's existing style
  (no `@pytest.mark.parametrize` conversion) — folding scenarios into one
  parametrized test would be an unrelated refactor beyond "add the cases the
  plan requires."
- Reuse the existing `_make_etag_mgr()` helper and `MagicMock`/`patch`
  pattern for every new/changed test; do not introduce new fixture
  infrastructure for a file this small.

## Alternatives considered
- Leaving the three COALESCE-fill tests in place but marked `xfail`/`skip`
  instead of deleting them — rejected: the branch they exercise
  (`_update_null_fill()`) is deleted outright per the plan's Phase 3 design,
  so keeping dead tests (even skipped) would misrepresent current behavior.
- Narrowing the two new raise-assertions to a guessed concrete exception
  class right now — rejected: the class is an `etag_manager.py`
  implementation-time decision (UNK-02); asserting a specific class here
  before that code exists risks a false negative if the implementer picks a
  different type. See Details for the mitigation.

## Implementation

### Target file
`tests/rag/ingestion/test_ingester_etag_guard.py`

### Procedure
1. Delete `test_missing_fetched_at_uses_coalesce_fill_only`,
   `test_missing_fetched_at_does_not_overwrite_existing_etag`, and
   `test_missing_fetched_at_fills_null_etag` — all three call
   `etag_mgr.update(..., None)` to exercise the now-deleted
   `_update_null_fill()` dispatch branch, which is unreachable once
   `new_fetched_at` is mandatory.
2. Replace `test_both_none_returns_early_no_db_query` with a new test, e.g.
   `test_both_null_metadata_still_updates_fetched_at`: build via
   `_make_etag_mgr("2026-06-01T10:00:00")`, call
   `etag_mgr.update(None, None, "2026-06-02T10:00:00")` (newer than stored),
   and assert `db.execute.assert_called_once()` with `fetched_at` present in
   the params tuple — this is the inverse of the deleted early-return
   assertion and locks in the plan's stated fix for the "silently dropped"
   bug (both HTTP metadata fields null must no longer skip the `fetched_at`
   update).
3. Replace `test_invalid_timestamp_treated_as_non_stale` with two new tests:
   - `test_malformed_incoming_timestamp_raises`: `_make_etag_mgr("2026-06-10T10:00:00")`,
     call `etag_mgr.update("etag-x", "Mon, 01 Jun 2026", "not-a-date")`,
     assert it raises and `db.execute.assert_not_called()`.
   - `test_malformed_stored_timestamp_raises_distinct_error`:
     `_make_etag_mgr("not-a-date")`, call
     `etag_mgr.update("etag-x", "Mon, 01 Jun 2026", "2026-06-10T10:00:00")`,
     assert it raises an error that is not a plain `ValueError` (per UNK-02,
     the stored-value error must be distinguishable from the incoming-value
     `ValueError`) and `db.execute.assert_not_called()`.
4. Add `test_tz_naive_incoming_timestamp_raises`:
   `_make_etag_mgr("2026-06-10T10:00:00+00:00")`, call
   `etag_mgr.update("etag-x", "Mon, 11 Jun 2026", "2026-06-11T10:00:00")`
   (no `Z`/offset suffix), assert it raises instead of the old silent
   `replace(tzinfo=UTC)` fallback, and `db.execute.assert_not_called()`.
5. Add `test_equal_timestamp_updates_fetched_at` (UNK-01):
   `_make_etag_mgr("2026-06-10T10:00:00Z")`, call
   `etag_mgr.update("etag-x", "Mon, 10 Jun 2026", "2026-06-10T10:00:00Z")`
   (`new_dt == stored_dt`), assert `db.execute.assert_called_once()` —
   equal is "fresh," not stale.
6. Leave `test_newer_incoming_updates_etag`, `test_stale_incoming_skips_update`,
   and `test_datetime_comparison_with_z_suffix` unchanged (see Assumptions).
7. Add `import pytest` to the file's imports (needed for `pytest.raises` in
   the three new raise-asserting tests; not currently imported).
8. After editing, run
   `rg -n "_update_null_fill|COALESCE\(\?, fetched_at\)" tests/rag/ingestion/test_ingester_etag_guard.py`
   and confirm zero matches.

### Method
Edit tests in place using the existing `_make_etag_mgr()` helper and
`unittest.mock.MagicMock`/`patch` pattern already used throughout this file;
use `pytest.raises(...)` for the three new raise-asserting tests.

### Details
- For the two malformed-timestamp tests and the tz-naive test, if this
  document's implementation lands before `etag_manager.py`'s own Phase 3
  change is written, assert against the broadest correct type known from the
  plan (`ValueError` for incoming/tz-naive per UNK-02's incoming-value
  re-raise; a non-`ValueError` exception, e.g. `RuntimeError`, for the
  malformed-stored case) and leave a short comment noting the exact class is
  contingent on `etag_manager.py`'s implementation, to be tightened once that
  file's own implementation document/commit lands.
- Do not change `_make_etag_mgr()`'s signature or the `stored_fetched_at: str | None`
  parameter — `None` (no row) and a malformed string ("not-a-date") remain
  two distinct fixture states used by different tests.

## Compatibility considerations
- These test changes must land together with (or strictly after)
  `scripts/rag/ingestion/etag_manager.py`'s Phase 3 change — the new
  fail-closed assertions will fail against the current, still-permissive
  implementation.
- No downstream consumer of this test file exists (tests are leaf nodes), so
  no compatibility impact beyond CI ordering within this plan.

## Security considerations
N/A: test-only file, no external input surface, no production code changed.

## Rollback considerations
- Revert this file's changes together with `etag_manager.py`'s Phase 3 commit
  as one unit; reverting only this file while `etag_manager.py`'s fail-closed
  rewrite stays would immediately fail CI, and reverting only `etag_manager.py`
  while this file stays would fail CI in the other direction.
- No data/schema rollback implication — test-only file.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py -v` — passes
  once `etag_manager.py`'s Phase 3 change lands; the six required behaviors
  (newer/updates, older/stale-skips, equal/updates, tz-naive/raises,
  malformed-incoming/raises, malformed-stored/raises-distinct-error) each
  have one dedicated passing test, per the plan's Validation plan row for
  `etag_manager.py`.
- `rg -n "_update_null_fill|COALESCE\(\?, fetched_at\)" tests/rag/ingestion/test_ingester_etag_guard.py`
  — zero matches, confirming no residual reference to the deleted branch.

## Out of scope
- `scripts/rag/ingestion/etag_manager.py` production code (own implementation
  document, Phase 3).
- Any other test file under `tests/rag/ingestion/`.

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
- Related target files: tests/rag/ingestion/test_ingester_etag_guard.py
