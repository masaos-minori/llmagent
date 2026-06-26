## Goal

Implement index-backed outline retrieval for MDQ by reading from indexed chunks instead of reparsing files, returning hierarchy metadata and chunk IDs.

## Scope

**In-Scope**:
- Read outline data from indexed chunks table
- Return hierarchy information: heading, level, heading_path, chunk_id, start_line, end_line
- Add max_depth parameter to limit heading depth
- Add max_items parameter to cap result count
- Return stale index warning if source file changed after indexing

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' outline behavior

## Assumptions

1. max_depth default = 6 (reasonable for most Markdown documents)
2. max_items default = 500 (cap for large documents)
3. Stale index warning: compare documents.mtime_ns with documents.indexed_at

## Implementation

### Target file: scripts/mcp/mdq/models.py

**Procedure**: Update OutlineRequest with new fields, update OutlineResponse with hierarchy metadata.

**Method**: Modify BaseModel class definitions in models.py.

**Details**:
1. `OutlineRequest`: add `max_depth: int = 6`, `max_items: int = 500` fields (after `path` field)
2. Replace `OutlineHeading` with structured response model:
   - `heading: str` — heading text
   - `level: int` — heading level (1-6)
   - `heading_path: str` — heading hierarchy path
   - `chunk_id: str` — chunk identifier for follow-up get_chunk calls
   - `start_line: int` — start line number
   - `end_line: int` — end line number
3. Replace `OutlineResponse` with structured response including headings list and stale warning

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Rewrite outline method to query chunks table, add stale check.

**Method**: Replace outline() method implementation to use indexed chunks instead of parsing files.

**Details**:
1. Query chunks table for source_path matching req.path:
   - Add WHERE clause: `WHERE c.source_path = ?`
   - Order by heading_level, ordinal
2. Filter by max_depth if specified:
   - Add WHERE clause: `AND c.heading_level <= ?`
3. Cap results at max_items:
   - Add LIMIT clause with req.max_items
4. Add stale index warning:
   - Query documents table for same source_path
   - Compare documents.mtime_ns with documents.indexed_at
   - If mtime > indexed_at, add stale warning to response

### Target file: scripts/mcp/mdq/tools.py

**Procedure**: Update outline tool definition schema.

**Method**: Modify tool definition in tools.py.

**Details**:
1. Add max_depth, max_items parameters to tool definition
2. Update OutlineHeading schema to match new fields
3. Update OutlineResponse schema to include stale warning field

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| service.py | Test with unchanged file | curl with existing file path | Structured response with chunk_ids returned |
| service.py | Test with changed file | Modify file, run outline | Stale index warning present in response |
| service.py | Test max_depth limit | curl with max_depth=2 | Only depth 1-2 headings returned |
| service.py | Test max_items cap | curl with large document | Only max_items results returned |

## Risks

- **Risk**: Breaking changes to consumers expecting plain text response | **Likelihood**: Medium | **Mitigation**: Document breaking changes; consider backward-compatible response format | False
- **Risk**: Stale index detection misses rapid file changes | **Likelihood**: Low | **Mitigation**: Use mtime_ns for precision; document limitation | False
