## Goal

Add test coverage to `tests/rag/ingestion/test_crawler_integration.py` proving that
the `fetched_at` value `WebCrawler` writes into a crawl output JSON for the live
HTTP-fetch path is canonical UTC (`YYYY-MM-DDTHH:MM:SSZ`, `Z`-suffixed, parseable),
once `_save_crawl_file()` is changed from
`datetime.now().isoformat(timespec="seconds")` to
`datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")`. This file currently has zero
`fetched_at` references (confirmed by reading the file in full — 313 lines, four test
classes exercising `_fetch_html_async()`, `_fetch_and_extract_async()`,
`_should_enqueue_link()`, and BFS queue mechanics — none touches `_save_crawl_file()`
or `CrawlPayload` construction today).

## Scope

**In scope**
- `tests/rag/ingestion/test_crawler_integration.py` only: add test coverage for
  `_save_crawl_file()`'s `fetched_at` generation (the HTTP/live-crawl path).

**Out of scope**
- The local-`file://`-source `fetched_at` derivation (`crawl_file()`, mtime-based) —
  per the source plan's Affected areas table this belongs to
  `tests/rag/ingestion/test_crawler_targets_file.py` and/or
  `test_crawler_retry_boundary.py`, which have their own implementation documents.
- Any change to `scripts/rag/ingestion/crawler.py` itself — it has its own
  implementation document under this same plan.

## Assumptions

- This test cannot pass until `crawler.py`'s own implementation lands: the `datetime`
  import widens to `from datetime import UTC, datetime`, and both `CrawlPayload`
  construction sites (`crawl_file()`, `_save_crawl_file()`) switch to a UTC-based
  `fetched_at`. Confirmed by reading the current `crawler.py`: today it imports only
  `datetime` and `_save_crawl_file()` uses
  `datetime.now().isoformat(timespec="seconds")` (naive local time, no `Z` suffix,
  colon-containing offset-less ISO format — not the target canonical form).
- `_save_crawl_file()` is a synchronous, directly callable method taking
  `(url, title, lang, content, code_blocks, etag=None, last_modified=None)` and
  returning the `Path` it wrote — confirmed by reading its signature and body. It can
  be called directly in a test without going through the async fetch/BFS machinery,
  avoiding the need for respx/HTTP mocking for this specific assertion.
- `self._rag_src_dir` is set from `config["rag_src_dir"]` at `__init__` time
  (confirmed by reading `WebCrawler.__init__()`); the existing `mock_config` fixture
  in this file already sets `"rag_src_dir": "/tmp/crawl-test-output"` — the new test
  should override this to a `tmp_path`-backed value rather than writing into the
  shared `/tmp` path the fixture currently hardcodes, to keep the test hermetic.

## Design decisions

- Call `_save_crawl_file()` directly rather than driving the full async
  `crawl_site()`/BFS path — the `fetched_at` generation logic lives entirely inside
  `_save_crawl_file()`, so a direct call is the minimal boundary that exercises the
  behavior under test without coupling to unrelated BFS/retry mechanics this file's
  other test classes already cover separately.
- Assert both structurally (`str.endswith("Z")`) and semantically (parseable via
  `datetime.strptime(..., "%Y-%m-%dT%H:%M:%SZ")` or `datetime.fromisoformat()` after
  normalizing the `Z`, and the parsed value's `tzinfo` is UTC / the value round-trips)
  — a bare substring check alone would not catch a value that merely happens to end
  in a literal `"Z"` character without being validly formatted UTC.
- Follow this file's existing convention of a dedicated `Test*` class per behavior
  (e.g. `TestFetchedAtIsCanonicalUtc`) rather than adding a loose function, matching
  `TestHttpRetryOnTransientFailure`, `TestResponseSkippingContentFetch`, etc.

## Alternatives considered

- Asserting only `"Z" in fetched_at` — rejected: too weak, would pass for malformed
  values containing a `Z` elsewhere; see Design decisions for the stronger check.
- Driving the assertion through `crawl_site()`'s full BFS/HTTP-mocked flow (as the
  file's other tests do for retry/skip behavior) — rejected as the primary test: adds
  respx/mock setup unrelated to what's being verified (`fetched_at` format is decided
  entirely inside `_save_crawl_file()`, independent of how it's reached); a direct
  call is simpler and equally valid per the source plan's Validation plan wording
  ("Every crawl payload has a UTC `fetched_at`").

## Implementation

### Target file
`tests/rag/ingestion/test_crawler_integration.py`

### Procedure
1. Confirm `crawler.py`'s own implementation document (this plan's Phase 2 step) has
   landed — `_save_crawl_file()` generates `fetched_at` via
   `datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")`. Do not write this test's
   fixtures ahead of that change landing.
2. Add a new test class, e.g. `TestFetchedAtIsCanonicalUtc`, alongside the existing
   four test classes.
3. In the new test, build a `WebCrawler` from a copy of `mock_config` with
   `"rag_src_dir"` pointed at `tmp_path` (or `tmp_path`'s string form).
4. Call `crawler._save_crawl_file(url="http://example.com/page", title="t",
   lang="en", content="body", code_blocks=[])` directly; capture the returned `Path`.
5. Read and parse the written JSON file (`orjson.loads(path.read_bytes())` or
   `json.loads(path.read_text())`), extract `payload["fetched_at"]`.
6. Assert the value ends with `"Z"` and is parseable as UTC via
   `datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")` (no exception raised).
7. Optionally add a second assertion/test that the parsed value is close to
   "now" (e.g. within a few seconds of `datetime.now(UTC)`) to confirm it is not a
   frozen/hardcoded string that happens to match the format.

### Method
- Direct synchronous call to `_save_crawl_file()` plus a filesystem read-back, no
  `respx`/HTTP mocking needed for this specific test class (the existing file already
  uses `respx`-based mocking per its module docstring for other classes; this new
  class does not require it since the method under test performs no HTTP I/O itself).

### Details
- Use a fresh `mock_config` copy (`dict(mock_config)` or a fixture override) with
  `"rag_src_dir": str(tmp_path)` rather than mutating the shared fixture dict in
  place, to avoid cross-test leakage within the same test session.
- `_save_crawl_file()` requires `etag`/`last_modified` only as optional keyword
  arguments (both default `None`); omit them unless a specific assertion needs them,
  keeping the fixture minimal per this test's narrow purpose.
- Do not assert on `title`/`lang`/`content`/`code_blocks` values beyond what's needed
  to construct a valid call — this test's sole responsibility is `fetched_at` format.

## Compatibility considerations

- Purely additive: does not modify any of the four existing test classes
  (`TestHttpRetryOnTransientFailure`, `TestResponseSkippingContentFetch`,
  `TestMaxPagesBoundaryCondition`, `TestBfsQueueOrdering`) or the shared
  `mock_config` fixture's defaults (only a local override is used).
- Must fail before `crawler.py`'s UTC-generation change lands (current
  `datetime.now().isoformat(timespec="seconds")` output does not end with `Z`) and
  pass once it lands — confirms the test is not vacuously true.

## Security considerations

N/A: test-only file: exercises only local `tmp_path` file I/O and a direct method
call, no network request is made by the new test class, no external input surface.

## Rollback considerations

- Independently revertable: a new test class with no other test's dependency on it.
- If the UTC-generation change in `crawler.py` is ever reverted, this test should
  fail loudly rather than be deleted — it is the test in this plan's Affected areas
  responsible for the HTTP-path canonical-UTC guarantee (the local-file-path
  guarantee is covered separately, see Out of scope).

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` — all four
  existing test classes plus the new `fetched_at` format test(s) pass.
- `rg -n "fetched_at" tests/rag/ingestion/test_crawler_integration.py` shows at least
  one match after the change (0 today, per the source plan's Affected areas table).
- Cross-check the new assertion against the source plan's Validation plan row for
  `scripts/rag/ingestion/crawler.py`: "Every crawl payload has a UTC `fetched_at`."
  Combined with `test_crawler_retry_boundary.py`/`test_crawler_targets_file.py`'s own
  local-file-path coverage, this satisfies that row's "both HTTP and local-file paths"
  requirement jointly, not from this file alone.

## Out of scope

- The local-`file://`-source `fetched_at` derivation from `stat.st_mtime`
  (`crawl_file()`) — covered by `test_crawler_targets_file.py` and/or
  `test_crawler_retry_boundary.py` per the source plan's Affected areas table.
- Any change to `scripts/rag/ingestion/crawler.py` itself.
- Testing that `fetched_at` is *identical across multiple chunks* of one crawl record
  — that is `tests/rag/ingestion/test_chunk_splitter.py`'s responsibility (its own
  implementation document), since chunking happens downstream of the crawler.

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
- Related target files: tests/rag/ingestion/test_crawler_integration.py
