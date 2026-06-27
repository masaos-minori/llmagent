## Goal

Implement true incremental refresh_index behavior for MDQ by tracking file metadata (mtime_ns, size_bytes, content_hash) and only re-indexing changed files. Add force option for full re-index and return structured refresh summary.

## Scope

**In-Scope**:
- Track file metadata: mtime_ns, size_bytes, content_hash
- Skip unchanged files based on metadata comparison
- Re-index changed files only
- Remove chunks for deleted files
- Add force option for full re-index
- Return structured refresh summary (indexed count, skipped count, deleted count, failed count, elapsed time)

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' indexing behavior

## Assumptions

1. index_state table already exists in service.py for tracking file metadata
2. Force option should bypass all skip logic and re-index everything
3. Deleted files should be detected by comparing current filesystem state with index_state records

## Implementation

### Target file: models.py

**Procedure**: Add force field to RefreshIndexRequest, update RefreshIndexResponse with structured summary.

**Method**: Modify BaseModel class definitions.

**Details**:
1. `RefreshIndexRequest`: add `force: bool = False` field (after `paths` field)
2. Replace `RefreshIndexResponse` with structured summary fields:
   - `indexed_count: int` — number of files indexed
   - `skipped_count: int` — number of unchanged files skipped
   - `deleted_count: int` — number of deleted files removed from index
   - `failed_count: int` — number of files that failed to index
   - `elapsed_seconds: float` — total elapsed time

### Target file: scripts/mcp/mdq/indexer.py

**Procedure**: Add incremental indexing logic with metadata comparison.

**Method**: Modify `_index_paths()` function to compare metadata and skip unchanged files.

**Details**:
1. Load index_state records for current index_paths before indexing
2. For each file in req.paths:
   - If force=True: always re-index (skip all comparison)
   - Else: compare mtime_ns and content_hash with index_state record
   - If metadata matches (unchanged): skip, increment skipped_count
   - If metadata differs (changed): re-index via existing logic, increment indexed_count
3. Detect deleted files:
   - Compare index_state paths with current filesystem state
   - For paths in index_state but not on filesystem: delete chunks and index_state records, increment deleted_count
4. Track failed_count for any I/O errors during indexing

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Update refresh_index to use incremental indexer and return structured summary.

**Method**: Modify refresh_index() method to collect and return summary from indexer.

**Details**:
1. Pass force option from request to indexer: `req.force`
2. Collect structured summary from indexer (indexed_count, skipped_count, deleted_count, failed_count, elapsed_seconds)
3. Return formatted summary string instead of simple message

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Update stats() method to query chunks/documents tables instead of sections.

**Method**: Modify SQL queries in stats() method.

**Details**:
1. Replace `"SELECT COUNT(*) as cnt FROM sections"` → `"SELECT COUNT(*) as cnt FROM chunks"` (line 349)
2. Replace `"SELECT COUNT(DISTINCT file_path) as cnt FROM sections"` → `"SELECT COUNT(DISTINCT source_path) as cnt FROM chunks"` (line 352)

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| indexer.py | Test with unchanged files | Modify file mtime, run refresh_index | Unchanged files skipped, indexed_count=0 |
| indexer.py | Test with changed files | Modify file content, run refresh_index | Changed files re-indexed, indexed_count>0 |
| indexer.py | Test with deleted files | Delete a file, run refresh_index | Deleted file removed from index, deleted_count>0 |
| indexer.py | Test force option | Run refresh_index with force=True | All files re-indexed regardless of changes |
| service.py | Verify structured summary | Check response fields | indexed_count, skipped_count, deleted_count present |

## Risks

- **Risk**: Deleted file detection misses files outside tracked index_paths | **Likelihood**: Low | **Mitigation**: Document that deleted file detection only works within configured index_paths | False
- **Risk**: Metadata comparison fails on edge cases (e.g., mtime precision) | **Likelihood**: Medium | **Mitigation**: Use content_hash as primary change detection; fall back to mtime if hash unavailable | False
