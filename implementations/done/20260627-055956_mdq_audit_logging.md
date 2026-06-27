## Goal

Improve MDQ audit logging target and details per tool by setting appropriate targets (query for search_docs, chunk ID for get_chunk, path for outline, etc.) and adding detail fields (result count, elapsed time, truncated flag, indexed count, skipped count, deleted count, error kind).

## Scope

**In-Scope**:
- Set audit target per tool: query+path for search_docs, chunk_id for get_chunk, path for outline, first path for index_paths/refresh_index, pattern for grep_docs, service name for stats
- Add detail fields: result count, elapsed time, truncated flag, indexed count, skipped count, deleted count, error kind
- Preserve X-Session-Id and X-Request-Id correlation

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' audit logging

## Assumptions

1. Elapsed time measurement uses time.perf_counter() like cicd/server.py
2. Detail fields are only populated when available (some may be None)
3. Error kind is derived from exception type (ValueError, PermissionError, etc.)

## Implementation

### Target file: scripts/mcp/mdq/server.py

**Procedure**: Update target extraction logic, add elapsed time measurement, add detail fields.

**Method**: Modify _handle_mdq_tool() function to use tool-aware target extraction and pass detail parameter to _audit_log().

**Details**:
1. Replace flat `req.args.get("query", req.args.get("path", ""))` with tool-aware logic:
   - search_docs: target = query + optional path filter
   - get_chunk: target = chunk_id
   - outline: target = path
   - index_paths: target = first path in paths list
   - refresh_index: target = first path in paths list
   - grep_docs: target = regex pattern
   - stats: target = "mdq-mcp" (service name)
2. Add elapsed time measurement:
   - Already exists: `ms = (time.perf_counter() - t0) * 1000` (line 124)
   - Convert to seconds for detail field: `elapsed = ms / 1000`
3. Add detail fields to _audit_log call:
   - `detail={"result_count": result_count, "elapsed_seconds": elapsed, "truncated": truncated}`
   - For index operations: add `indexed_count`, `skipped_count`, `deleted_count`
   - For errors: add `error_kind = type(e).__name__`

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Return structured results with metadata (result count, truncated flag).

**Method**: Modify service methods to return structured response objects instead of plain strings.

**Details**:
1. Update search_docs to return result count and truncated flag:
   - Add `result_count` field to response
   - Add `truncated` flag when results exceed limit
2. Update grep_docs to return result count and truncated flag:
   - Add `result_count` field to response
   - Add `truncated` flag when results exceed max_matches
3. Update index operations to return structured summary:
   - indexed_count, skipped_count, deleted_count fields

### Target file: mcp/audit.py

**Procedure**: Verify detail parameter is supported by _audit_log().

**Method**: Check _audit_log() function signature and implementation.

**Details**:
1. Verify _audit_log() accepts `detail` parameter
2. If not, add `detail: dict | None = None` parameter to _audit_log()

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| server.py | Verify target per tool | Check audit log for each tool call | Correct target extracted per tool |
| server.py | Verify elapsed time | Check audit log detail field | Elapsed time present in detail |
| server.py | Verify result count | Check audit log for search/grep | Result count present in detail |
| server.py | Verify X-Session-Id correlation | Check audit log session/request IDs | Session/request IDs preserved |

## Risks

- **Risk**: Audit log detail becomes too verbose for production use | **Likelihood**: Medium | **Mitigation**: Make detail fields optional; document verbosity implications | False
- **Risk**: Error kind classification misses edge cases | **Likelihood**: Low | **Mitigation**: Use broad error categories (e.g., "validation_error", "permission_error") | False
