# Goal

Add stale document count to mdq-mcp /health endpoint details.

## Scope

**In-Scope**:
- Add `stale_document_count` field to `/health` response details in `scripts/mcp/mdq/server.py`
- Query sections table to find documents where file_mtime doesn't match current file mtime

**Out-of-Scope**:
- Changes to other MCP servers' health endpoints
- Adding new tools or features to mdq-mcp

## Assumptions

1. Stale document = sections where file_mtime doesn't match the current file's mtime at index_paths
2. The config `index_paths` contains the list of paths being indexed
3. A document is stale if its file_mtime is older than the current file's mtime

## Implementation

### Target file: `scripts/mcp/mdq/server.py`

#### Procedure

1. After line 195 (after getting last_indexed), add stale document count calculation
2. Query sections table to find documents where file_mtime doesn't match current file mtime
3. Add stale_document_count to details

#### Method

Use Edit tool to insert the stale document count logic after line 195.

#### Details

Insert after line 195:

```python
            # Check for stale documents (file_mtime mismatch)
            try:
                from pathlib import Path as _Path
                stale_count = 0
                index_paths_cfg = mdq_cfg.get("index_paths", []) or []
                if index_paths_cfg:
                    # Get current mtime of the first index path directory
                    first_path = _Path(index_paths_cfg[0])
                    if first_path.is_dir():
                        # Use the directory's mtime as reference
                        ref_mtime = first_path.stat().st_mtime
                        stale_count = conn.execute(
                            "SELECT COUNT(DISTINCT file_path) FROM sections WHERE file_mtime < ?",
                            (ref_mtime,)
                        ).fetchone()["COUNT(DISTINCT file_path)"] or 0
                    elif first_path.is_file():
                        # Use the file's mtime as reference
                        ref_mtime = first_path.stat().st_mtime
                        stale_count = conn.execute(
                            "SELECT COUNT(DISTINCT file_path) FROM sections WHERE file_mtime < ?",
                            (ref_mtime,)
                        ).fetchone()["COUNT(DISTINCT file_path)"] or 0
            except Exception:
                # If stale count fails, don't break health check
                stale_count = None
            details["stale_document_count"] = stale_count
```

## Validation plan

| Target File | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| server.py | Verify /health includes stale_document_count field | curl http://127.0.0.1:8013/health | stale_document_count present in details |
| server.py | Verify stale count is 0 when files are fresh | curl with up-to-date index | stale_document_count: 0 |
| server.py | Verify stale count > 0 when files are outdated | Modify file mtime to be older, curl again | stale_document_count > 0 |