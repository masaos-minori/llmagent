## Goal

Capture the third return value (`idempotency_key`) from `extract_request_context()` instead of overwriting `request_id` or discarding it, and propagate it to `dispatch_tool()` via `_dispatch_shell_tool()`, enabling end-to-end duplicate detection for side-effecting shell tool calls. (REQ-001; AC-1)

## Scope

- Modify `scripts/mcp_servers/shell/shell_server.py`:
  - Change the three-value unpack at line 155 to capture `idempotency_key`
  - Pass `idempotency_key` to `_dispatch_shell_tool()`
  - Update `_dispatch_shell_tool()` signature to accept optional `idempotency_key` parameter

## Assumptions

- `extract_request_context()` returns `(session_id, request_id, idempotency_key)` per `scripts/mcp_servers/server.py`
- `dispatch_tool()` already accepts `idempotency_key: str | None = None` parameter (confirmed at `scripts/mcp_servers/dispatch.py:94`)
- When `idempotency_key` is `None`, duplicate detection is skipped (per `dispatch.py:116`)
- Adding an optional trailing parameter to `_dispatch_shell_tool()` is backward-compatible because existing callers pass positional arguments `(name, args)`

## Design decisions

- Use `idempotency_key` as the variable name (not `request_id`) to avoid shadowing the `request_id` variable used later in audit logging.
- Make the parameter optional with default `None` in `_dispatch_shell_tool()` so existing callers within the same file remain compatible.
- Forward the key via keyword argument `idempotency_key=idempotency_key` to make the intent explicit.

## Alternatives considered

- Overwriting `request_id` with the third value (current buggy pattern): rejected because it corrupts the audit log's `request_id` field.
- Using `_` to discard the third value: rejected because the key is needed for duplicate detection.
- Positional forwarding `await _dispatch_shell_tool(req.name, req.args, idempotency_key)`: rejected in favor of keyword argument for clarity.

## Implementation
### Target file

`scripts/mcp_servers/shell/shell_server.py`

### Procedure

1. At line 155, change the three-value unpack from `request_id, session_id, request_id = extract_request_context(request)` to `request_id, session_id, idempotency_key = extract_request_context(request)`.
2. At line 156, change `_dispatch_shell_tool(req.name, req.args)` to `await _dispatch_shell_tool(req.name, req.args, idempotency_key=idempotency_key)`.
3. At line 126, update `_dispatch_shell_tool(name: str, args: ToolArgs)` to `_dispatch_shell_tool(name: str, args: ToolArgs, idempotency_key: str | None = None)`.
4. At line 128, update the `dispatch_tool()` call inside `_dispatch_shell_tool` to include `idempotency_key=idempotency_key`.

### Method

Direct edit of four lines across two functions in the same file. No new imports required.

### Details

```diff
@@ -123,7 +123,7 @@
 # ──────────────────────────────────────────────────────────────────────────────
 
 
-async def _dispatch_shell_tool(name: str, args: ToolArgs) -> DispatchResult:
+async def _dispatch_shell_tool(name: str, args: ToolArgs, idempotency_key: str | None = None) -> DispatchResult:
     """Route shell tool calls through the service's dispatch table."""
-    return await dispatch_tool(_service.get_dispatch_table(), name, args)
+    return await dispatch_tool(_service.get_dispatch_table(), name, args, idempotency_key=idempotency_key)
 
 
@@ -152,8 +152,8 @@
     enabled, reason = _shell_tool_availability(_cfg, req.name)
     if not enabled:
         return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
-    request_id, session_id, request_id = extract_request_context(request)
-    r = await _dispatch_shell_tool(req.name, req.args)
+    request_id, session_id, idempotency_key = extract_request_context(request)
+    r = await _dispatch_shell_tool(req.name, req.args, idempotency_key=idempotency_key)
     _audit_log(
         logger,
         session_id=session_id,
```

## Compatibility considerations

- Backward-compatible: `_dispatch_shell_tool()` gains an optional trailing parameter with default `None`. Existing callers within the same file pass positional `(name, args)` — adding an optional trailing parameter does not break them.
- `dispatch_tool()` already has `idempotency_key: str | None = None` as an optional parameter.
- When `idempotency_key` is `None`, `dispatch.py:116` skips duplicate detection entirely — no behavioral change for current callers without the header.

## Security considerations

No new secrets exposure or unsafe operations introduced. The `idempotency_key` comes from the `x-idempotency-key` HTTP header, which is a client-provided identifier for deduplication.

## Rollback considerations

Revert the four-line diff above. If deployed partially (e.g., only the unpack fix without the dispatch wiring), the idempotency key will be captured but not propagated — the duplicate-detection feature remains inert.

## Validation plan

- Unit: Confirm the three-value unpack captures `idempotency_key` (not `request_id` or `_`) at line 155.
- Unit: Confirm `_dispatch_shell_tool()` is called with `idempotency_key=idempotency_key` at line 156.
- Unit: Confirm `_dispatch_shell_tool()` signature includes `idempotency_key: str | None = None` at line 126.
- Unit: Confirm `dispatch_tool()` call inside `_dispatch_shell_tool()` forwards `idempotency_key` at line 128.
- Regression: `uv run pytest tests/mcp_servers/test_shell_server.py -q` passes.
- Standard sequence: `uv run ruff check scripts/mcp_servers/shell/shell_server.py` clean; `uv run mypy scripts/mcp_servers/shell/shell_server.py` clean.

## Completion criteria

- [ ] Line 155 reads `request_id, session_id, idempotency_key = extract_request_context(request)` (not `request_id` or `_` as the third element).
- [ ] Line 156 passes `idempotency_key=idempotency_key` to `_dispatch_shell_tool()`.
- [ ] Line 126 signature includes `idempotency_key: str | None = None`.
- [ ] Line 128 forwards `idempotency_key=idempotency_key` to `dispatch_tool()`.
- [ ] All validation checks pass.

## Out of scope

- Modifying `dispatch.py`'s duplicate-detection logic itself.
- Adding the `x-idempotency-key` header to outgoing HTTP requests.
- Idempotency support for non-side-effecting tool calls beyond what `dispatch.py` already handles via `_is_side_effecting()`.
- Group B handlers (file/read, file/delete, file/write, rag_pipeline servers).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix three-value unpack at line 155: change `request_id, session_id, request_id` to `request_id, session_id, idempotency_key` | Pending | — | — | |
| 2 | Pass `idempotency_key` to `_dispatch_shell_tool()` at line 156 | Pending | — | — | |
| 3 | Update `_dispatch_shell_tool()` signature at line 126 to accept `idempotency_key: str | None = None` | Pending | — | — | |
| 4 | Forward `idempotency_key` to `dispatch_tool()` inside `_dispatch_shell_tool()` at line 128 | Pending | — | — | |
| 5 | Add or update tests per Validation plan | Pending | — | — | |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260918-073838_mcp001_wire_idempotency_key_header.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260918-075225_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-163828
- **Related target files**: scripts/mcp_servers/shell/shell_server.py
