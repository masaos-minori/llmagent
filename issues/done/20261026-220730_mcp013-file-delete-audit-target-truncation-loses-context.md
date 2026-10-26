# file/delete_server.py audit target truncation loses context

## Priority
Low

## Summary
The `call_tool` endpoint in `delete_server.py` truncates the audit target to 80 characters at line 213, which can lose critical path information for long paths.

## Background
The `call_tool` endpoint in `delete_server.py` (lines 209-250):

```python
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    session_id, request_id, idempotency_key = extract_request_context(request)
    audit_target = cast(str, req.args.get("path", ""))[:80]
    ...
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=audit_target,
        outcome=r.outcome,
        server_key=FILE_DELETE_SERVER_KEY,
    )
```

The `audit_target` is truncated to 80 characters at line 213:

```python
audit_target = cast(str, req.args.get("path", ""))[:80]
```

This same pattern appears in other MCP servers:
- `git_server.py` line 401: `target=target[:80]`
- `mdq_server.py` line 401: `target=target[:80]`

## Problem
Truncating the path to 80 characters can lose critical information:
1. For paths longer than 80 characters, the truncated path may not uniquely identify the file being deleted.
2. Two different files with the same first 80 characters will produce identical audit entries, making it impossible to distinguish between them.
3. The truncation is applied before the audit log entry is created, so the full path is not available for forensic analysis.

For example:
- `/home/user/documents/project-alpha/src/main.py` → `/home/user/documents/project-alpha/src/main.py` (no truncation needed)
- `/home/user/documents/project-alpha/src/main.py.bak` → `/home/user/documents/project-alpha/src/main.py.bak` (no truncation needed)
- `/home/user/documents/project-alpha/src/main.py.backup.20241026` → `/home/user/documents/project-alpha/src/main.py.backu` (truncated, loses `.backup.20241026`)

## Reason for Change
Truncating the path to 80 characters can lose critical information needed for forensic analysis. A more robust approach would either use a hash-based identifier or store the full path in a separate field.

## Implementation Intent
1. Add a `full_path` field to the audit log entry that stores the untruncated path, or
2. Use a hash-based identifier for the target while keeping the truncated path for display, or
3. Increase the truncation limit to accommodate longer paths.

## Target Files orAreas
- `scripts/mcp_servers/file/delete_server.py` — `call_tool` endpoint (lines 209-250)

## Required Changes
- Add a `full_path` field to the audit log entry that stores the untruncated path
- Or use a hash-based identifier for the target
- Document the change in the audit log schema

## Constraints
- Must not change the existing audit log format (backward compatibility)
- Must preserve the 80-character truncation for display purposes

## Acceptance Criteria
- Full path is available for forensic analysis
- Truncated path is still used for display purposes
- No breaking changes to the audit log format

## Testing Expectations
- Unit test: verify full path is stored in audit log
- Integration test: verify audit log distinguishes between similar paths
- Regression test: ensure existing audit log format is preserved

## Documentation Impact
Update the audit log schema documentation to include the new `full_path` field.

## Out of Scope
- Changes to the audit log format itself (beyond adding the new field)
- Changes to how paths are validated before auditing

## Dependencies
N/A: none

## Unresolved Questions
- What is the maximum path length that should be supported?
- Are there other MCP servers with the same pattern?

## AI ImplementationInstruction
In `scripts/mcp_servers/file/delete_server.py`, add a `full_path` field to the audit log entry that stores the untruncated path. Do not modify any other MCP server's audit logic.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/file/delete_server.py
