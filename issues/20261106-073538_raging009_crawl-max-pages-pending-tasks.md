# max_pages budget is consumed by URLs that are never persisted

## Priority
Medium

## Summary
`CrawlOrchestrator.crawl_site` caps the crawl with `len(visited) >= max_pages`, and
`visited` is populated for every URL scheduled for a fetch task — including URLs that
then return HTTP 304, produce no content, are rejected by the language check, or fail
during fetch. A crawl capped at `max_pages` can therefore stop before persisting that
many pages, with the remaining queued URLs dropped.

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
