# max_pages budget is consumed by URLs that are never persisted

## Priority
Medium

## Summary
`CrawlOrchestrator.crawl_site` caps the crawl with `len(visited) >= max_pages`, and
`visited` is populated for every URL scheduled for a fetch task — including URLs that
then return HTTP 304, produce no content, are rejected by the language check, or fail
during fetch. A crawl capped at `max_pages` can therefore stop before persisting that
many pages, with the remaining queued URLs dropped.

### Verification (issue-to-plan cycle 20261106-104043)
- Confirmed line-by-line at HEAD `bdb9bed66`: guard `if len(visited) >= self._max_pages:
  break` at `orchestrator.py:104-110`; `visited.add(url)` before any fetch at `:144`;
  non-persist budget consumers — 304/None early return `:177-178`, empty extraction
  `:184-186`, unsupported resolved lang `:189-191`, task exceptions logged only `:126-127`;
  remaining queue dropped on break (queue is function-local).
- New finding (budget already overshoots): the guard runs once per loop iteration before
  `_drain_queue_to_tasks` schedules every queued URL without a per-URL cap check — with
  `visited=199`, a 50-URL queue, and `max_pages=200`, 50 more URLs are scheduled and fetched,
  exceeding the budget even on the all-success path.
- New finding: `enqueue_links` runs only after `save_http` succeeds (`:204`), so a failed URL
  both consumes budget and adds no frontier — failure-heavy crawls shrink coverage doubly.
- New finding (test vacuity): `TestMaxPagesBoundaryCondition.test_stops_at_max_pages` and
  `test_max_pages_warning_logged` (`tests/rag/ingestion/test_crawler_integration.py:160-206`)
  patch `crawl_site` and assert nothing ("verify the guard exists by checking the source
  logic", `pass`). The only real max_pages coverage is `test_max_pages_boundary`
  (`test_crawler_retry_boundary.py:62-76`), which pins `len(respx.calls) <= 1` — i.e.
  scheduled-fetch semantics — and must be characterized before redefining the budget.
- New finding (default drift): `crawler.py:66` defaults `max_pages` to 200, but
  `orchestrator.py:74` defaults to 500 on the same raw config dict — with the key absent,
  the guard uses 500 while `WebCrawler._max_pages` says 200. Out of scope for this fix;
  recorded as a new issue candidate in the plan.
- Docs status: `docs/21_rag/rag_05_01-configuration-reference.md:34` states "reaching it
  stops BFS for the site" (no persisted/scheduled distinction);
  `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` §2.1.1 describes `max_pages` as a BFS
  bound only — both need the semantics update.
- Coordination: `issues/20261106-073205_crawl002_remove-dead-orchestrator-crawl-method.md`
  is still open with no plan; its target (`CrawlOrchestrator.crawl`, `orchestrator.py:76-88`)
  is disjoint from this fix's region (`crawl_site` / `_drain_queue_to_tasks` /
  `_process_crawl_url_async`).

## Problem
- `scripts/rag/ingestion/orchestrator.py` `crawl_site`: the guard is
  `if len(visited) >= self._max_pages: break` at the top of the BFS loop.
- `_drain_queue_to_tasks` adds every dequeued, unvisited URL to `visited` before any
  fetch happens, then creates the fetch task.
- `_process_crawl_url_async` can consume that budget slot without persisting anything:
  304 / conditional-GET skip (`fetch_html` returns `None` → early return), empty
  extraction (`no content` → return), unsupported resolved language (→ return), or a
  task exception (logged only).
- Consequence: with many cached (304) or non-persistable URLs, the run reaches
  `max_pages` and breaks out while the queue still holds uncrawled URLs; the operator's
  page budget counts visited URLs, not persisted pages.

## Background
The orchestrator was extracted from WebCrawler to own BFS queue/semaphore orchestration;
`visited` serves both loop termination (no re-fetch) and the page budget, conflating
"scheduled" with "crawled". Tests cover retry/semaphore behavior
(`tests/rag/ingestion/test_crawler_retry_boundary.py`) but do not pin budget semantics
against skip paths.

## Reason for Change
The crawl budget is the operator's control over how many pages a run processes; counting
no-op visits makes runs terminate unpredictably and hides reachable pages.

## Implementation Intent
Keep `visited` for loop termination and separate a persisted-page counter incremented
only where `save_http` succeeds (or at least only after a fetch returned content); apply
`max_pages` to that counter. The loop still needs a bound so failure-heavy crawls
terminate — e.g. cap total scheduled URLs at `max_pages` plus a non-persist allowance.

## Target Files or Areas
- `scripts/rag/ingestion/orchestrator.py`
- `tests/rag/ingestion/` crawler tests

## Required Changes
- Introduce a distinct persisted-page counter and gate the loop on it.
- Keep a separate scheduling bound so 304/failure/empty-content tasks cannot make the
  loop run unbounded.
- Log the distinction at loop end (scheduled vs persisted) so operators see why a crawl
  stopped.

## Constraints
- Preserve `max_depth` and `visited` dedup semantics.
- Preserve the conditional-GET (304) skip behavior itself — only accounting changes.
- Do not fetch any URL more than once per run.

## Acceptance Criteria
- A run with N cached (304) URLs and M persistable URLs with `max_pages = M` persists all
  M URLs (test with a stubbed fetch).
- A failure-only queue terminates with a bounded number of scheduled tasks (test).
- `uv run pytest tests/rag/ingestion`.

## Testing Expectations
- Unit tests with a stubbed `HttpFetcher.fetch_html`: 304-heavy queue reaches `max_pages`
  persisted pages; empty-content and language-reject paths consume the non-persist
  allowance, not the page budget.
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
If crawl docs describe `max_pages`, state that it counts persisted pages under the new
rule.

## Out of Scope
- Crawl scheduling and target-list generation.
- `CrawlOrchestrator.crawl` removal (tracked by
  `issues/20261106-073205_crawl002_remove-dead-orchestrator-crawl-method.md`).

## Dependencies
- N/A: none

## Unresolved Questions
- Preferred bound for scheduled non-persisted URLs (fixed multiplier vs. config key).
  Resolved in `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md`: fixed
  internal multiplier (`max_scheduled = 2 * max_pages`, no new config key) — config surface
  growth rejected because `config/crawler.toml` already documents its limit values as
  unvalidated heuristics, and the bound is a safety valve, not an operator tuning knob.

## AI Implementation Instruction
Keep the change inside the orchestrator loop; do not move budget logic into HttpFetcher
or CrawlPersister.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`
