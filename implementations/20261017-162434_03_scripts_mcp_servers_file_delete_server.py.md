## Goal

Emit one shared `mcp_tool_exec` audit record per `POST /v1/call_tool` on file-delete-mcp, for both
accepted and rejected calls, so a delete attempt that never reached the service is still recorded
(REQ-002).

## Scope

- Import the shared audit emitter into `scripts/mcp_servers/file/delete_server.py`.
- Bind the request context at the top of `call_tool` instead of discarding it.
- Emit a record on the disabled-`allowed_dirs` early return, on the validation-error early return,
  and after dispatch.

## Assumptions

- `DispatchResult.outcome` yields `"ok"` or `"error"` and is the correct value for the post-dispatch
  record; the two server-layer early returns are unambiguous rejections.
- Both tools on this server (`delete_file`, `delete_directory`) carry their resource in the `path`
  argument, so no per-tool target extraction is needed.
- The dedicated delete audit log written by `DeleteFileService` stays exactly as it is; the shared
  record is additive, not a replacement.

## Design decisions

- Record the attempted path in `target`, truncated to 80 characters, matching the existing convention
  in `scripts/mcp_servers/shell/shell_server.py` and `scripts/mcp_servers/mdq/audit_target.py`.
  `requested_target` is not set here: this layer has no canonical form to pair it with.
- Bind the context as `session_id, request_id, idempotency_key`, the order documented by
  `extract_request_context`, rather than the swapped order used by five other MCP servers.
- Call `_audit_log` directly, as cicd-mcp, shell-mcp, and web-search-mcp do.
- `error_type` is left at its default empty string, matching how git-mcp records rejections.

## Alternatives considered

- Emit only after dispatch: rejected — AC-001 requires a record for rejected calls, and both early
  returns currently produce none.
- Replace the dedicated delete audit log with the shared record: rejected — the dedicated log is the
  documented delete-specific channel and other documents reference it.

## Implementation

### Target file

`scripts/mcp_servers/file/delete_server.py`

### Procedure

1. Add `from mcp_servers.audit import _audit_log` (new) to the import block.
2. Replace the discarded context binding with a bound one, and move it to the top of `call_tool`.
3. Compute the audit target once, after the context binding.
4. Emit a rejected record before each of the two early returns.
5. Emit one record after dispatch, before `_to_call_tool_response`.

### Method

Keep the existing control flow and response values identical; only add emission statements and move
the context binding earlier. The shape mirrors `call_tool` in `scripts/mcp_servers/cicd/cicd_server.py`.

### Details

- `call_tool` is `scripts/mcp_servers/file/delete_server.py:208-221`. The discarded binding is
  `_, _, idempotency_key = extract_request_context(request)` at
  `scripts/mcp_servers/file/delete_server.py:219`.
- New head of `call_tool`:

```
    session_id, request_id, idempotency_key = extract_request_context(request)
    audit_target = cast(str, req.args.get("path", ""))[:80]
    if not _cfg.allowed_dirs:
        _audit_log(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target=audit_target,
            outcome="rejected",
            server_key=FILE_DELETE_SERVER_KEY,
        )
        return CallToolResponse(
            result="Tool disabled: allowed_dirs is empty", is_error=True
        )
```

- Validation-error return emits the same record shape, still with `outcome="rejected"`.
- Post-dispatch record uses `outcome=r.outcome` and the same `server_key`.
- `FILE_DELETE_SERVER_KEY` is already defined at `scripts/mcp_servers/file/delete_server.py:66`, and
  `cast` is already imported at `scripts/mcp_servers/file/delete_server.py:17`.

## Compatibility considerations

- Response bodies, status codes, and dispatch behaviour are unchanged; only log output is added.
- `tests/mcp_servers/file/test_file_delete_mcp_service.py` and
  `tests/mcp_servers/file/test_delete_service.py` assert service and response behaviour, not shared
  audit output, so they are unaffected.

## Security considerations

- The record contains the caller-supplied path, which is the attempted action and the point of the
  audit. It records no file content and no directory listing.
- Truncation to 80 characters bounds record size for pathological paths.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest -q tests/mcp_servers/file/test_file_server_audit_records.py` (new, Plan row 7)
- `uv run pytest -q tests/mcp_servers/file/test_file_delete_mcp_service.py tests/mcp_servers/file/test_delete_service.py`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- Every `POST /v1/call_tool` on file-delete-mcp produces exactly one parseable JSON-lines record with
  `event` set to `mcp_tool_exec` and `server_key` set to `file_delete` (AC-001).
- A disabled-tool rejection and a validation failure each produce a record with `outcome` set to
  `rejected` before the response is returned (AC-001).

## Out of scope

- Emission from `DeleteFileService` or changes to its dedicated audit log.
- Fixing the swapped context binding in the other MCP servers.
- Documenting the field vocabulary (Plan target row 17).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the audit import, bind the request context, and emit records on all three return paths | Completed | 20261017-190500 | 20261017-192200 | REQ-002 |
| 2 | Add or update tests per Validation plan | Completed | 20261017-190500 | 20261017-192200 | Owned by Plan row 7 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-190500 | 20261017-192200 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-10-17 | Owned by Plan row 12 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `scripts/mcp_servers/file/delete_server.py`