**Status: IMPLEMENTED**

## Goal

Enforce result size limits for MDQ tools to prevent unbounded MCP responses. Add configurable limits and truncation markers for all MDQ tools (search_docs, get_chunk, outline, grep_docs).

## Scope

**In-Scope**:
- Add configurable limits: max_results_limit, max_chars_per_chunk, max_total_result_chars, max_outline_items, max_grep_matches
- Apply limits to search_docs, get_chunk, outline, grep_docs
- Mark truncated output with clear indicators and original size
- Suggest narrowing query or using get_chunk when truncated

**Out-of-Scope**:
- Adding new tools or features
- MCP-level truncation (this is server-side before MCP truncation)

## Assumptions

1. Limits are configurable via config/mdq_mcp_server.toml
2. Empty allowlist = fail-closed for path authorization (already implemented in auth.py)
3. Truncated output should include: truncation indicator, original size, suggestion to narrow query

## Implementation

### Target file: config/mdq_mcp_server.toml

**Procedure**: Add limit configuration keys.

**Method**: Append new TOML entries to the existing config.

**Details**:
1. Add `max_results_limit = 100` (replaces max_search_results)
2. Add `max_chars_per_chunk = 10000` (replaces max_chunk_chars)
3. Add `max_total_result_chars = 100000`
4. Add `max_outline_items = 500`
5. Add `max_grep_matches = 200`

### Target file: models.py

**Procedure**: Add limit request fields to existing request models.

**Method**: Modify TypedDict and BaseModel class definitions.

**Details**:
1. `SearchDocsRequest`: add `max_results_limit: int | None = None` and `max_total_result_chars: int | None = None`
2. `GetChunkRequest`: add `max_chars_per_chunk: int | None = None`
3. `OutlineRequest`: add `max_outline_items: int | None = None`
4. `GrepDocsRequest`: add `max_grep_matches: int | None = None`

### Target file: tools.py

**Procedure**: Add limit parameters to tool definitions.

**Method**: Modify tool parameter definitions in inputSchema properties.

**Details**:
1. `search_docs` tool: add `max_results_limit` and `max_total_result_chars` properties (type: integer, optional)
2. `get_chunk` tool: add `max_chars_per_chunk` property (type: integer, optional)
3. `outline` tool: add `max_outline_items` property (type: integer, optional)
4. `grep_docs` tool: add `max_grep_matches` property (type: integer, optional)

### Target file: service.py

**Procedure**: Apply limits in search_docs, get_chunk, outline, grep_docs methods with truncation markers.

**Method**: Add limit enforcement logic after query execution, before response construction.

**Details**:
1. `search_docs()`: 
   - Clamp results by `max_results_limit` (default: config value)
   - Truncate total chars if exceeds `max_total_result_chars`, mark truncation with "[Truncated — X of Y items returned]"
2. `get_chunk()`: 
   - Truncate chunk content if exceeds `max_chars_per_chunk`, mark truncation with "[Truncated — X/Y chars]"
3. `outline()`: 
   - Cap items at `max_outline_items`, mark truncation with "[Truncated — X of Y headings]"
4. `grep_docs()`: 
   - Cap matches at `max_grep_matches`, mark truncation with "[Truncated — X of Y matches]"

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| search_docs | Test with large result set | curl with query returning >100 results | Only 100 results returned, truncated marker present |
| get_chunk | Test with large chunk | curl with query for large chunk | Chunk truncated if >10000 chars, truncated marker present |
| outline | Test with large outline | curl with query for large outline | Only 500 items returned, truncated marker present |
| grep_docs | Test with many matches | curl with query returning >200 matches | Only 200 matches returned, truncated marker present |

## Risks

- **Risk**: Truncation breaks existing consumers expecting full results | **Likelihood**: Medium | **Mitigation**: Document truncation behavior clearly; include original size in response | False
- **Risk**: Default limits too low for production use | **Likelihood**: Low | **Mitigation**: Use reasonable defaults that can be overridden via config | False
