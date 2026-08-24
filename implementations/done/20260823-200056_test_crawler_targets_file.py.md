## Goal
Add new test coverage to `tests/rag/ingestion/test_crawler_targets_file.py` asserting
that, for a `file://` source crawled via `WebCrawler.crawl_file()`, the resulting
`fetched_at` is derived from the source file's `stat.st_mtime` (in UTC, canonical
`Z`-suffixed form) rather than wall-clock time, per `scripts/rag/ingestion/crawler.py`'s
Design item 1 in `plans/20260820-095054_plan.md`. This file currently has zero
`fetched_at` references; its only `crawl_file()`-adjacent test
(`test_crawl_dispatches_file_url_to_crawl_file`) mocks `crawl_file()` entirely via
`patch.object`, so it never exercises the real payload-construction body.

## Scope
- In scope: `tests/rag/ingestion/test_crawler_targets_file.py` only — adding one new
  test function that calls the real (unmocked) `WebCrawler.crawl_file()` against a
  `tmp_path`-created file with a controlled mtime, then reads back the produced crawl
  JSON and asserts `fetched_at` equals the mtime-derived canonical UTC string.
- Out of scope: `crawler.py`'s own generation-logic implementation (own implementation
  document); `tests/rag/ingestion/test_crawler_retry_boundary.py`'s HTTP-path
  canonical-UTC assertion (own implementation document, this batch);
  `parse_targets_file()`/`main()` CLI argument tests and the existing
  mock-based dispatch test already in this file (unaffected — no `fetched_at`
  involvement).

## Assumptions
- `crawler.py`'s Phase 2 migration (this plan) has landed: `crawl_file()` derives
  `fetched_at` from `stat.st_mtime` in UTC (e.g.
  `datetime.fromtimestamp(stat.st_mtime, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")`) instead
  of `datetime.now().isoformat(timespec="seconds")` — confirmed as the target design in
  `plans/20260820-095054_plan.md`'s crawler.py Design item 1 and Implementation steps
  Phase 2. Before migration, the new test is expected to fail; that is intentional
  regression-locking, matching the sibling test-file document's approach.
- `crawl_file()` already computes `mtime_iso` from the same `stat` object used for
  `last_modified` (naive local time, per the current source) — the plan's design
  explicitly wants `fetched_at` and `last_modified` mtime-consistent after migration.
  The new test therefore pins a controlled mtime and asserts `fetched_at`'s value
  against a value computed independently in the test from that same mtime, rather than
  merely checking that `fetched_at` "looks like" a timestamp.
- `os.utime(path, (atime, mtime))` reliably sets a file's mtime to a known
  integer-second value in this project's execution environment (Linux, per
  `AGENTS.md`/`rules/env.md`) — no sub-second precision is required since the canonical
  format truncates to whole seconds.
- `crawl_file()` writes its output JSON via `self._make_crawl_filepath(url)` under
  `self._rag_src_dir` (config `rag_src_dir`); the existing
  `test_crawl_dispatches_file_url_to_crawl_file()`'s config dict already sets
  `rag_src_dir: str(tmp_path)`, so the same config pattern locates the output file for
  the new test.

## Design decisions
- Set a known, deliberately non-current mtime on the source file with `os.utime()`
  before calling `crawl_file()`, rather than asserting only "fetched_at is parseable
  UTC" — a bare format check (as used for the HTTP path in the sibling document) would
  not distinguish an mtime-derived value from a wall-clock-derived one; only a
  controlled, distinguishable mtime proves the source is `stat.st_mtime`.
- Call the real `crawl_file()` (no `patch.object`), unlike this file's existing
  dispatch test — that test's job (assert `crawl()` routes `file://` to `crawl_file()`)
  is already satisfied by mocking; this new test's job is the opposite (assert what
  `crawl_file()` itself produces), so it must not mock the method under test.
- Read the output JSON back from disk and assert an exact string match, computed
  independently in the test via
  `datetime.fromtimestamp(known_mtime, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")` — an
  exact-string comparison is no more complex than a regex-plus-tolerance check, and the
  test fully controls the mtime input so exactness is achievable.

## Alternatives considered
- Mocking `Path.stat()` to return a fake `stat_result` — rejected: heavier than
  `os.utime()` on a real `tmp_path` file, and `os.utime()` exercises the real filesystem
  stat path end-to-end, closer to production behavior.
- Asserting only that `fetched_at` matches the canonical-format regex (reusing the
  sibling document's HTTP-path check) without pinning mtime — rejected: does not verify
  the mtime-vs-wall-clock source distinction, which is the specific behavior this plan
  changes for the `file://` path (the plan's Design item 1 "latent inconsistency"
  callout).
- Comparing `fetched_at` to `time.time()` at test-invocation time to prove it is *not*
  wall-clock-derived — rejected as indirect and weaker than a direct equality check
  (near-equality could occur coincidentally); pinning the mtime and asserting exact
  equality is deterministic.

## Implementation
### Target file
`tests/rag/ingestion/test_crawler_targets_file.py`

### Procedure
1. Add a new test function (e.g. `test_crawl_file_fetched_at_derived_from_mtime`) in
   the "crawl() dispatch tests" section, alongside
   `test_crawl_dispatches_file_url_to_crawl_file`.
2. Create a real source file under `tmp_path` (e.g. `tmp_path / "source.txt"` with
   arbitrary content).
3. Set a known mtime via `os.utime(source_path, (fixed_epoch_seconds, fixed_epoch_seconds))`,
   choosing a value clearly distinct from "now" (e.g. a fixed past date).
4. Build a minimal valid `WebCrawler` config (mirroring
   `test_crawl_dispatches_file_url_to_crawl_file`'s dict, with
   `rag_src_dir: str(tmp_path)`) and instantiate `WebCrawler(config=config)`.
5. Call `crawler.crawl_file(source_path, "en")` directly (no mocking) and assert it
   returns `1`.
6. Locate the produced JSON file under `tmp_path` (glob by `*.json`, distinguishable
   from the non-JSON source file), load it, and assert
   `payload["fetched_at"] == datetime.fromtimestamp(fixed_epoch_seconds, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")`.
7. Leave all existing test functions in the file unchanged.

### Method
Additive change — one new, independent test function; no modification to
`parse_targets_file()` tests, CLI tests, or the existing dispatch test.

### Details
- Add imports needed for the new test (`os`, `orjson` or `json`, and
  `datetime`/`UTC`) alongside this file's existing imports (`asyncio`, `sys`, `Path`,
  `patch`) — none of these are currently imported here.
- Avoid ambiguity between the source file and the output JSON file when globbing
  `tmp_path` — filter by suffix (`*.json`) since the source file is created with a
  non-`.json` extension (e.g. `.txt`); per `crawler.py`, `crawl_file()` writes directly
  into `_rag_src_dir` with `mkdir(parents=True, exist_ok=True)` (no subdirectory
  nesting), so a flat `*.json` glob under `tmp_path` is expected to be sufficient —
  confirm at implementation time.
- Keep the fixed mtime value a named constant with a short comment stating it is
  deliberately not "now," so the test's intent (mtime vs. wall-clock) is
  self-documenting.

## Compatibility considerations
N/A: test-only file; adding one new test function does not change any existing test's
behavior, and `parse_targets_file()`/`main()` CLI tests are untouched.

## Security considerations
N/A: test-only file operating on a `tmp_path`-sandboxed local file — no network or
untrusted-input surface is introduced.

## Rollback considerations
- Purely additive; revert by removing the new test function if it proves flaky (e.g. an
  environment where `os.utime()` sub-second behavior differs) or if the source design
  changes.
- Expected to be added in the same change window as `crawler.py`'s own Phase 2
  migration, since the new test fails against pre-migration `crawler.py` by design
  (wall-clock `fetched_at` would not equal the pinned mtime-derived value) — not
  intended as a standalone gate against unmigrated source.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_crawler_targets_file.py -v` — all existing
  tests plus the new one pass after `crawler.py`'s migration lands.
- Confirm the new test fails against pre-migration `crawler.py` (wall-clock `fetched_at`
  would not equal the pinned mtime-derived value), then confirm it passes
  post-migration, to validate the test actually locks in the intended behavior change.

## Out of scope
- `crawler.py`'s own `stat.st_mtime`-derivation implementation (own implementation
  document).
- `test_crawler_retry_boundary.py`'s HTTP-path canonical-UTC assertion (own
  implementation document, this batch).
- Any change to `parse_targets_file()`, `main()` CLI argument handling, or the existing
  mock-based `crawl()` dispatch test in this file.

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
- Related target files: tests/rag/ingestion/test_crawler_targets_file.py
