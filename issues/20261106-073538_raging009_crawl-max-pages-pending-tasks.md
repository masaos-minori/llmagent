# Count crawl max_pages only for actual page fetches

## Priority
Medium

## Summary
`CrawlOrchestrator.crawl` decrements its page budget for every dequeued task, including
tasks that end in HTTP 304, 404/403, network failure, or re-queue — none of which fetch
and persist a page. A crawl capped at `max_pages` can therefore stop before crawling
that many pages, and a re-queued task consumes the budget twice.

## Problem
In `scripts/rag/ingestion/orchestrator.py`:
- The guard is `if pages_fetched >= max_pages: break` at dequeue time, and the code
  comments state this "correctly counts only actually-fetched pages" — the implementation
  does not match the comment: `pages_fetched += 1` runs before any fetch decision.
- The 304 skip path (`fetch_html` returns None), the 404/403 path, the fetch-exception
  path, and the re-queue path all `continue` after the increment, so skipped and failed
  pages consume budget slots.
- Re-queued tasks (added back to the queue) will increment the counter a second time on
  their later dequeue.
- Consequence: with many cached (304) URLs mixed into the queue, the crawl reports
  `pages_crawled` well below `max_pages` and never visits the remaining queued URLs.

## Background
The orchestrator was extracted from WebCrawler to separate BFS queue/semaphore
orchestration; the dequeue-time counter was carried over from the earlier implementation.
Tests cover semaphore behavior (`tests/rag/ingestion/test_crawler_retry_boundary.py` area)
but do not pin the budget semantics against skip paths.

## Reason for Change
The crawl budget is the operator's control over how many pages a run processes; counting
no-op dequeues makes runs terminate unpredictably and hides reachable pages.

## Implementation Intent
Decouple loop iterations from page accounting: keep a separate guard against unbounded
loops (e.g., a processed-task cap), and increment `pages_fetched` only when a fetch
produces content that proceeds to persistence (the current `persist_page` path).

## Target Files or Areas
- `scripts/rag/ingestion/orchestrator.py`
- `tests/rag/ingestion/` crawler tests

## Required Changes
- Move the `pages_fetched` increment to the point where a page is actually fetched and
  processed (or at least fetched with content).
- Keep a separate termination guard so 304/404/exception tasks cannot make the loop run
  forever (e.g., cap total dequeued tasks at a multiple of `max_pages`).
- Ensure re-queued tasks do not double-count against the fetch budget.

## Constraints
- Preserve the existing `max_depth` and `visited` semantics.
- Preserve the conditional-GET (304) skip behavior itself — only the accounting changes.
- Keep the `CrawlStats.pages_crawled` meaning consistent with the new counting rule.

## Acceptance Criteria
- A run with N cached (304) URLs and M uncached URLs and `max_pages = M` crawls all M
  uncached URLs (test).
- A run where all fetches fail terminates without exceeding a bounded number of
  iterations (test).
- Re-queued tasks do not consume extra fetch budget.

## Testing Expectations
- Unit tests with a stubbed `fetch_html` covering: 304-heavy queue reaches `max_pages`
  real fetches; failure-only queue terminates; re-queue counts once.
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
If crawl docs describe `max_pages`, state that it counts fetched pages, not queue
iterations.

## Out of Scope
- Crawl scheduling and target-list generation.

## Dependencies
- N/A: none

## Unresolved Questions
- Preferred bound for total dequeued tasks when fetches keep failing (fixed multiplier vs.
  config key).

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
