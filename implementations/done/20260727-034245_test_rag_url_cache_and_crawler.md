## Goal

Add guard tests for RAG layer URL cache fallback and E2E integration to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Create `tests/test_rag_url_cache.py`:
  - Config failure returns empty string cache
  - Cache reuse on hit
- Create `tests/test_crawler_integration.py` (respx-based):
  - HTTP retry on transient failures
  - 304 response skipping content fetch
  - max_pages boundary condition
  - BFS queue ordering
  - Link filtering
- Create `tests/integration/test_ingestion_e2e.py`:
  - Full ingestion pipeline from URL to processed document
  - Real SQLite in-memory database

**Out-of-Scope:**
- Changing the behavior of RAG or crawler modules
- Any changes beyond the tests

## Assumptions

1. The RAG layer needs characterization tests due to multiple coverage gaps
2. Tests must use respx for HTTP mocking where applicable
3. Tests should verify current behavior, not expected future behavior

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for RAG edge cases | Search for `rag` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_rag_url_cache.py`
  - New file: `tests/test_crawler_integration.py`
  - New file: `tests/integration/test_ingestion_e2e.py`

- **Blast Radius:**
  - Test-only change — no production code affected

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the RAG layer:
```python
# Key behaviors:
# - URL cache: stores fetched URLs, returns empty string on config failure
# - Crawler: HTTP retry, 304 handling, BFS traversal, link filtering
# - Ingestion pipeline: URL -> crawl -> parse -> chunk -> store
```

The tests will verify URL cache behavior, crawler integration, and end-to-end ingestion.

## Implementation

### Target files
- New file: `tests/test_rag_url_cache.py`
- New file: `tests/test_crawler_integration.py`
- New file: `tests/integration/test_ingestion_e2e.py`

### Procedure
1. Create `tests/integration/` directory if it doesn't exist
2. Create all three test files
3. Write tests for each module
4. Save the files

### Method
Create characterization tests using respx for HTTP mocking and real components where possible.

### Details
1. Create `tests/test_rag_url_cache.py`:
   ```python
   """Characterization tests for RAG URL cache."""
   
   @pytest.mark.asyncio
   async def test_config_failure_returns_empty_string():
       ...
   
   @pytest.mark.asyncio
   async def test_cache_reuse_on_hit():
       ...
   ```

2. Create `tests/test_crawler_integration.py`:
   ```python
   """Integration tests for WebCrawler with respx."""
   
   import respx
   
   @pytest.mark.asyncio
   async def test_http_retry_on_transient_failure(respx_mock):
       ...
   
   @pytest.mark.asyncio
   async def test_304_response_skips_content_fetch(respx_mock):
       ...
   
   @pytest.mark.asyncio
   async def test_max_pages_boundary_condition(respx_mock):
       ...
   
   @pytest.mark.asyncio
   async def test_bfs_queue_ordering(respx_mock):
       ...
   
   @pytest.mark.asyncio
   async def test_link_filtering(respx_mock):
       ...
   ```

3. Create `tests/integration/test_ingestion_e2e.py`:
   ```python
   """E2E integration tests for ingestion pipeline."""
   
   @pytest.mark.asyncio
   async def test_full_ingestion_pipeline():
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

N/A — this test documents current behavior

## Rollback considerations

- Simple revert: delete the test files

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_rag_url_cache.py` | Characterization tests document current behavior | `uv run pytest -k "rag" -v` | All tests pass |
| `tests/test_crawler_integration.py` | Integration tests document current behavior | `uv run pytest -k "crawler" -v` | All tests pass |
| `tests/integration/test_ingestion_e2e.py` | E2E integration tests document current behavior | `uv run pytest -k "ingestion" -v` | All tests pass |

## Out of scope

- Changing the behavior of RAG or crawler modules
- Any changes beyond the tests

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-130639_require.md
- Source plan: plans/20260726-172757_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/rag/llm_client.py, scripts/rag/ingestion/crawler.py, tests/integration/
