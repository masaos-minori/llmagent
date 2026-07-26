## Goal

Create `tests/test_crawler_retry_boundary.py` with four test methods covering previously untested critical code paths: HTTP retry (503→200), 304 skip, max_pages boundary, and BFS queue / external link filtering.

## Scope

**In-Scope:**
- Create new test file `tests/test_crawler_retry_boundary.py`
- Add 4 test methods using respx-based mocking:
  1. `test_retry_on_503_then_succeeds` — verify retry behavior
  2. `test_skip_304_response` — verify 304 handling
  3. `test_max_pages_boundary` — verify exact stop at limit
  4. `test_external_link_filter` — verify external link filtering

**Out-of-Scope:**
- Modifying existing crawler or ingestion tests
- Adding integration/E2E tests beyond unit-level respx mocks

## Assumptions

1. WebCrawler accepts a `config` dict in its constructor to override default values
2. respx.mock() can intercept httpx.AsyncClient requests made by the crawler
3. The crawler's public interface includes a method that triggers the crawl loop (e.g., `crawl()`)

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | What is the public API entry point for triggering a crawl (crawl(), crawl_file(), etc.) | Read WebCrawler class public interface | False |
| UNK-02 | Whether the crawler uses asyncio concurrency that complicates testing | Check _concurrency config usage | False |
| UNK-03 | How to set up a minimal test URL that the crawler will accept | Check parse_target_urls() logic | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `tests/test_crawler_retry_boundary.py` — new file to be created (4 test methods)
  - `scripts/rag/ingestion/crawler.py` — reference for understanding production code paths

- **Blast Radius:**
  - Very low churn — new file creation only
  - Very low risk since change is purely additive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `crawler.py`:
```python
# WebCrawler public interface:
class WebCrawler:
    def __init__(self, config: dict | None = None) -> None: ...
    async def crawl(self, targets: list[tuple[str, str]] | None = None) -> None: ...
    async def crawl_site(self, start_url: str, hint_lang: str) -> None: ...
    def crawl_file(self, path: Path, lang: str) -> int: ...

# Key config keys:
#   - "max_pages" (default: 500)
#   - "skip_external" (default: True)
#   - "fetch_retry" (number of retries)
#   - "fetch_timeout" (timeout in seconds)
```

Test structure:
```python
import pytest
import respx
from scripts.rag.ingestion.crawler import WebCrawler

@pytest.mark.asyncio
async def test_retry_on_503_then_succeeds(tmp_path: Path) -> None:
    # Mock 503 then 200 response
    # Verify crawler eventually succeeds after retry

@pytest.mark.asyncio
async def test_skip_304_response(tmp_path: Path) -> None:
    # Mock 304 response
    # Verify URL added to crawled set without content fetch

@pytest.mark.asyncio
async def test_max_pages_boundary(tmp_path: Path) -> None:
    # Set config["max_pages"] = 1
    # Verify exactly one page crawled

@pytest.mark.asyncio
async def test_external_link_filter(tmp_path: Path) -> None:
    # Set config["skip_external"] = True
    # Verify external links filtered from BFS queue
```

## Implementation

### Target file
`tests/test_crawler_retry_boundary.py` (new file)

### Procedure
1. Create `tests/test_crawler_retry_boundary.py`
2. Add imports for pytest, respx, httpx, asyncio, WebCrawler
3. Implement `test_retry_on_503_then_succeeds` using respx.route().mock(side_effect=[Response(status_code=503), Response(status_code=200)])
4. Implement `test_skip_304_response` — mock 304 response, verify URL added to crawled set without content fetch
5. Implement `test_max_pages_boundary` — set config["max_pages"] = 1, verify exactly one page crawled
6. Implement `test_external_link_filter` — set config["skip_external"] = True, verify external links filtered
7. Save the file

### Method
Create new test file with respx-based mocking for each scenario.

### Details
- Use `@pytest.mark.asyncio` decorator for async tests
- Use `respx.mock()` context manager to intercept httpx requests
- Configure WebCrawler with temp directory via `config={"rag_src_dir": str(tmp_path)}`
- For retry test: use `respx.route().mock(side_effect=[Response(status_code=503), Response(status_code=200)])`
- For 304 test: mock 304 response and verify no content fetch occurred
- For max_pages test: set `config["max_pages"] = 1`, verify exactly one page processed
- For external filter test: set `config["skip_external"] = True`, verify external links excluded from BFS queue

## Compatibility considerations

N/A — new test file has no runtime effect

## Security considerations

N/A

## Rollback considerations

- Simple revert: delete the new test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_crawler_retry_boundary.py` | All 4 tests pass individually | `uv run pytest tests/test_crawler_retry_boundary.py -v` | All 4 tests pass |

## Out of scope

- Modifying existing crawler or ingestion tests
- Adding integration/E2E tests beyond unit-level respx mocks

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-163423_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-031450
- Related target files: rag/ingestion/crawler.py, tests/test_crawler_retry_boundary.py
