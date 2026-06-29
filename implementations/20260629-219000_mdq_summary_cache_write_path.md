## 1. Goal
- Design and implement the MDQ summary cache write path: define the summary registration flow to `chunk_summaries` table (LLM call or external API).

## 2. Scope
- **In-Scope**:
  - Add `_generate_and_cache_summary` method to `MdqService` for summary generation and cache write
  - Add logic in `get_chunk` to attempt summary generation when cache miss occurs
  - Guarantee fallback (return raw truncated content) on generation failure
  - Stub implementation for `summary_model = "default"` (external LLM not yet integrated)
- **Out-of-Scope**:
  - Actual LLM API call integration (stub while `summary_model == "default"`)
  - `chunk_summaries` table schema changes
  - Changes to existing cache read path

## 3. Requirements
### Functional
- `_generate_and_cache_summary(conn, chunk_id, content, content_hash) -> str | None` added to `MdqService`
- When `summary_model == "default"`, return `None` (stub)
- On success, save via `INSERT OR REPLACE INTO chunk_summaries`
- On exception, catch and return `None` (fallback guarantee)
- `get_chunk` calls `_generate_and_cache_summary` on cache miss (when cache enabled && threshold exceeded && no cache entry)
- If return value is `None`, return raw truncated content (existing fallback)

### Non-functional
- Summary generation should not block `get_chunk` response — use `asyncio.create_task` for background generation
- `summary_cache_enabled = false` is default; no generation unless explicitly enabled

## 4. Architecture
### Concurrency Model
- `get_chunk` is `async def`; summary generation uses `asyncio.create_task` for non-blocking background execution
- DB writes use existing SQLite connection pattern (no pooling)

### Component Boundaries
```
MdqService
  ├── _generate_and_cache_summary(conn, chunk_id, content, content_hash) -> str | None
  │     ├── summary_model == "default" → return None (stub)
  │     ├── LLM call → INSERT OR REPLACE INTO chunk_summaries
  │     └── exception → return None (fallback guarantee)
  └── get_chunk(chunk_id)
        ├── cache hit → return cached summary
        ├── cache miss && enabled && threshold exceeded → asyncio.create_task(_generate_and_cache_summary)
        └── fallback → return raw truncated content
```

## 5. Module Design
No changes to dependency direction. All changes within `service.py` and `test_mdq_summary_cache.py`.

## 6. Interface Design
### New/Modified Methods

```python
# service.py
class MdqService:
    def __init__(self, db_path: str = ..., summary_cache_enabled: bool = False, summary_model: str = "default", ...):
        self.summary_cache_enabled: bool = summary_cache_enabled  # default False
        self.summary_model: str = summary_model  # default "default"

    async def _generate_and_cache_summary(
        self, conn: sqlite3.Connection, chunk_id: str, content: str, content_hash: str
    ) -> str | None:
        """Generate a summary for the given chunk and cache it in chunk_summaries.

        Returns the generated summary on success, or None on failure/fallback.
        """
        try:
            # Stub: when summary_model is "default", no LLM integration yet
            if self.summary_model == "default":
                # TODO: Replace with actual LLM call when external LLM client is integrated
                # e.g., await llm_client.summarize(content, max_tokens=500)
                return None

            # Future: actual LLM call here
            # summary = await self._call_llm_for_summary(content)

            # Cache the generated summary
            conn.execute(
                "INSERT OR REPLACE INTO chunk_summaries (chunk_id, content_hash, summary, created_at) VALUES (?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))",
                (chunk_id, content_hash, summary),
            )
            conn.commit()
            return summary

        except Exception:
            # Fallback: do not break get_chunk on generation failure
            return None

    async def get_chunk(self, chunk_id: str) -> MCPResponse:
        # ... existing cache read path unchanged ...

        # NEW: cache miss logic — attempt background summary generation
        if (
            self.summary_cache_enabled
            and len(content) > SUMMARY_CACHE_THRESHOLD  # e.g., 500 chars
            and cached_summary is None
        ):
            # Non-blocking background generation
            asyncio.create_task(
                self._generate_and_cache_summary(conn, chunk_id, content, content_hash)
            )

        # If summary generation returned None, use existing fallback (raw truncated content)
        if summary is None:
            summary = self._truncate_to_threshold(content, threshold)

        return MCPResponse(output=summary)
```

## 7. Data Model & Serialization
No changes to data models. `chunk_summaries` table schema already exists; write path uses existing columns (`chunk_id`, `content_hash`, `summary`, `created_at`).

## 8. Error Handling & Resource Lifecycle
### Failure Modes
- Stub may be inconsistent with future LLM integration → **Mitigation**: Lock method signature, document integration point in comments
- `get_chunk` performance degradation from generation attempt overhead → **Mitigation**: Stub returns immediately `None`; actual generation runs asynchronously

### Resource Lifecycle
- No connection pooling changes; each operation opens and closes its own connection (unchanged)
- `asyncio.create_task` fires-and-forgets; task lifecycle managed by asyncio event loop

## 9. Configuration
- `summary_cache_enabled = false` is default in config; no generation unless enabled
- `summary_model = "default"` triggers stub behavior; future model names will trigger actual LLM calls

## 10. Test Strategy
### Unit Tests
- `test_generate_and_cache_summary_returns_none_for_default_model`: Mock `summary_model == "default"`, assert `_generate_and_cache_summary` returns `None`
- `test_generate_and_cache_summary_inserts_into_chunk_summaries`: Mock LLM call, assert INSERT OR REPLACE executed with correct values

### Regression Tests
- Full mdq regression: `uv run pytest tests/test_mdq_summary_cache.py -x -q`

## 11. Implementation Plan
### Phase 1: Write Method Addition
- Add `_generate_and_cache_summary(conn, chunk_id, content, content_hash) -> str | None` to `MdqService`
- Stub for `summary_model == "default"`: return `None`
- On success: `INSERT OR REPLACE INTO chunk_summaries` with `content_hash`
- Exception handling: catch and return `None` (fallback guarantee)

### Phase 2: get_chunk Integration
- Add cache miss logic in `get_chunk`: when cache enabled && threshold exceeded && no cache entry → call `_generate_and_cache_summary` via `asyncio.create_task`
- If return value is `None`, use existing fallback (raw truncated content)

### Phase 3: Test Addition
- Add `_generate_and_cache_summary` stub behavior test to `tests/test_mdq_summary_cache.py`
- Run `uv run pytest tests/test_mdq_summary_cache.py -x -q`

## 12. Risks / Open Questions
- **UNK-01**: Summary generation destination when `summary_model == "default"` — actual LLM client integration undecided → **Resolution**: Implement as stub (immediate `None` return); document future integration point in comments.
- **UNK-02**: Summary generation async approach — `get_chunk` currently includes synchronous DB calls → **Resolution**: Use `asyncio.create_task` for background generation; synchronous generation after cache save is also viable. Consider both options during implementation.
- **Risk**: Stub may be inconsistent with future LLM integration → **Mitigation**: Lock method signature, document integration point in comments.
- **Risk**: `get_chunk` performance degradation from generation attempt overhead → **Mitigation**: Stub returns immediately `None`; actual generation is async.
