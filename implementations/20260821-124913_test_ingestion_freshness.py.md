## Goal
Confirm and document that `tests/rag/ingestion/test_ingestion_freshness.py` requires no code
change for the `CrawlPayload` -> `CrawlJsonPayload` migration in
`scripts/rag/ingestion/crawler.py`.

## Scope
- In scope: verification only — no edit to `tests/rag/ingestion/test_ingestion_freshness.py`
  is required by this plan.
- Out of scope: `crawler.py`'s own migration (own implementation document).

## Assumptions
- Independently re-verified (this document's own investigation, not just the source plan's
  claim): `TestCrawlFilePayload` (lines 51-106, 2 tests:
  `test_etag_and_last_modified_in_payload`, `test_etag_is_sha256_of_content`) contains zero
  references to the `CrawlPayload`/`CrawlFilePayload` Python symbol. The class name's
  "CrawlFilePayload" substring is coincidental — no such symbol exists anywhere in the
  codebase. Both tests black-box-test `WebCrawler.crawl_file()`'s written JSON via
  `orjson.loads()` on the on-disk file.
- `crawler.py`'s `crawl_file()` local-file path (lines 100-142, dict literal at 122-134)
  unconditionally assigns `"etag": sha256` and `"last_modified": mtime_iso` as direct dict
  keys — no conditional-insertion logic. This is a structurally different code path from the
  HTTP-crawl path (`_save_crawl_file()`, formerly referenced as `_save_crawl_result()`, lines
  314-347) where the actual conditional-insertion behavior this plan changes lives (lines
  338-341: `if etag is not None: payload["etag"] = etag`, same for `last_modified`).
  `TestCrawlFilePayload` never exercises the HTTP-crawl path.
- No other test in the file (`TestIsFileUnchanged`, lines 18-45; `TestGetOrCreateDocumentFreshness`,
  lines 152-237, plus helpers `_make_ingester`/`_make_fake_db`, lines 112-149) references
  `CrawlPayload` or constructs/parses crawl JSON — they operate on plain Python
  strings/kwargs and an in-memory SQLite fixture, with no JSON serialization involved.

## Design decisions
N/A — no code change is being designed; this document records the verification outcome.

## Alternatives considered
- Rewriting `TestCrawlFilePayload` proactively to reference `CrawlJsonPayload` by name, "just
  in case" — rejected: the class contains no reference to the old type either, so adding a new
  one would be introducing an untested coupling that doesn't exist today, contrary to the
  workflow's Out-of-scope rule against unrelated refactoring.

## Implementation
### Target file
`tests/rag/ingestion/test_ingestion_freshness.py`

### Procedure
- No code edit required. At implementation time, after `crawler.py`'s migration lands, run
  this file's test suite as a regression check only (see Validation plan).

### Method
N/A — verification-only document.

### Details
- If, contrary to this analysis, `crawler.py`'s `crawl_file()` local-file path itself is
  altered by the migration (not just `_save_crawl_file()`'s HTTP path), re-verify
  `TestCrawlFilePayload` against the changed code before assuming this document's "no change"
  conclusion still holds.

## Compatibility considerations
N/A.

## Security considerations
N/A — test-only file, no external input surface.

## Rollback considerations
N/A — no change is made.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -v` after `crawler.py`'s
  migration lands — expect all existing tests (including the 2 in `TestCrawlFilePayload`) to
  keep passing unchanged, confirming the "no code change needed" conclusion in practice, not
  just by static reading.

## Out of scope
- Any change to `crawler.py` itself.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260820-094150_plan.md
- Source implementation procedure: N/A
- Generated at: 20260821-124913
- Related target files: test_ingestion_freshness.py
