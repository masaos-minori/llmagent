## Goal

Align search_docs schema with actual implementation by implementing or removing unsupported fields, and returning enough metadata to support follow-up get_chunk calls.

## Scope

**In-Scope**:
- Remove mode=hybrid (unsupported)
- Implement heading_prefix filtering
- Implement tag_filter filtering
- Update SearchResultItem fields to include chunk_id, source_path, heading_path, score, start_line, end_line, token_count, snippet

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' search behavior

## Assumptions

1. mode=bm25 should use FTS5 ranking (already implemented)
2. mode=hybrid should combine FTS5 with semantic embeddings (future work — remove for now)
3. tag_filter requires chunks.tags_json column (already exists in new schema)
4. heading_prefix filtering should filter by heading_path prefix match

## Implementation

### Target file: scripts/mcp/mdq/models.py

**Procedure**: Remove hybrid mode, update SearchResultItem fields.

**Method**: Modify BaseModel class definitions.

**Details**:
1. `SearchDocsRequest`: keep mode=bm25 and mode=grep only (remove hybrid)
2. Replace `SearchResultItem` with fields matching new schema:
   - `chunk_id: str` — chunk identifier
   - `source_path: str` — file path
   - `heading_path: str` — heading hierarchy path
   - `score: float` — FTS5 rank score
   - `start_line: int` — start line number
   - `end_line: int` — end line number
   - `token_count: int` — token count
   - `snippet: str` — content snippet (same as current content)

### Target file: scripts/mcp/mdq/search.py

**Procedure**: Implement heading_prefix and tag_filter filtering.

**Method**: Modify SQL queries in `_search_docs_structured()` function.

**Details**:
1. Add heading_prefix filtering:
   - If req.heading_prefix is set, add `AND s.heading_path LIKE ?` condition
   - Pass `f"{req.heading_prefix}%"` as parameter
2. Add tag_filter filtering:
   - If req.tag_filter is set, add `AND s.tags_json LIKE ?` condition
   - Use SQLite JSON contains or LIKE check against tags_json column
3. Update SQL query to return all metadata fields from chunks/chunks_fts tables

### Target file: scripts/mcp/mdq/tools.py

**Procedure**: Update search_docs tool definition schema.

**Method**: Modify tool definition in tools.py.

**Details**:
1. Remove mode=hybrid from mode enum in tool definition (line 32)
2. Update SearchResultItem schema to match new fields
3. Keep tag_filter and heading_prefix as optional parameters

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Update search_docs response formatting.

**Method**: Modify `search_docs()` method to use structured result.

**Details**:
1. Format search results with new metadata fields
2. Include chunk_id, source_path, heading_path, score for each result

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| search.py | Test heading_prefix filter | curl with heading_prefix parameter | Only results matching prefix returned |
| search.py | Test tag_filter | curl with tag_filter parameter | Only results with matching tags returned |
| models.py | Verify SearchResultItem has all metadata fields | Check field definitions | chunk_id, source_path, heading_path, score present |
| tools.py | Verify mode=hybrid removed from schema | Check tool definition | Only bm25/grep modes available |

## Risks

- **Risk**: Breaking changes to consumers expecting old SearchResultItem fields | **Likelihood**: Medium | **Mitigation**: Document breaking changes; consider backward-compatible field names | False
- **Risk**: tag_filter JSON contains check is slow on large datasets | **Likelihood**: Low | **Mitigation**: Use FTS5 index for tag filtering if performance becomes an issue | False
