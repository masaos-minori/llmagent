## Goal
Add new test coverage to `tests/rag/ingestion/test_crawler_retry_boundary.py` asserting
that `fetched_at` in the crawl JSON payload produced via the HTTP crawl path
(`WebCrawler.crawl_site()` -> `_save_crawl_file()`) is canonical UTC
(`YYYY-MM-DDTHH:MM:SSZ`, `Z`-suffixed, round-trip parseable) once
`scripts/rag/ingestion/crawler.py`'s Phase 2 migration lands. This file currently has
zero `fetched_at` references.

## Scope
- In scope: `tests/rag/ingestion/test_crawler_retry_boundary.py` only — adding one new
  test function that exercises the existing HTTP-mocked `crawl_site()` flow already used
  by `test_retry_on_503_then_succeeds()`/`test_skip_304_response()`, then reads back the
  crawl JSON file written under `tmp_path` and asserts on `fetched_at`'s format.
- Out of scope: `crawler.py`'s own generation-logic change (own implementation
  document); `tests/rag/ingestion/test_crawler_targets_file.py`'s mtime-derived
  `file://`-path coverage (own implementation document, this batch);
  `tests/rag/ingestion/test_crawler_integration.py`'s and
  `tests/rag/ingestion/test_chunk_splitter.py`'s own `fetched_at` coverage (separate
  implementation documents per the source plan's Phase 5 list).

## Assumptions
- `crawler.py`'s Phase 2 migration (this plan) has landed by the time this test is
  executed: `_save_crawl_file()` generates `fetched_at` via
  `datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")` instead of
  `datetime.now().isoformat(timespec="seconds")` (naive local time, no `Z`) — confirmed
  as the target design in `plans/20260820-095054_plan.md`'s crawler.py Design item 1.
  Before migration, the new test is expected to fail; that is intentional
  regression-locking, not a test defect.
- Crawl JSON output files are written under `self._rag_src_dir` (config `rag_src_dir`,
  already pointed at `tmp_path` by this file's existing `_get_base_cfg()` helper) with
  filename pattern `{ts}-{slug}.json` via `_make_crawl_filepath()` — confirmed by reading
  `crawler.py`. The new test can locate them with a glob under `tmp_path` without needing
  to predict the exact slug.
- A 304 response (`test_skip_304_response()`'s scenario) never reaches
  `_save_crawl_file()`, so no crawl JSON file is produced in that case — the new
  `fetched_at` assertion belongs with a 200-response scenario, not the 304 case.

## Design decisions
- Verify `fetched_at` by reading back the on-disk JSON file the crawler actually wrote,
  not by mocking or inspecting internal state — matches this file's existing black-box
  style (asserting on `respx` call counts / route flags) and stays resilient to internal
  refactors of `_save_crawl_file()` as long as its file-output contract holds.
- Validate the canonical form with a regex anchored to the exact
  `YYYY-MM-DDTHH:MM:SSZ` shape plus a round-trip parse, rather than a loose
  substring check — a bare "contains `Z`" check would pass for accidentally malformed
  values.
- Add the new coverage as a separate test function rather than folding it into
  `test_retry_on_503_then_succeeds()` — keeps each test asserting one behavior (existing
  retry-count assertion vs. new `fetched_at`-format assertion), consistent with this
  file's current one-test-one-boundary style.

## Alternatives considered
- Asserting `fetched_at` inside the existing `test_retry_on_503_then_succeeds()` —
  rejected: conflates two unrelated boundary conditions (retry count vs. timestamp
  format) in one test, making a future failure ambiguous about which behavior broke.
- Freezing time (e.g. `freezegun`) to assert an exact `fetched_at` value — rejected as
  unnecessary precision; the plan's acceptance criterion is "canonical UTC format," not
  "exact clock value," and freezing time would add a new time-mocking dependency to this
  file for no additional coverage value.
- Comparing `fetched_at` against `last_modified` (mtime) — not applicable to the HTTP
  path, where `last_modified` comes from the HTTP response header, not filesystem mtime;
  mtime-derived comparison belongs to the `file://` path covered in
  `test_crawler_targets_file.py`.

## Implementation
### Target file
`tests/rag/ingestion/test_crawler_retry_boundary.py`

### Procedure
1. Add a new test function (e.g. `test_fetched_at_is_canonical_utc_on_success`) using
   the same `respx.mock` context manager and `_get_base_cfg(tmp_path)` helper already
   used by the existing tests.
2. Mock a single 200 response for `"http://example.com"` (a plain `return_value=` mock
   is sufficient; retry behavior is not what this test targets).
3. Instantiate `WebCrawler(config=...)` and `await crawler.crawl_site("http://example.com", "en")`.
4. Locate the produced crawl JSON file(s) under `tmp_path` (e.g.
   `sorted(tmp_path.glob("*.json"))`), load the contents, and assert:
   - `fetched_at` matches `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`.
   - the value round-trip-parses to a valid, timezone-aware UTC `datetime`.
5. Leave all four existing test functions unchanged.

### Method
Additive change — one new, independent test function; no modification to existing test
bodies or the `_get_base_cfg()` helper.

### Details
- Reuse `respx.mock` / `WebCrawler(config=...)` exactly as the existing tests do; no new
  fixtures are needed for a single new test.
- If the mocked page could yield more than one crawl JSON file (e.g. self-referential
  links), either assert `len(...) == 1` first or assert the format property holds for
  every file found — implementer's judgment based on what the mocked response actually
  produces for `"http://example.com"` with no outbound links.
- This file does not currently import `orjson`/`json`, `re`, or `datetime` — add only
  what the new assertion needs.

## Compatibility considerations
N/A: test-only file; adding one new test function does not change any existing test's
behavior or signature, and there is no downstream consumer of this file.

## Security considerations
N/A: test-only file exercising a mocked HTTP crawl inside a `tmp_path` sandbox — no new
external input surface or trust boundary is introduced.

## Rollback considerations
- Purely additive; revert by removing the new test function if it proves flaky or the
  canonical-format decision changes upstream.
- Expected to be added in the same change window as `crawler.py`'s own Phase 2
  migration, since the new test fails against pre-migration `crawler.py` by design
  (regression lock) — not intended to be committed alone as a standalone gate against
  unmigrated source.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_crawler_retry_boundary.py -v` — all five test
  functions (four existing + one new) pass after `crawler.py`'s migration lands.
- Confirm the new test fails against pre-migration `crawler.py` (sanity-check that it
  actually exercises the changed behavior), then confirm it passes post-migration.

## Out of scope
- `crawler.py`'s own generation-logic change (own implementation document).
- `test_crawler_targets_file.py`'s mtime-derived `fetched_at` coverage for the `file://`
  path (own implementation document, this batch).
- `test_crawler_integration.py`'s and `test_chunk_splitter.py`'s own `fetched_at`
  coverage (separate implementation documents per the source plan's Phase 5 list).

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
- Related target files: tests/rag/ingestion/test_crawler_retry_boundary.py
