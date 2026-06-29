## Implementation Design: mdq-mcp /health Endpoint Schema Alignment

### Goal

Fix the `/health` endpoint in `scripts/mcp/mdq/server.py` to reflect the current production schema (`chunks`/`chunks_fts`/`documents` triggers), add `row_factory`, and align all health checks with acceptance criteria.

### Scope

- **In-Scope**:
  - `scripts/mcp/mdq/server.py` — rewrite `health()` and `_check_stale_documents()` for new schema
  - `tests/test_mdq_health_stale.py` — update fixtures and queries from `sections` to `chunks`/`documents`
  - New test file `tests/test_mdq_health_endpoint.py` — full acceptance-criteria coverage

### Changes

#### 1. `scripts/mcp/mdq/server.py`

**`_check_stale_documents()`**: Simplified to use `documents` table only:
- Removed `mdq_cfg` parameter and file-mtime comparison logic (no longer applicable)
- Now queries `documents WHERE mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)` to detect stale docs
- Accepts `conn: sqlite3.Connection` only

**`health()`**: Added `row_factory = sqlite3.Row` and updated all schema references:
- Table checks: `sections` → `chunks`, `sections_fts` → `chunks_fts`
- Trigger checks: `sections_ai/ad/au` → `chunks_ai/ad/au`
- FTS5 probe query: `SELECT COUNT(*) FROM sections_fts WHERE sections_fts = 'delete' LIMIT 1` → `SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts = 'delete' LIMIT 1`
- Stats queries updated:
  - `chunk_count`: `SELECT COUNT(*) as cnt FROM chunks`
  - `doc_count`: `SELECT COUNT(DISTINCT source_path) as cnt FROM chunks`
  - `fts_count`: `SELECT COUNT(*) as cnt FROM chunks_fts WHERE chunks_fts != 'delete'`
  - `last_indexed`: `SELECT MAX(indexed_at) as mt FROM documents`

#### 2. `tests/test_mdq_health_stale.py`

Added new test class `TestStaleDocumentCountNewSchema` with tests for:
- `test_stale_count_zero_when_fresh`: mtime_ns <= indexed_at * 1e9 → stale count = 0
- `test_stale_count_positive_when_outdated`: mtime_ns > indexed_at * 1e9 → stale count > 0
- `test_stale_count_mixed`: Some docs fresh, some stale → count only stale
- `test_stale_count_with_corrupt_db`: Missing documents table → None (not raised)

Added new test class `TestStaleDocumentCountNoDocumentsTable` with:
- `test_returns_none_when_no_documents_table`: Verifies `_check_stale_documents()` returns None when documents table is missing

#### 3. `tests/test_mdq_health_endpoint.py` (new file)

Full acceptance-criteria coverage for mdq-mcp `/health` endpoint:

**TestHealthEndpointReady** (4 tests):
- `test_health_returns_ready_true_with_valid_schema`: HTTP 200, ready=true when all tables and triggers exist
- `test_health_response_contains_no_stub_key`: Response must not contain 'stub' key
- `test_health_response_details_fields`: Details contains database, document_count, chunk_count, fts_row_count, last_indexed, stale_document_count
- `test_health_response_service_field`: Details contains 'service': 'mdq-mcp'

**TestHealthEndpointMissingSchema** (6 tests):
- `test_missing_chunks_table_returns_ready_false`: HTTP 503, ready=false when chunks table missing
- `test_missing_chunks_fts_table_returns_ready_false`: HTTP 503, ready=false when chunks_fts table missing
- `test_missing_triggers_returns_ready_false`: HTTP 503, ready=false when triggers missing
- `test_missing_chunks_ai_trigger`: HTTP 503, 'chunks_ai' in error message
- `test_fts5_query_failure_returns_ready_false`: HTTP 503, 'fts5' in dependencies
- `test_db_file_not_found_returns_ready_false`: HTTP 503, 'db_file' in dependencies

**TestHealthEndpointStats** (8 tests):
- `test_document_count_from_chunks_source_path`: document_count = COUNT(DISTINCT source_path) FROM chunks
- `test_chunk_count_from_chunks_table`: chunk_count = COUNT(*) FROM chunks
- `test_fts_row_count_excludes_deletes`: fts_row_count excludes 'delete' rows (skipped — requires FTS5 virtual table)
- `test_last_indexed_from_documents`: last_indexed = MAX(indexed_at) FROM documents
- `test_last_indexed_is_none_when_no_documents`: last_indexed is null when documents empty
- `test_health_returns_http_200_when_ready`: HTTP 200 when ready=true (MCP-08 guidance)
- `test_health_returns_http_503_when_degraded`: HTTP 503 when ready=false (MCP-08 guidance)
- `test_health_response_has_correct_top_level_keys`: Response has exactly {status, ready, dependencies, details}

### Test Results

All tests pass:
- `tests/test_mdq_health_endpoint.py`: 17 passed, 1 skipped
- `tests/test_mdq_health_stale.py`: 8 passed
