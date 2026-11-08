# A 304 or failed fetch of one page stops link discovery for its whole subtree

## Priority
High

## Summary
`_process_crawl_url_async` returns as soon as `fetch_html` returns `None`, before it enqueues the page links, and `fetch_html` returns `None` for both HTTP 304 and retry exhaustion, so on a re-crawl an unchanged index page ends the crawl after one page.

## Background
Review finding F-005. Evidence (Explicit in code): in `scripts/rag/ingestion/orchestrator.py`, `if result is None: return` precedes the call `self._link_discovery.enqueue_links(html, url, start_url, depth, queue)`; `scripts/rag/ingestion/http_fetcher.py` `fetch_html` documents "None on 304 or retry exhaustion". `get_conditional_headers` sends `If-None-Match`/`If-Modified-Since` for pages already stored, so the start page answers 304 on the second crawl.

## Problem
Pages added or changed deeper in a site are never discovered after the first crawl whenever an ancestor page is unchanged, and a transient fetch failure of an index page hides its subtree for that run.

## Reason for Change
Incremental crawling is the normal operating mode, so the discovery loss affects every site that supports conditional requests.

## Implementation Intent
Distinguish "not modified" from "failed" in the fetch result, and for a not-modified page still discover links from the stored content (or a stored link list) so the traversal continues.

## Target Files or Areas
- `scripts/rag/ingestion/orchestrator.py` (`_process_crawl_url_async`)
- `scripts/rag/ingestion/http_fetcher.py` (`fetch_html`)
- `scripts/rag/ingestion/link_discovery.py`
- `tests/rag/ingestion/`

## Required Changes
- Return a typed result that separates not-modified, failed and fetched.
- On not-modified, enqueue links from the stored page content.
- Add a crawl test with a start page that answers 304 and a changed child page.

## Constraints
- Do not re-persist unchanged documents.
- Respect the page budget and robots policy during link discovery.

## Acceptance Criteria
- A second crawl whose start page answers 304 still reaches and ingests a changed child page.
- A failed fetch is reported distinctly from a 304.
- Budget and depth limits still apply.

## Testing Expectations
- Async orchestrator test with a mock transport (304 for the start page, 200 for a new child).
- ruff and mypy on touched files.

## Documentation Impact
Update the crawl description if it says unchanged pages are skipped entirely.

## Out of Scope
- Redirect handling (see the redirect issue in the same batch).
- robots.txt policy.

## Dependencies
Related, no required order: `issues/20261108-131127_ragrev012_crawler-redirect-trust-boundary.md` (same fetch path).

## Unresolved Questions
Where the stored page content or link list should come from for a 304 page (the saved `rag-src` file versus a stored link table) is `Needs confirmation`.

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131125
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`, `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/link_discovery.py`, `tests/rag/ingestion/`
