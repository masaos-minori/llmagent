## Goal

Implement production-safe grep_docs with path filtering, result limits, regex safety, and structured chunk ID responses.

## Scope

**In-Scope**:
- Apply `paths` filtering to limit search scope
- Add `max_matches` parameter to cap result count
- Add `max_chars_per_match` parameter for content truncation
- Add optional context line controls (before/after matching lines)
- Return chunk IDs with matches using structured response model
- Prevent unbounded regex scans with timeout/length limits
- Handle invalid regex patterns as tool-level errors

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' grep behavior

## Assumptions

1. max_matches default = 200 (reasonable for production use)
2. max_chars_per_match default = 500 (truncate content to prevent unbounded output)
3. Context line controls: context_before=2, context_after=2 lines around match
4. Regex timeout = 1 second to prevent catastrophic backtracking
5. Invalid regex returns tool error, not plain text response

## Implementation

### Target file: scripts/mcp/mdq/models.py

**Procedure**: Update GrepDocRequest with new fields, update GrepDocMatch with chunk_id and metadata fields.

**Method**: Modify BaseModel class definitions in models.py.

**Details**:
1. `GrepDocsRequest`: add `max_matches: int = 200`, `max_chars_per_match: int = 500`, `context_before: int = 2`, `context_after: int = 2` fields (after `pattern` field)
2. Replace `GrepDocMatch` with structured response model:
   - `chunk_id: str` — chunk identifier (changed from int to str)
   - `source_path: str` — file path
   - `heading_path: str` — heading hierarchy path
   - `match_text: str` — the matched text snippet
   - `line_number: int` — line number where match was found

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Implement path filtering, result limits, regex safety, structured response.

**Method**: Replace grep_docs() method with new implementation using chunks/chunks_fts tables and new request/response models.

**Details**:
1. Add path filtering:
   - If req.paths is set, add WHERE clause for source_path IN (...)
   - Use LIKE prefix matching for path_prefix filtering if needed
2. Add result limits:
   - Cap matches at max_matches count (default 200)
   - Truncate content to max_chars_per_match characters (default 500)
   - Extract context lines around match position using context_before/context_after
3. Implement regex safety:
   - Add timeout decorator or threading-based timeout for regex search
   - Return tool error if regex takes longer than timeout (1 second)
4. Handle invalid regex as tool error:
   - Catch re.error and return proper tool error response instead of plain text
5. Update SQL query to use chunks/chunks_fts tables instead of sections

### Target file: scripts/mcp/mdq/tools.py

**Procedure**: Update grep_docs tool definition schema.

**Method**: Modify tool definition in tools.py.

**Details**:
1. Add max_matches, max_chars_per_match, context_before, context_after parameters to tool definition
2. Update GrepDocMatch schema to match new fields

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| service.py | Test path filtering | curl with paths parameter | Only results from specified paths returned |
| service.py | Test max_matches limit | curl with query returning >200 matches | Only 200 matches returned |
| service.py | Test max_chars_per_match | curl with large content match | Content truncated to max_chars_per_match |
| service.py | Test invalid regex | curl with invalid regex pattern | Tool error returned, not plain text |
| service.py | Test regex timeout | curl with catastrophic regex | Timeout error returned |

## Risks

- **Risk**: Regex timeout may kill legitimate long-running queries | **Likelihood**: Low | **Mitigation**: Use reasonable timeout (1 second); document limitation | False
- **Risk**: Context line extraction is complex for large files | **Likelihood**: Medium | **Mitigation**: Implement context extraction only for small files; skip for large files | False
