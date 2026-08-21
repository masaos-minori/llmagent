## Goal
Confirm and document that `tests/rag/ingestion/test_crawler_integration.py` requires no
assertion edit for the always-present-`etag`/`last_modified`-keys change to
`scripts/rag/ingestion/crawler.py`'s `_save_crawl_file()`.

## Scope
- In scope: verification only — no edit to `tests/rag/ingestion/test_crawler_integration.py`
  is required by this plan, as currently written.
- Out of scope: `crawler.py`'s own migration (own implementation document); adding new
  regression coverage for `_save_crawl_file()` (a genuine gap, but a new test, not an edit —
  see Out of scope below).

## Assumptions
- **Correction (adversarial review, 2026-08-21) applied to `plans/20260820-094150_plan.md`:**
  the plan's original Affected-areas entry for this file said "Update `etag`/`last_modified`
  assertions to expect always-present keys" — independently re-verified this is incorrect.
  This file (312 lines, 12 test functions across 5 classes: `TestHttpRetryOnTransientFailure`,
  `TestResponseSkippingContentFetch`, `TestMaxPagesBoundaryCondition`, `TestBfsQueueOrdering`,
  `TestLinkFiltering`) never calls `_save_crawl_file()` — the actual conditional-insertion site
  at `crawler.py:338-341` — and never parses an on-disk crawl JSON artifact via `orjson`/`json`.
- The only two `etag`/`last_modified` references in the file are:
  - Line 90: `html, etag, last_modified = result` inside `test_success_after_retry` — a tuple
    unpack of `_fetch_html_async()`'s return value (a pre-payload-construction stage); neither
    variable is asserted on afterward.
  - Lines 144-145: `_, title, text, code_blocks, etag, last_modified = result` /
    `assert etag == "abc123"` inside `test_conditional_headers_sent_with_request` — asserts a
    **present** value (mocked `ETag` response header), unrelated to the None-fallback behavior
    this plan changes.
- No fixture in this file constructs `lang` outside `{"ja","en"}`, empty `content` without
  `code_blocks`, or any other value the plan's new construction-time validation would reject —
  confirmed by grep across the file.

## Design decisions
N/A — no code change is being designed; this document records the verification outcome.

## Alternatives considered
- Adding a new test here that calls `_save_crawl_file()` directly and asserts both keys are
  always present with `None` fallback — this would genuinely close the coverage gap the
  plan's original (incorrect) entry seems to have been gesturing at, but authoring a *new*
  test is outside this document-only workflow's scope (`prompts/02_plan-to-implementation-
  procedure.md` explicitly forbids implementation; new-test-authoring belongs to
  `crawler.py`'s own implementation document's Validation plan, which already lists
  `tests/rag/ingestion/test_crawler_integration.py` as a command to re-run — the actual new
  assertion, if wanted, should be proposed there or in a follow-up issue, not invented here).

## Implementation
### Target file
`tests/rag/ingestion/test_crawler_integration.py`

### Procedure
- No code edit required in this file for this plan's migration. Continue to include it in the
  regression test run for `crawler.py`'s changes (see Validation plan).

### Method
N/A — verification-only document.

### Details
- If a future requirement wants explicit regression coverage of `_save_crawl_file()`'s
  always-present-keys behavior, file it as a new issue/plan item rather than folding it into
  this migration's scope.

## Compatibility considerations
N/A.

## Security considerations
N/A — test-only file, no external input surface.

## Rollback considerations
N/A — no change is made.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` after `crawler.py`'s
  migration lands — expect all 12 existing tests to keep passing unchanged, confirming no
  regression in the fetch-stage / BFS / link-filtering logic this file actually covers.

## Out of scope
- Authoring a new test to cover `_save_crawl_file()`'s always-present-keys behavior directly —
  flag as a documentation gap in the source plan, not an item for this document-only phase.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260820-094150_plan.md
- Source implementation procedure: N/A
- Generated at: 20260821-124913
- Related target files: test_crawler_integration.py
