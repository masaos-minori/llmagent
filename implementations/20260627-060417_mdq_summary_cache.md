## Goal

Add optional summary caching for large Markdown chunks to reduce token usage by returning summaries instead of raw content when chunks exceed configured threshold.

## Scope

**In-Scope**:
- Add chunk_summaries table with chunk_id, summary, summary_model, content_hash, created_at
- Invalidate summaries when content hash changes
- Use summary when chunk exceeds configured threshold
- Fall back to raw truncated content if summarization fails
- Make summary cache optional

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' caching behavior

## Assumptions

1. Summary threshold default = 5000 characters (configurable)
2. Summarization uses LLM API with configurable model
3. Fallback to raw truncated content when summarization fails is acceptable
4. Summary cache is optional — disabled by default unless configured

## Implementation

### Target file: config/mdq_mcp_server.toml

**Procedure**: Add summary cache configuration fields.

**Method**: Add new fields to existing config file.

**Details**:
1. Add `summary_cache_enabled = false` (disabled by default)
2. Add `summary_threshold = 5000`
3. Add `summary_model = "default"`

### Target file: scripts/mcp/mdq/models.py

**Procedure**: Add ChunkSummary model, GetChunkSummaryRequest.

**Method**: Add new BaseModel class definitions in models.py.

**Details**:
1. `GetChunkSummaryRequest`: add `use_summary: bool = False` field (after `chunk_id` field)
2. `ChunkSummary`: TypedDict with chunk_id, summary, summary_model, content_hash, created_at fields

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Add chunk_summaries table, summary caching logic, get_chunk update.

**Method**: Modify service.py to add new table and implement summary caching.

**Details**:
1. Add CREATE TABLE chunk_summaries in schema initialization:
   - `chunk_id TEXT PRIMARY KEY`
   - `summary TEXT NOT NULL`
   - `summary_model TEXT NOT NULL`
   - `content_hash TEXT NOT NULL`
   - `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
2. Update get_chunk to use summary cache:
   - Check if chunk exceeds summary_threshold (compare content length)
   - If yes, check summary_cache for existing summary with matching content_hash
   - If no cached summary, generate one using LLM API
   - Return summary + source metadata instead of raw content
3. Add summary invalidation logic:
   - Compare content_hash on each get_chunk call
   - Invalidate cached summary if hash changes
4. Add fallback to raw truncated content:
   - If summarization fails, return raw content truncated to max_chars_per_chunk

### Target file: scripts/mcp/mdq/indexer.py

**Procedure**: Add summary generation during indexing.

**Method**: Modify _index_single_file() function to generate summaries for large chunks.

**Details**:
1. During indexing, check if chunk exceeds summary_threshold
2. If yes, generate summary using LLM API
3. Store summary in chunk_summaries table with content_hash

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| service.py | Test summary cache returns cached summary | Call get_chunk for large chunk twice | Second call returns cached summary |
| service.py | Test summary invalidation | Modify file, call get_chunk again | Old summary invalidated, new summary generated |
| service.py | Test fallback on summarization failure | Simulate LLM API failure | Raw truncated content returned instead of error |
| config file | Verify optional cache is disabled by default | Check config values | summary_cache_enabled = false |

## Risks

- **Risk**: Summarization adds latency to get_chunk calls | **Likelihood**: Medium | **Mitigation**: Cache summaries aggressively; only generate on first request | False
- **Risk**: Summary quality may be insufficient for some use cases | **Likelihood**: Low | **Mitigation**: Document summary limitations; allow users to request raw content | False
