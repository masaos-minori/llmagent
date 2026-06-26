## Goal

Treat index_paths and refresh_index as side-effect tools by adding safety, scheduling, and concurrency controls for MDQ indexing operations. Add write/admin metadata to tool definitions, configure concurrency limits, serialize concurrent indexing operations, and define search behavior during indexing.

## Scope

**In-Scope**:
- Mark index_paths and refresh_index as write/admin tools in tool safety tiers
- Add requires_serial: true or resource_scope: "mdq_index" metadata
- Configure concurrency limit for mdq server
- Serialize concurrent indexing operations
- Define behavior for search while indexing is running
- Invalidate cache after successful index updates

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' safety controls

## Assumptions

1. SQLite FTS5 triggers provide row-level integrity but not concurrent write protection
2. Cache invalidation should occur after successful index refresh
3. Search during indexing should return partial results with a warning that index is being updated

## Implementation

### Target file: scripts/mcp/mdq/tools.py

**Procedure**: Add write/admin metadata to index_paths and refresh_index tool definitions.

**Method**: Modify tool schema definitions in _MCP_TOOLS list.

**Details**:
1. `index_paths` tool: add `"is_write": true`, `"requires_serial": true` fields to the tool schema (after "status" field)
2. `refresh_index` tool: add same metadata (`"is_write": true`, `"requires_serial": true`)

### Target file: config/mdq_mcp_server.toml

**Procedure**: Add concurrency limit configuration for mdq server.

**Method**: Append new TOML entry to the existing config.

**Details**:
1. Add `concurrency_limit = 1` under the existing config section

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Add concurrency control, cache invalidation logic.

**Method**: Add asyncio.Lock for serialization, _is_indexing flag, and cache invalidation after index updates.

**Details**:
1. Add `self._index_lock = asyncio.Lock()` in MdqService.__init__
2. Add `self._is_indexing = False` flag in __init__
3. Wrap index_paths() and refresh_index() methods with lock context manager: `async with self._index_lock:`
4. Set `_is_indexing = True` before indexing, `_is_indexing = False` after
5. Add cache invalidation after successful index updates (clear any cached search results or outline data)

### Target file: config/agent.toml

**Procedure**: Add mdq to tool_safety_tiers and tool_concurrency_limits.

**Method**: Modify existing TOML config sections.

**Details**:
1. Add `mdq = "WRITE_DANGEROUS"` to `[tool_safety_tiers]` section (after git_push)
2. Add `mdq = 1` to `tool_concurrency_limits` dict in agent.toml (after cicd = 2)

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Define search behavior during indexing — return partial results with warning.

**Method**: Check `_is_indexing` flag before executing search, append warning to results if true.

**Details**:
1. In search_docs() method: check `if self._is_indexing:` before returning results
2. If indexing is in progress: append warning message like "[WARNING: Index is being updated — results may be incomplete]"
3. Return partial results rather than blocking

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools.py | Verify write metadata on index_paths and refresh_index | Check tool schema definitions | is_write: true, requires_serial: true present |
| service.py | Test concurrent indexing operations | Call index_paths and refresh_index simultaneously | Only one operation executes at a time |
| service.py | Test search during indexing | Call search_docs while indexing | Partial results with warning returned |
| agent.toml | Verify mdq in tool_safety_tiers | Check config file | mdq key present with WRITE_DANGEROUS classification |

## Risks

- **Risk**: Serialization causes user-visible delays for indexing operations | **Likelihood**: Low | **Mitigation**: Use non-blocking lock with timeout; return error if lock cannot be acquired | False
- **Risk**: Cache invalidation misses some cached entries | **Likelihood**: Medium | **Mitigation**: Implement comprehensive cache invalidation logic; test thoroughly | False
