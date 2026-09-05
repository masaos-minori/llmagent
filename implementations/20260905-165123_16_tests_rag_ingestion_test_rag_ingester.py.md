## Goal
Remove `class TestCacheInvalidation` (all three of its test methods) from
`tests/rag/ingestion/test_rag_ingester.py`, since every method in it depends on
`_cache_invalidator`/`_rag_pipeline_service_url`, both removed from
`scripts/rag/ingestion/ingester.py` by procedure document `05` (`REQ-004`, `REQ-006`).

## Scope
- **In-Scope**: remove `class TestCacheInvalidation:` in its entirety — lines 364-462,
  the file's exact final section (confirmed: file is exactly 462 lines). This spans
  three test methods: `test_all_skipped_run_no_cache_invalidation`,
  `test_all_failed_run_no_cache_invalidation`, and a third (partial-success) test whose
  docstring reads "Verify cache invalidated only once on partial success" — all three
  set `ingester._cache_invalidator._client = ...` and
  `ingester._rag_pipeline_service_url = "http://cache-svc"`, and assert on
  `ingester._client.post` being called (or not) with `"http://cache-svc/rag_invalidate_cache"`.
- **Out-of-Scope**: every test class preceding line 364 in this file — confirmed
  unrelated to cache invalidation by reading the class boundary at line 362/363; no
  other class in the file references `_cache_invalidator`.

## Assumptions
- `scripts/rag/ingestion/ingester.py`'s `_cache_invalidator` attribute and
  `_rag_pipeline_service_url` attribute (procedure document `05`; the latter is
  explicitly retained per that document's Design decisions, but its role in *this*
  test's cache-verification setup becomes moot once `_cache_invalidator` itself is
  gone) are removed/no-longer-referenced by `ingest_all()` in the same implementation
  pass — this test class's fixtures construct an `ingester` instance and directly
  poke `_cache_invalidator`, which will raise `AttributeError` once that attribute no
  longer exists.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- **Correction to the Plan's stated evidence**: the Plan's `Implementation Target
  Files` row for this file states only "References the removed ingestion-side
  invalidation call" with evidence "`rg -n \"invalidate_cache\\|rag_invalidate_cache\"`
  matched this file" — that search pattern does not match `_cache_invalidator` (the
  substring `invalidate_cache` is not present in `_cache_invalidator`), so the Plan's
  evidence undercounted this row's actual scope. Step 3a Adversarial Verification
  (`rg -n "_cache_invalidator|cache_invalidator|_rag_pipeline_service_url|rag_invalidate_cache"`)
  found the full `class TestCacheInvalidation` (three methods, lines 364-462) depends
  on the removed attribute — this is recorded here as the corrected, actual scope for
  this row; it does not require amending the Plan document itself, since the target
  file (this same file) is unchanged and no additional file was discovered (see
  `skills/plan-to-implementation-procedure/workflow.md` Step 3a: a stale/undercounted
  claim about the *same* row is corrected in the generated document, not necessarily
  requiring a Plan edit when the row's file path and Requirement linkage remain
  correct).
- Remove the whole class as one contiguous block, since all three methods exist solely
  to verify `_cache_invalidator` delegation behavior that procedure `05` removes.

## Alternatives considered
- Rewriting the three tests to assert `ingester` no longer has a `_cache_invalidator`
  attribute (a negative-existence test) — rejected: the originating issue's Testing
  Expectations for `REQ-004`/`tests/rag/ingestion/test_rag_ingester.py` state "update to
  assert `RagIngester` no longer constructs or calls `CacheInvalidator`" as a general
  expectation, not a request for a new negative-assertion test; deleting the
  now-meaningless class satisfies this more directly than adding a new assertion
  against an intentionally-removed attribute.

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingester.py`

### Procedure
1. Delete lines 364-462 (`class TestCacheInvalidation:` in full, including its three
   test methods) — this is the file's exact tail, so deletion can be performed as a
   truncation to line 362 (confirm line 362/363 is the blank-line class separator
   following the prior class's last test, matching this file's existing convention,
   before truncating).

### Method
Direct removal via `Edit`.

### Details
- Since `TestCacheInvalidation` is confirmed to be this file's final class (file is
  exactly 462 lines), this is a clean tail-truncation — verify no trailing content
  exists after line 462 before treating this as safe.
- Confirm after editing: `rg -n
  "_cache_invalidator|cache_invalidator|_rag_pipeline_service_url|rag_invalidate_cache|CacheInvalidator"
  tests/rag/ingestion/test_rag_ingester.py` returns zero matches — this broader pattern
  (not just `invalidate_cache`) is the one that must be re-run to confirm completeness,
  per this document's Design decisions correction.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; functionally coupled to procedure
  document `05` (reverting only this test file while `05` remains applied would leave
  tests poking an `_cache_invalidator` attribute that no longer exists, causing
  `AttributeError` at test setup rather than a clean pass/fail).

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -v` — all remaining tests
  pass; no `TestCacheInvalidation` collection error.
- `rg -n
  "_cache_invalidator|cache_invalidator|_rag_pipeline_service_url|rag_invalidate_cache|CacheInvalidator"
  tests/rag/ingestion/test_rag_ingester.py` — zero matches.

## Completion criteria
- `class TestCacheInvalidation` no longer exists in this file (Plan `AC-5`, `AC-9`).
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -v` passes in full.

## Out of scope
- `scripts/rag/ingestion/ingester.py`'s own edit (procedure document `05`).
- Every other test class in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: this document itself is a test-removal change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-004` (references the removed ingestion-side invalidation call); `REQ-006` (remove tests referencing the removed API)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: tests/rag/ingestion/test_rag_ingester.py
