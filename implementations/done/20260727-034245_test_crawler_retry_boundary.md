## Goal

Add guard tests for crawler.py before refactoring to establish behavioral baseline for async retry, BFS traversal, and URL filtering logic.

## Scope

**In-Scope:**
- Create `tests/test_crawler_retry_boundary.py` with tests for:
  - Async retry: transient failures trigger retries up to max attempts
  - BFS traversal: URLs discovered and visited breadth-first
  - URL filtering: filtered URLs excluded from crawling
  - Depth limits: crawling stops at configured depth

**Out-of-Scope:**
- Changing the behavior of WebCrawler itself
- Any changes beyond the test

## Assumptions

1. The crawler needs characterization tests since it has zero effective coverage
2. Tests should use respx for HTTP mocking
3. Tests should verify current behavior, not expected future behavior

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for crawler retry behavior | Search for `crawler` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_crawler_retry_boundary.py`

- **Blast Radius:**
  - Test-only change — no production code affected

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `crawler.py`:
```python
# crawl(): iterates over targets, calls crawl_file() for file:// URLs or crawl_site() for HTTP URLs
# crawl_site(): BFS crawl using asyncio.Queue + asyncio.Semaphore + FIRST_COMPLETED loop
# _drain_queue_to_tasks(): dequeues URLs, checks visited/deepth, creates fetch tasks
```

The test will verify BFS traversal order, retry on transient failures, URL filtering, and depth limits.

## Implementation

### Target file
New file: `tests/test_crawler_retry_boundary.py`

### Procedure
1. Create new test file `tests/test_crawler_retry_boundary.py`
2. Write tests for async retry behavior
3. Write tests for BFS traversal order
4. Write tests for URL filtering
5. Write tests for depth limits
6. Save the file

### Method
Create characterization tests using respx for HTTP mocking.

### Details
1. Create `tests/test_crawler_retry_boundary.py`:
   ```python
   """Characterization tests for WebCrawler."""
   
   import asyncio
   import pytest
   import respx
   from unittest.mock import patch
   
   @pytest.mark.asyncio
   async def test_crawl_retry_on_transient_failure():
       """Transient HTTP errors should trigger retries."""
       ...
   
   @pytest.mark.asyncio
   async def test_crawl_bfs_traversal_order():
       """URLs should be visited breadth-first."""
       ...
   
   @pytest.mark.asyncio
   async def test_crawl_excludes_filtered_urls():
       """Filtered URLs should not be crawled."""
       ...
   
   @pytest.mark.asyncio
   async def test_crawl_stops_at_max_depth():
       """Crawling should stop at configured depth limit."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

N/A — this test documents current behavior

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_crawler_retry_boundary.py` | Characterization tests document current behavior | `uv run pytest -k "crawler" -v` | All tests pass |

## Out of scope

- Changing the behavior of WebCrawler itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-125926_require.md
- Source plan: plans/20260726-172403_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/rag/ingestion/crawler.py, tests/test_crawler_retry_boundary.py
