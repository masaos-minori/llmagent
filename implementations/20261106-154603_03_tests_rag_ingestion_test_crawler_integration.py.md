## Goal

Replace the two vacuous max_pages tests in `TestMaxPagesBoundaryCondition`
(`test_stops_at_max_pages`, `test_max_pages_warning_logged`) with real async-crawl
assertions (`REQ-005`): the new semantics must fail on the old code's under-delivery
scenario and pass on the new code, asserting the stop WARNING wording (persisted vs
scheduled) via `caplog`. Keep `test_max_pages_fallback_default` unchanged.

## Scope
**Release unit**: crawl-persisted-budget (Plan Phase 2)

## Assumptions
- The vacuous tests currently patch `crawler.crawl_site` / `crawler.orchestrator._drain_queue_to_tasks`
  and assert nothing (`pass`), so replacing them loses no coverage (AC-3).
- `WebCrawler(config=...)` builds a real orchestrator; `crawl_site(start_url, hint_lang)`
  runs the real BFS loop with respx-stubbed fetches.
- `test_max_pages_fallback_default` (asserts `crawler._max_pages == 200`) is a real
  characterization test and stays.

## Design decisions
- **Real crawls, not patched internals.** Drive `await crawler.crawl_site(...)` with
  respx routes so the actual guard logic executes; assert on captured warnings via
  `caplog` and on persisted artifacts. This pins the new behavior instead of the
  old "verify the guard exists by checking the source logic" `pass`.
- **Assert the warning wording.** The new guards emit `"persisted budget reached"`
  and `"scheduling budget reached"`; assert these substrings appear in the captured
  records (AC-3, REQ-004 wording).
- **Under-delivery scenario.** A 304-heavy run at a small `max_pages` must now
  persist pages the old code would have dropped — assert persisted count > 0 where
  the old code produced 0.

## Alternatives considered
- Keeping the patched-internation approach: rejected — it asserted nothing.
- Asserting only on `respx.calls`: insufficient — must also assert the WARNING
  wording to pin REQ-002/REQ-004 output.

## Implementation
### Target file
- `tests/rag/ingestion/test_crawler_integration.py`

### Procedure
1. Rewrite `test_stops_at_max_pages` as a real async crawl at `max_pages=N` that
   exceeds N via links, asserting the persisted-budget WARNING and that persisted
   pages equal N (not the visited count).
2. Rewrite `test_max_pages_warning_logged` as a real async crawl asserting both the
   `"persisted budget reached"` and `"scheduling budget reached"` WARNING substrings
   via `caplog`.
3. Keep `test_max_pages_fallback_default` untouched.

### Method
- Build `WebCrawler(config=mock_config)` with `mock_config["max_pages"]` set low and
  `max_depth` high; stub five+ linked pages with respx so the BFS would visit more
  than `max_pages` when persisted.
- For `test_stops_at_max_pages`: after `await crawler.crawl_site(...)`, assert the
  number of chunk JSON files under `mock_config["rag_src_dir"]` equals `max_pages`
  (persisted budget), and that a `"persisted budget reached"` warning was logged.
- For `test_max_pages_warning_logged`: run a crawl that hits the scheduling cap
  (many non-persisted URLs) and assert both `"persisted budget reached"` and
  `"scheduling budget reached"` appear in `caplog.text`.
- Use `caplog.at_level(logging.WARNING, logger="rag.ingestion.orchestrator")` for
  the warning capture; attach `caplog.handler` to
  `logging.getLogger("rag.ingestion.orchestrator")` directly if capture is empty.

### Details
- Import `logging` at the top of the file (add to the existing imports) for
  `caplog.at_level`.
- Persisted-file assertion: `glob` the `rag_src_dir` for the persister's
  `{ts}-{slug}-{hash}.json` shape; count matches.
- The dedup assertion (AC-3): a crawl where two pages link to the same URL must
  fetch it once — assert `len(respx.calls)` for that URL equals 1 (can fold into one
  of the rewritten tests).
- Do not touch `test_max_pages_fallback_default` or any test outside
  `TestMaxPagesBoundaryCondition`.

## Compatibility considerations
Replacing vacuous tests changes what the suite pins but loses nothing (they asserted
nothing). The rewritten tests fail against current code (under-delivery / no summary
log) and pass after Phase 3.

## Security considerations
N/A: test-only changes, no input handling or credential change.

## Rollback considerations
Revert the commit to this test file. Only the two methods in
`TestMaxPagesBoundaryCondition` change.

## Validation plan
- Rewritten tests fail against current code (Phase 2 RED), pass after Phase 3.
- `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` passes, incl.
  `test_max_pages_fallback_default`.
- `uv run pytest tests/rag/ingestion` passes.
- Static gates: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll` — clean.

## Completion criteria
- `test_stops_at_max_pages` and `test_max_pages_warning_logged` are real async-crawl
  assertions of the new stop behavior and WARNING wording; they fail on old code and
  pass after the change.
- `test_max_pages_fallback_default` unchanged and green.
- Full ingestion suite green; static gates clean.

## Out of Scope
- New budget unit tests in `test_crawler_retry_boundary.py` (companion document).
- Any production-file change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace vacuous max_pages tests with real assertions (RED) | Pending | — | — | REQ-005 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|-------|----------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261106-073538_raging009_crawl-max-pages-pending-tasks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-154603
- **Related target files**: `tests/rag/ingestion/test_crawler_integration.py`
