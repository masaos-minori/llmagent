## Goal
Add the two tests that lock the no-orphan guarantee of `CrawlOrchestrator.crawl_site`
(ragrev013): a budget-stop-with-in-flight-tasks test and a cleanup-exception test, written
test-first so they fail on HEAD and pass once the cleanup helper (seq 01 document) lands.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change: add two new async tests to the existing
`TestMaxPagesBoundaryCondition` class in `tests/rag/ingestion/test_crawler_integration.py`.
Existing tests are not modified (AC-3). No source file is touched by this document.

## Assumptions
- Revalidated 20261109: `TestMaxPagesBoundaryCondition` is at L161-244 and already uses
  `respx`, `caplog`, the `mock_config` fixture (`crawl_delay = 0`, `crawl_concurrency = 3` at
  L19/L24), `tmp_path` as `rag_src_dir`, and `crawler.crawl_site(...)` — the new tests reuse
  this fixture pattern.
- Timing determinism (plan Risk mitigation): in-flight state is held by an `asyncio.Event` the
  test controls, never by fixed sleeps; assertions are on task state and file lists, not
  wall-clock.
- The budget `break` happens at the top of the loop before the next drain, so an orphan only
  exists if a task is still running when the budget check fires; the tests below construct
  exactly that state (fast page completes and persists while the slow page is still in flight).
- `Task.__del__` emits "Task exception was never retrieved" on garbage collection, so the
  "never retrieved" assertion captures the `asyncio` logger and forces `gc.collect()` after
  the crawl returns.
- Overlap judgment: `test_crawler_integration.py` is also a target of ragrev011 (fetch-result
  tests) and ragrev018 (a caller-side `save_http` test); compatible — this document adds new
  test methods to `TestMaxPagesBoundaryCondition` and touches no existing test.
- On HEAD (no cleanup yet) both tests must FAIL — this is the plan's expected outcome ("new
  test fails on HEAD (live tasks), passes after"); the `finally: event.set()` release keeps a
  failing run from hanging the suite.

## Design decisions
- Two tests, both inside `TestMaxPagesBoundaryCondition` (plan: "next to" it — same class
  reuses `_page` and the fixture pattern):
  - `test_no_orphaned_tasks_after_budget_stop` (new) (`REQ-001`, `REQ-004` / AC-1, AC-4)
  - `test_cleanup_exception_logged_once` (new) (`REQ-002` / AC-2)
- In-flight control: the slow respx handler awaits `event.wait()` on an `asyncio.Event` the
  test sets only in its own `finally`; deterministic, no sleeps.
- Orphan construction: `max_pages = 1`; `/start` links to `/fast` and `/slow`; `/fast`
  persists immediately (persisted becomes 1), `/slow` stays in flight; the next loop iteration
  hits the persisted-budget check while `/slow`'s task is still running and `break`s — the
  orphan state AC-1 targets.
- Liveness assertion: snapshot `asyncio.all_tasks()` before the crawl call; after
  `crawl_site` returns, assert every currently live task was in the snapshot
  (`asyncio.all_tasks() <= before`), i.e. no crawl-created task survives.
- Cleanup-exception construction: the slow handler converts the cleanup cancellation into a
  real error — `await event.wait()` inside `try`, `except asyncio.CancelledError: raise
  RuntimeError("cleanup boom")`. Cancellation is guaranteed to be delivered by the seq 01
  cleanup (the task is provably in flight at the budget stop), so the exception surfaces to
  `gather(return_exceptions=True)` deterministically. On HEAD the handler is never cancelled,
  the event releases in `finally`, the page is written, and the test fails on the
  file-list/log assertions — the required fail-on-HEAD behavior.

## Alternatives considered
- Fixed-sleep slow handlers: rejected (flaky, plan Risk explicitly rules out wall-clock
  assertions).
- Wrapping `asyncio.create_task` to capture crawl task identities: rejected — the
  `all_tasks()` before/after snapshot needs no production-code hooks.
- Cancelling the crawl from outside (outer cancellation test): deferred; the two paths in the
  plan (budget stop, cleanup exception) cover AC-1/AC-2; outer cancellation propagates
  `CancelledError` by design (see seq 01 Assumptions).

## Implementation
### Target file
`tests/rag/ingestion/test_crawler_integration.py`

### Procedure
1. Add `import gc` to the test file imports if not present (`asyncio` is already imported;
   verify).
2. Inside `TestMaxPagesBoundaryCondition`, after `test_max_pages_warning_logged`, add the two
   new tests sketched in Details. Do not modify the three existing tests.

### Method
`edit` tool, two appended test methods; run them targeted with
`uv run pytest tests/rag/ingestion/test_crawler_integration.py -q` before the seq 01 change
lands to confirm they fail, and again after to confirm they pass.

### Details
Sketch (adapt to file style; docstrings state the AC):

```python
    @pytest.mark.asyncio
    async def test_no_orphaned_tasks_after_budget_stop(
        self,
        mock_config: dict,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """AC-1/AC-4: a budget stop with a slow request in flight leaves no live task, no never-retrieved warning, and writes no file after return."""
        mock_config["max_pages"] = 1
        mock_config["max_depth"] = 2
        mock_config["rag_src_dir"] = str(tmp_path)
        release = asyncio.Event()

        async def slow_handler(request: httpx.Request) -> Response:
            await release.wait()
            return Response(200, text=self._page("Slow"))

        with respx.mock:
            respx.get("http://example.com/start").mock(
                return_value=Response(200, text=self._page("Alpha", ("/fast", "/slow")))
            )
            respx.get("http://example.com/fast").mock(
                return_value=Response(200, text=self._page("Fast"))
            )
            respx.get("http://example.com/slow").mock(side_effect=slow_handler)
            crawler = WebCrawler(config=mock_config)
            before = asyncio.all_tasks()
            try:
                with caplog.at_level(
                    logging.WARNING,
                    logger="rag.ingestion.orchestrator",
                ):
                    await crawler.crawl_site("http://example.com/start", "en")
                files_after_return = sorted(tmp_path.glob("*-*.json"))
                assert asyncio.all_tasks() <= before
                assert len(files_after_return) == 1
            finally:
                release.set()
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            gc.collect()

        assert sorted(tmp_path.glob("*-*.json")) == files_after_return
        assert "never retrieved" not in caplog.text

    @pytest.mark.asyncio
    async def test_cleanup_exception_logged_once(
        self,
        mock_config: dict,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """AC-2: a non-cancellation exception during cleanup is logged once and does not make crawl_site raise; cancelled tasks are silent."""
        mock_config["max_pages"] = 1
        mock_config["max_depth"] = 2
        mock_config["rag_src_dir"] = str(tmp_path)
        release = asyncio.Event()

        async def boom_handler(request: httpx.Request) -> Response:
            try:
                await release.wait()
            except asyncio.CancelledError:
                raise RuntimeError("cleanup boom") from None
            return Response(200, text=self._page("Boom"))

        with respx.mock:
            respx.get("http://example.com/start").mock(
                return_value=Response(200, text=self._page("Alpha", ("/fast", "/boom")))
            )
            respx.get("http://example.com/fast").mock(
                return_value=Response(200, text=self._page("Fast"))
            )
            respx.get("http://example.com/boom").mock(side_effect=boom_handler)
            crawler = WebCrawler(config=mock_config)
            try:
                with caplog.at_level(
                    logging.ERROR,
                    logger="rag.ingestion.orchestrator",
                ):
                    await crawler.crawl_site("http://example.com/start", "en")
            finally:
                release.set()

        boom_logs = [r for r in caplog.records if "cleanup boom" in r.getMessage()]
        assert len(boom_logs) == 1
        assert "never retrieved" not in caplog.text
```

Implementation notes:
- `respx.mock` + `side_effect=` with an async handler is the supported pattern; the handler must
  return a `Response`.
- The bounded `await asyncio.sleep(0)` yields after `release.set()` let a HEAD-run orphan drain
  its response so the post-return file-list comparison is meaningful; keep the count small and
  fixed (no wall-clock sleeps).
- Capture the `asyncio` logger too if the "never retrieved" text does not land in the
  orchestrator logger capture: add a second `caplog.at_level(..., logger="asyncio")` block or
  widen `caplog` level at the test decorator level.
- The error log message asserted here comes from the seq 01 helper (`Crawl cleanup error: %s`);
  assert on the exception text (`"cleanup boom"`) so the exact message wording may change
  without breaking the contract.
- If ragrev018's caller-side test lands first in this file, keep both additions independent.

## Compatibility considerations
- Existing budget tests run unmodified (AC-3).
- `mock_config` defaults (`crawl_delay = 0`, `crawl_concurrency = 3`) keep the fast/slow race
  deterministic without config changes beyond `max_pages`/`max_depth`/`rag_src_dir`.
- Tests use `WebCrawler.crawl_site` (the same entry point as the existing tests), so they
  exercise the real `finally` path including `session_db` handling.

## Security considerations
No production surface. Tests only mock HTTP locally via `respx`.

## Rollback considerations
Remove the two test methods (and the `gc` import if unused elsewhere). No production impact.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| New tests before the seq 01 change | `uv run pytest tests/rag/ingestion/test_crawler_integration.py -q -k "orphaned or cleanup_exception"` | FAIL on HEAD (live task / missing cleanup log) |
| New tests after the seq 01 change | same command | pass |
| File regression | `uv run pytest tests/rag/ingestion/test_crawler_integration.py -q` | green |
| Ingestion suites | `uv run pytest tests/rag/ingestion -q` | green |
| Determinism | run the file 3 consecutive times | identical results (no timing flakiness) |
| Static gates | `uv run ruff check`, `uv run mypy` | clean |

## Completion criteria
- Both tests exist in `TestMaxPagesBoundaryCondition` and fail on HEAD for the intended reason
  (live crawl task after return / cleanup log missing), with a short evidence note in the
  Execution Status.
- After the seq 01 change: both pass; `test_stops_at_max_pages` and
  `test_max_pages_warning_logged` unmodified and green; three consecutive runs identical.
- Static gates clean.

## Out of Scope
- Changes to any existing test.
- Source changes (covered by the seq 01 document).
- Atomic-write tests (ragrev017 scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261110-075116 | 20261110-075116 | test-first: write before the seq 01 source change |
| 2 | Add or update tests per Validation plan | Completed | 20261110-075116 | 20261110-075116 | this document is the test work |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-075116 | 20261110-075116 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261110-075116 | 20261110-075116 | no documentation change in this plan N/A: no documentation change in this plan |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-004`
- **Source issue**: issues/20261108-131231_ragrev013_crawl-orphaned-tasks-budget.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170226_ragrev013_crawl-orphaned-tasks-budget.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-225207
- **Related target files**: `tests/rag/ingestion/test_crawler_integration.py`