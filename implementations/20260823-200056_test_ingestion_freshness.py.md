# Implementation Procedure: tests/rag/ingestion/test_ingestion_freshness.py

## Goal

Update `TestGetOrCreateDocumentFreshness`'s four `_get_or_create_document()` call sites
to supply the newly-mandatory `fetched_at` keyword argument, so this file keeps passing
once `scripts/rag/ingestion/ingester.py::_get_or_create_document()` widens `fetched_at`
from an implicit/absent parameter to a required `str`.

## Scope

**In-Scope**
- `TestGetOrCreateDocumentFreshness.test_unchanged_file_skips_reingest`
- `TestGetOrCreateDocumentFreshness.test_changed_sha256_triggers_reingest`
- `TestGetOrCreateDocumentFreshness.test_force_true_skips_freshness_check`
- `TestGetOrCreateDocumentFreshness.test_non_file_url_uses_etag_update_path`

**Out-of-Scope**
- `TestIsFileUnchanged` and `TestCrawlFilePayload` — neither calls
  `_get_or_create_document()` or otherwise references `fetched_at`; unaffected by this
  plan.
- `DocumentManager.handle_existing_document()` / `_update_etag()` internals — this file
  only calls the real `DocumentManager` in one test (`test_unchanged_file_skips_reingest`)
  and mocks it everywhere else; the fail-closed rewrite of `etag_manager.py` itself is
  covered by `tests/rag/ingestion/test_ingester_etag_guard.py`, not this file.

## Assumptions

- This file was omitted from the source plan's original Affected areas / Related target
  files list, which instead named `tests/mcp_servers/rag_pipeline/test_document_manager.py`
  — verified during implementation-procedure review that the latter file's `DocumentManager`
  is an unrelated class (`scripts/mcp_servers/rag_pipeline/document_manager.py`, no
  `handle_existing_document()`/`_update_etag()`), while this file (`test_ingestion_freshness.py`)
  is the one that actually exercises `scripts/rag/ingestion/ingester.py::_get_or_create_document()`,
  which calls `DocumentManager.handle_existing_document()`. The source plan
  (`plans/20260820-095054_plan.md`) has been corrected in place to reflect this.
- `_get_or_create_document()`'s new `fetched_at` parameter will be keyword-only at these
  call sites regardless of its exact position in the function signature (per the
  companion `ingester.py` implementation procedure, it moves to immediately after
  `force`) — all four calls in this file already pass `force`, `etag`, and
  `last_modified` as keywords, so adding `fetched_at=...` as a keyword follows the
  existing call style without needing positional-argument reordering here.

## Design decisions

- Add `fetched_at="2024-01-01T00:00:00Z"` (a fixed, canonical-UTC-format literal
  consistent with the `last_modified`/`etag` values already used in these fixtures) as a
  keyword argument to each of the four `_get_or_create_document()` calls, rather than
  introducing a shared fixture/constant — the four call sites already duplicate similar
  literal values (`"2024-01-01"`, `"2024-01-02"`) inline, so a new shared constant would
  be inconsistent with this file's existing style without a broader refactor this plan
  does not request.

## Alternatives considered

- Introduce a module-level `_FETCHED_AT = "2024-01-01T00:00:00Z"` constant and reference
  it at all four sites — rejected for this pass because it would touch more lines than
  necessary for a mechanical mandatory-parameter fix and the existing file does not use
  shared constants for the sibling `etag`/`last_modified` literals either.

## Implementation

### Target file
`tests/rag/ingestion/test_ingestion_freshness.py`

### Procedure
1. In `test_unchanged_file_skips_reingest`, add `fetched_at="2024-01-01T00:00:00Z"` to
   the `ingester._get_or_create_document(...)` call.
2. In `test_changed_sha256_triggers_reingest`, add the same keyword argument to its
   `ingester._get_or_create_document(...)` call.
3. In `test_force_true_skips_freshness_check`, add the same keyword argument to its call.
4. In `test_non_file_url_uses_etag_update_path`, add the same keyword argument to its
   call.
5. Run the file's test suite to confirm all four tests still pass with their existing
   assertions unchanged (this is a signature-compatibility fix, not a behavior change to
   the tests themselves).

### Method
Direct, mechanical edit: add one keyword argument per call site. No fixture
infrastructure change needed.

### Details
- No return-value or assertion changes are needed in any of the four tests — none of
  them assert on `fetched_at` itself; they only exercise the freshness-decision branch
  (`force`/etag/sha comparison) that `_get_or_create_document()` returns.
- `test_unchanged_file_skips_reingest` is the one call that goes through a real
  `DocumentManager(db)` (not a `MagicMock`) — confirm after the edit that this path still
  reaches `handle_existing_document()` without raising, since that method's own
  `fetched_at`/`new_fetched_at` parameters are being widened to mandatory `str` in the
  same overall plan (see the companion `document_manager.py` implementation procedure).

## Compatibility considerations

- This is a test-only file; the change here has no runtime compatibility impact. It
  exists solely to keep this file passing once `ingester.py`'s signature changes land.

## Security considerations

N/A: test-only file, no security-relevant logic changed.

## Rollback considerations

- Independently revertable: reverting the four added keyword arguments has no effect on
  any other file. If `_get_or_create_document()`'s signature change is reverted first,
  these added keyword arguments become unrecognized-keyword `TypeError`s — revert both
  together as a pair, not in isolation.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/rag/ingestion/test_ingestion_freshness.py | Unit | `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -v` | All 4 `TestGetOrCreateDocumentFreshness` tests pass; `TestIsFileUnchanged`/`TestCrawlFilePayload` unaffected |

## Out of scope

- Adding new test coverage for `fetched_at` propagation itself (e.g., asserting the
  value reaches `handle_existing_document()`) — not requested by the source plan for
  this file; the plan's explicit propagation-verification coverage lives in
  `tests/rag/ingestion/test_ingester.py` and `tests/rag/ingestion/test_ingester_etag_guard.py`.

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
- Related target files: tests/rag/ingestion/test_ingestion_freshness.py
