## Goal
Make `CrawlOrchestrator.crawl_site` leave no running task behind: on every exit from the BFS
loop (budget stop, error, cancellation), cancel the remaining tasks, await them, and log
non-cancellation errors once, before `session_db` is closed and the HTTP client exits.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change: add a private async cleanup helper `_cancel_and_drain_pending` (new) to
`scripts/rag/ingestion/orchestrator.py` and call it from the `finally` path of `crawl_site`
before `session_db.close()`. Budget semantics, the FIRST_COMPLETED loop, the budget log
messages, and `_process_crawl_url_async` are untouched.

## Assumptions
- Revalidated 20261109 against current source: `crawl_site` is at `orchestrator.py:100-181`;
  budget `break` at L144 and L152; empty-pending exit at L163-164; `finally` closes only
  `session_db` at L178-180; `pending` is already declared at L105, before the `try` and before
  `async with httpx.AsyncClient` — so no move of `pending` is needed, only the cleanup call.
- `Task.exception()` (used in the loop at L170) raises `CancelledError` for a cancelled task,
  so cleanup must collect results with `asyncio.gather(..., return_exceptions=True)` and must
  not reuse that call.
- Cancellation cannot interrupt a write: after `fetch_html` returns, `_process_crawl_url_async`
  runs `extract_content`, `resolve_lang`, `save_http` (synchronous `path.write_bytes`,
  `crawl_persister.py:140`) and `enqueue_links` with no `await`; the only cancellation points
  are the `asyncio.sleep(self._crawl_delay)` and the httpx fetch awaits.
- Overlap judgment (`tools/check_plan_target_overlaps.py`, both plans Frozen):
  `orchestrator.py` is also targeted by ragrev014 (per-URL robots guard at the start of
  `_process_crawl_url_async`) and ragrev018 (code after the `save_http` call); compatible,
  this change edits only the `finally` path of `crawl_site`; no ordering requirement.
- UNK-01 (bounded cancellation grace) is non-blocking: all current awaits are cancellable
  httpx and `asyncio.sleep` calls.
- If the outer `crawl_site` task itself is cancelled, `await asyncio.gather(...)` in `finally`
  re-raises `CancelledError` (standard asyncio behavior); cancellation propagates by design.
  The never-raises guarantee covers task exceptions collected by the cleanup, matching AC-2.

## Design decisions
- `finally`-based cancel-and-gather: cleanup runs on every exit path (budget `break`,
  exception, outer cancellation), not only the budget paths.
- Cleanup order inside `finally`: cancel-and-gather first, then `session_db.close()`; the
  `async with` client then exits with nothing in flight.
- Helper is a private `async` method taking the current `pending` set, so `crawl_site` stays in
  its current complexity band (`radon cc`: `crawl_site` C (11) confirmed 20261109).
- Only not-yet-done tasks are cancelled; already-done tasks are still gathered so their
  unconsumed exceptions are retrieved once (prevents "Task exception was never retrieved").
- A collected exception is logged once at `logger.error` unless it is `CancelledError`.

## Alternatives considered
- `asyncio.TaskGroup` rewrite of the loop: rejected (changes FIRST_COMPLETED scheduling and
  budget logic, beyond a minimal fix).
- Cancelling only on the budget `break` paths: rejected (an exception or outer cancellation
  leaves the same orphans).

## Implementation
### Target file
`scripts/rag/ingestion/orchestrator.py`

### Procedure
1. Add the private helper `_cancel_and_drain_pending` (new) to `CrawlOrchestrator`, placed
   after `crawl_site` and before `_drain_queue_to_tasks`.
2. In `crawl_site`'s `finally` block (currently L178-180), call
   `await self._cancel_and_drain_pending(pending)` before the existing
   `if session_db is not None: session_db.close()` lines.
3. Change nothing else: no edit to the budget checks, the `while` loop, the `done` task
   exception logging, the `_drain_queue_to_tasks`, or `_process_crawl_url_async`.

### Method
Targeted edits with the `edit` tool; the helper body is the only new code.

### Details
Helper (adapt names/messages to file style; docstring one line plus a blank line as elsewhere):

```python
    async def _cancel_and_drain_pending(self, pending: set[asyncio.Task]) -> None:
        """Cancel not-yet-done tasks, await all with gathered results, and log a non-cancellation error once; never raises.

        `Task.exception()` raises `CancelledError` for cancelled tasks, so results are collected with `gather(..., return_exceptions=True)` instead (ragrev013).
        """
        for t in pending:
            if not t.done():
                t.cancel()
        results = await asyncio.gather(*pending, return_exceptions=True)
        for result in results:
            if isinstance(result, BaseException) and not isinstance(result, asyncio.CancelledError):
                logger.error("Crawl cleanup error: %s", result)
```

`finally` becomes:

```python
            finally:
                await self._cancel_and_drain_pending(pending)
                if session_db is not None:
                    session_db.close()
```

Notes:
- `pending` at this point is the set reassigned by `done, pending = await asyncio.wait(...)`
  (L165-168) plus tasks added by the last `_drain_queue_to_tasks` call; both done and running
  tasks are covered.
- An empty `pending` set is a no-op: `gather()` with no awaitables returns immediately.
- `asyncio` is already imported; no new imports.
- `mypy`: `gather(..., return_exceptions=True)` returns `list[BaseException | Any]`; the
  `isinstance` checks narrow it. If mypy flags the union, annotate `results: list[object]`.

## Compatibility considerations
- Budget semantics and the budget-stop log messages are unchanged (REQ-003); existing tests
  `test_stops_at_max_pages` and `test_max_pages_warning_logged` must pass unmodified (AC-3).
- Shared file with ragrev014/ragrev018 procedures: they edit `_process_crawl_url_async`, this
  document edits only `crawl_site`'s `finally`; compatible in any order.
- `WebCrawler.crawl` calls `crawl_site` per target in one event loop
  (`crawler.py:121`); after this change the next site's crawl starts with no orphans.

## Security considerations
No new external input or surface. `gather(return_exceptions=True)` prevents unconsumed task
exceptions and keeps `crawl_site`'s original exception propagating (cleanup never raises).

## Rollback considerations
Single-file revert: remove the helper and the one `finally` call line. No data, schema, or
config change; no migration.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| New tests (seq 02 document) | `uv run pytest tests/rag/ingestion/test_crawler_integration.py -q` | new tests fail on HEAD (live tasks / post-return write), pass after this change |
| Ingestion regression | `uv run pytest tests/rag/ingestion -q` | green |
| Static gates | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria
- AC-1: after `crawl_site` returns from a budget stop with slow requests in flight, no task
  created by the crawl is still running.
- AC-2: a task raising a non-cancellation exception during cleanup is logged once and does not
  make `crawl_site` raise; cancelled tasks are silent.
- AC-3: `test_stops_at_max_pages` and `test_max_pages_warning_logged` pass unmodified; persisted
  JSON files valid.
- AC-4: no "never retrieved" text in captured asyncio logs; file list unchanged after return.
- All static gates clean.

## Out of Scope
- Concurrency settings, budget semantics, the typed fetch result and redirect work of sibling
  plans.
- Atomic (temp file plus rename) writes for crash safety — belongs to ragrev017.
- Bounded cancellation grace for non-cancellable awaits (UNK-01; revisit only if a
  non-cancellable await is added).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion seq 02 document carries the tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | no documentation change in this plan |

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
- **Requirement ID**: `REQ-001`..`REQ-003`
- **Source issue**: issues/20261108-131231_ragrev013_crawl-orphaned-tasks-budget.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170226_ragrev013_crawl-orphaned-tasks-budget.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-225207
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`
