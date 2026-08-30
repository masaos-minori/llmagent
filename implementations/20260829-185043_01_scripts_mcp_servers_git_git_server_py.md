# Implementation Procedure: NC-020 Row 1 — Modify `call_tool()` to use resolved canonical target

## Goal

Change `call_tool()` in `git_server.py` to use the resolved canonical repository path from `GitSecurityGuards._check_repo_path()` as the audit log `target` field instead of the raw caller-supplied `repo_path` string.

## Scope

Only `scripts/mcp_servers/git/git_server.py`: modify the `_audit_log()` call site within `call_tool()`. No other files are modified by this procedure document.

## Assumptions

- Row 2 changes `_check_repo_path()` return type from `(bool, str)` to `(bool, str, str)`, where the third element is the resolved path when `ok=True` and empty string when `ok=False`.
- The current code reads `req.args.get("repo", "")` which is incorrect — the schema uses `repo_path`, not `repo`.
- After Row 2, callers will unpack `ok, err, resolved = _check_repo_path(...)`.

## Design decisions

- **Use resolved path as audit target**: The canonical identity (post-validation, symlink-resolved) is the correct value for audit records because it identifies the actual repository affected, regardless of how the caller referred to it.
- **Fix `"repo"` to `"repo_path"`**: This is a prerequisite — even without Row 2's change, the current key is wrong.
- **Empty string fallback**: When `ok=False`, `resolved=""` ensures the audit record has a meaningful `outcome="rejected"` but no spurious target identity.

## Alternatives considered

1. **Keep using raw `repo_path`**: Would leave audit records with potentially misleading identities (symlinks, relative paths, path traversal attempts would all appear as different targets).
2. **Resolve path separately in `call_tool()`**: Would duplicate the `Path(repo_path).resolve()` computation that `_check_repo_path()` already performs.
3. **Introduce a new audit parameter**: Would require changing `_audit_log()` signature across all MCP servers — too broad for this issue.

## Implementation

### Target file

`scripts/mcp_servers/git/git_server.py`

### Procedure

1. Fix the audit `target` key from `"repo"` to `"repo_path"`.
2. After Row 2 is applied, consume the third element of `_check_repo_path()` return value as the audit `target`.

### Method

Direct modification of the `call_tool()` function body.

### Details

```python
# Before (current):
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    enabled, reason = _git_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    try:
        req.validate_args()
    except ValueError as e:
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    t0 = time.perf_counter()
    session_id, request_id = extract_request_context(request)
    r = await _dispatch_git_tool(req.name, req.args)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=cast(str, req.args.get("repo", "")),
        outcome=r.outcome,
        server_key="git",
    )
    return _to_call_tool_response(r)

# After Row 2 (with resolved path):
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    enabled, reason = _git_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    try:
        req.validate_args()
    except ValueError as e:
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    t0 = time.perf_counter()
    session_id, request_id = extract_request_context(request)
    repo_path = cast(str, req.args.get("repo_path", ""))
    ok, err, resolved = _service.security._check_repo_path(repo_path)
    if not ok:
        _audit_log(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target="",
            outcome="rejected",
            server_key="git",
            error_type="validation_error",
        )
        return CallToolResponse(result=err, is_error=True)
    r = await _dispatch_git_tool(req.name, req.args)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=resolved,
        outcome=r.outcome,
        server_key="git",
    )
    return _to_call_tool_response(r)
```

Note: The above shows the full `call_tool()` after both Row 1 and Row 2 changes combined. In practice, Row 1 alone should:
1. Fix `"repo"` to `"repo_path"` immediately (standalone fix).
2. Prepare the audit `target` variable to accept the resolved path once Row 2 is applied.

## Compatibility considerations

- **Breaking change to audit records**: Audit records will now contain canonical paths instead of raw strings. Downstream consumers must handle both formats during transition.
- **Pre-existing bug**: The `"repo"` vs `"repo_path"` key mismatch is a pre-existing bug that Row 1 fixes independently of Row 2.

## Security considerations

- **No credential exposure**: The resolved path is a filesystem path, never a remote URL.
- **Symlink resolution preserved**: `Path(repo_path).resolve()` resolves symlinks; the audit record reflects the actual repository.
- **Denial messages unchanged**: Error strings remain identical.

## Rollback considerations

- Revert the `target` parameter back to `req.args.get("repo", "")`.
- Remove the `error_type` addition if added.
- No data loss possible since only audit logging is changed.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| Audit `target` field populated | Verify audit record contains non-empty target | Manual inspection of audit log | Non-empty `target` field for valid calls |
| Key name fix | Verify `"repo_path"` key used | Code review | No `"repo"` key references remain |
| Type-checking | Run mypy on modified file | `uv run mypy scripts/mcp_servers/git/git_server.py` | No type errors introduced |

## Completion criteria

- [ ] Audit `target` key fixed from `"repo"` to `"repo_path"`
- [ ] Resolved path consumed from `_check_repo_path()` return value
- [ ] Pre-dispatch rejection audit record includes `error_type`
- [ ] No type-checking regressions introduced

## Out of scope

- Modifying `_check_repo_path()` return type (covered by Row 2)
- Adding new audit fields or changing audit schema
- Modifying `_audit_log()` function signature

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix `"repo"` to `"repo_path"` key in audit call | Pending | - | - | Standalone fix |
| 2 | Consume resolved path from `_check_repo_path()` | Pending | - | - | Depends on Row 2 |
| 3 | Add `error_type` to pre-dispatch rejection audit | Pending | - | - | Depends on Row 2 |
| 4 | Run validation sequence | Pending | - | - | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| - | - | - | - |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| - | - | - | - | - | - |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260828-160910_nc020_git_mcp_audit_target_resolution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-115719_nc020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-185043
- **Related target files**: scripts/mcp_servers/git/git_server.py
