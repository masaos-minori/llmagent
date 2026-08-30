## Goal

Isolate cache management logic from `ingester.py` into `scripts/rag/ingestion/cache_invalidation.py`, creating `CacheInvalidator` as the single source of truth for stale cache entry cleanup.

## Scope

- Create `scripts/rag/ingestion/cache_invalidation.py` with `CacheInvalidator` class
- Move `_write_error_metadata` method to `CacheInvalidator.invalidate()`
- Update imports in `ingester.py` to use `CacheInvalidator`
- Write tests in `tests/test_ingester_cache_invalidation.py`

## Assumptions

- `read_chunk_json` is called internally by `CacheInvalidator`
- `ChunkFormatError` exception is caught and handled within `CacheInvalidator`
- HTTP client (`httpx.Client`) is passed via dependency injection rather than owned by `CacheInvalidator`
- `orjson.dumps` is used for error metadata serialization (same as current implementation)
- `datetime.datetime.now(datetime.UTC)` is used for timestamps (same as current implementation)

## Design decisions

- `CacheInvalidator` owns the cache invalidation logic — it sends HTTP POST to the RAG pipeline service URL to invalidate stale entries
- `invalidate()` accepts the RAG pipeline service URL and HTTP client — same contract as current inline cache invalidation
- `write_error_metadata()` returns `dict | None` — same contract as current `_write_error_metadata`
- Cache invalidation is only triggered when at least one URL group succeeded

## Alternatives considered

- **Singleton cache invalidator**: Would reduce HTTP client duplication but couples callers to global state. Rejected — dependency injection is preferred.
- **Async cache invalidation**: Would improve throughput but changes the public contract. Deferred to a later refactor.
- **Separate CacheInvalidator and MetadataWriter**: Would isolate cache HTTP calls from metadata writing but adds unnecessary abstraction layer. Rejected — both are cache-related concerns.

## Implementation

### Target file

`scripts/rag/ingestion/cache_invalidation.py`

### Procedure

1. Create `scripts/rag/ingestion/cache_invalidation.py` with the `CacheInvalidator` class definition
2. Copy the inline cache invalidation block from `ingest_all()` into `CacheInvalidator.invalidate(rag_pipeline_service_url: str, http_client: httpx.Client) -> None`
3. Copy `_write_error_metadata` method body into `CacheInvalidator.write_error_metadata(path: Path, failure_reason: str) -> dict | None`
4. Preserve `self._client.post(self._rag_pipeline_service_url + "/rag_invalidate_cache")` call
5. Preserve `resp.raise_for_status()` call
6. Preserve `httpx.HTTPError` exception handling
7. Preserve `ChunkFormatError` exception handling in `write_error_metadata`
8. Preserve `orjson.dumps()` call for error metadata serialization
9. Preserve `datetime.datetime.now(datetime.UTC).isoformat()` timestamp generation
10. Update `ingester.py` import: replace inline method with `CacheInvalidator` instantiation
11. Replace all `self._write_error_metadata(...)` calls with `self.cache_invalidator.write_error_metadata(...)`
12. Replace inline cache invalidation block with `self.cache_invalidator.invalidate(...)`
13. Remove `_write_error_metadata` method from `RagIngester`
14. Remove unused imports: `httpx` (if no longer referenced after removal), `orjson`, `datetime` (if no longer referenced after removal)

### Method

```python
class CacheInvalidator:
    def __init__(
        self,
        http_client: httpx.Client,
    ) -> None: ...

    def invalidate(
        self,
        rag_pipeline_service_url: str,
        has_success: bool,
    ) -> None:
        """Invalidate RAG pipeline semantic cache after ingestion (only when at least one URL group succeeded)."""
        # Copy inline cache invalidation block from RagIngester.ingest_all verbatim

    def write_error_metadata(
        self, path: Path, failure_reason: str
    ) -> dict | None:
        """Write .error.json metadata for a failed chunk."""
        # Copy body of RagIngester._write_error_metadata verbatim
```

### Details

- `ChunkDocument` is imported from `rag.models_data` (unchanged)
- `ChunkFormatError` is imported from `rag.exceptions` (unchanged)
- `read_chunk_json` is imported from `rag.ingestion.pipeline_utils` (unchanged)
- `httpx` is imported from `httpx` (unchanged)
- `orjson` is imported from `orjson` (unchanged)
- `datetime` is imported from `datetime` (unchanged)
- `logging` uses the same `logger` instance from `shared.logger.Logger(__name__, ...)`
- `extra={"url": chunk_url, "source_type": "file", "stage_name": "ingester"}` — preserved in logging calls
- `"embedding" in reason.lower()` — preserved for retry vs failed directory decision
- `self._client.post(self._rag_pipeline_service_url + "/rag_invalidate_cache")` — preserved
- `resp.raise_for_status()` — preserved
- `httpx.HTTPError` — preserved in except clause
- `error_path.write_bytes(orjson.dumps(error_metadata))` — preserved
- `metadata["timestamp"] = datetime.datetime.now(datetime.UTC).isoformat()` — preserved

## Compatibility considerations

- Public API: `RagIngester.__init__` signature changes — callers must now pass a `CacheInvalidator` instance instead of raw config dict
- Backward compatibility: `RagIngester` constructor should accept both `config: dict | None` (legacy) and `cache_invalidator: CacheInvalidator` (new) with deprecation warning for legacy mode
- HTTP client lifecycle stays with `RagIngester` (owns the client, passes it to services)
- `RAG_PIPELINE_SERVICE_URL` is injected via constructor (allows test mocking)

## Security considerations

- No new secrets or credentials introduced
- Cache invalidation HTTP POST uses existing HTTP client (no new connection pool)
- Error metadata writes use safe JSON serialization (no code execution risk)
- Error messages do not leak sensitive data (only path names and first 60 chars of content)

## Rollback considerations

- Revert: restore `_write_error_metadata` method in `RagIngester`
- Revert: remove `CacheInvalidator` class from `cache_invalidation.py`
- Revert: restore original imports in `ingester.py`
- Revert: restore original `RagIngester.__init__` parameter
- Safe rollback: no database schema changes, no file system changes during refactoring

## Validation plan

1. Run `uv run pytest tests/test_ingester_cache_invalidation.py -v`
2. Verify `ingester.py` line count reduced by ~20 lines
3. Verify no import errors: `python -c "from rag.ingestion import ingester"`
4. Verify cyclomatic complexity of `ingest_all` and `ingest_url_group` unchanged (still high — Phase 8 will reduce)
5. Mutation testing: `uv run mutmut run --paths-to-mutate=scripts/rag/ingestion/cache_invalidation.py`

## Completion criteria

- [ ] `CacheInvalidator` class exists in `scripts/rag/ingestion/cache_invalidation.py`
- [ ] `invalidate()` method preserves HTTP POST to `/rag_invalidate_cache` endpoint
- [ ] `write_error_metadata()` method returns `dict | None` matching original contract
- [ ] All httpx.post() calls preserved identically
- [ ] All resp.raise_for_status() calls preserved identically
- [ ] All orjson.dumps() calls preserved identically
- [ ] All datetime.timestamp() calls preserved identically
- [ ] All logging calls preserved with identical `extra=` parameters
- [ ] `RagIngester` delegates to `CacheInvalidator` for all cache operations
- [ ] Tests pass: `uv run pytest tests/test_ingester_cache_invalidation.py -v`
- [ ] No import errors across the project
- [ ] `ingester.py` line count reduced by at least 20 lines

## Out of scope

- Moving `ChunkDocument` DTO to this module (stays in `rag.models_data`)
- Moving `ChunkFormatError` to this module (stays in `rag.exceptions`)
- Adding cache TTL configuration (deferred)
- Implementing distributed cache invalidation (deferred)
- Changing cache invalidation strategy (e.g., selective invalidation) (deferred)
- Adding progress callbacks for long-running batches (deferred)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement CacheInvalidator class in scripts/rag/ingestion/cache_invalidation.py | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-008 — Extract cache invalidation module
- **Source issue**: [refactor] Separate ingester.py into multiple modules by concern (3/3)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-181706_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260830-093541
- **Related target files**: scripts/rag/ingestion/cache_invalidation.py
