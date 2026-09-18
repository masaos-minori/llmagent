## Goal

Capture the third return value (`idempotency_key`) from `extract_request_context()` instead of discarding it via `_`, and propagate it to `dispatch_tool()` via `_dispatch_mdq_tool()`, enabling end-to-end duplicate detection for side-effecting MDQ tool calls. (REQ-001; AC-1)

## Scope

- Modify `scripts/mcp_servers/mdq/mdq_server.py`:
  - Change the three-value unpack at line 343 in `call_tool()` to capture `idempotency_key`
  - Pass `idempotency_key` to `_dispatch_mdq_tool()`
  - Update `_dispatch_mdq_tool()` signature to accept optional `idempotency_key` parameter
- Note: Line 81 in `_mdq_error_handler()` also uses `_` to discard the third value, but this function does not call `dispatch_tool()` and therefore does not need the key wired through.

## Assumptions

- `extract_request_context()` returns `(session_id, request_id, idempotency_key)` per `scripts/mcp_servers/server.py`
- `dispatch_tool()` already accepts `idempotency_key: str | None = None` parameter (confirmed at `scripts/mcp_servers/dispatch.py:94`)
- When `idempotency_key` is `None`, duplicate detection is skipped (per `dispatch.py:116`)
- Adding an optional trailing parameter to `_dispatch_mdq_tool()` is backward-compatible because existing callers pass positional arguments `(name, args)`

## Design decisions

- Use `idempotency_key` as the variable name (not `request_id`) to avoid shadowing the `request_id` variable used later in audit logging.
- Make the parameter optional with default `None` in `_dispatch_mdq_tool()` so existing callers within the same file remain compatible.
- Forward the key via keyword argument `idempotency_key=idempotency_key` to make the intent explicit.
- Do NOT modify `_mdq_error_handler()` at line 81 — it is an exception handler callback that does not invoke any side-effecting operation and has no mechanism to forward the key.

## Alternatives considered

- Overwriting `request_id` with the third value (current buggy pattern): rejected because it corrupts the audit log's `request_id` field.
- Using `_` to discard the third value: rejected because the key is needed for duplicate detection.
- Positional forwarding `await _dispatch_mdq_tool(req.name, req.args, idempotency_key)`: rejected in favor of keyword argument for clarity.

## Implementation
### Target file

`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure

1. At line 343, change the three-value unpack from `request_id, session_id, _ = extract_request_context(request)` to `request_id, session_id, idempotency_key = extract_request_context(request)`.
2. At line 347, change `_dispatch_mdq_tool(req.name, req.args)` to `await _dispatch_mdq_tool(req.name, req.args, idempotency_key=idempotency_key)`.
3. At line 264, update `_dispatch_mdq_tool(name: str, args: ToolArgs)` to `_dispatch_mdq_tool(name: str, args: ToolArgs, idempotency_key: str | None = None)`.
4. At line 268, update the `dispatch_tool()` call inside `_dispatch_mdq_tool` to include `idempotency_key=idempotency_key`.

### Method

Direct edit of four lines across two functions in the same file. No new imports required.

### Details

```diff
@@ -261,11 +261,11 @@
 }
 
 
-async def _dispatch_mdq_tool(name: str, args: ToolArgs) -> MdqDispatchResult:
+async def _dispatch_mdq_tool(name: str, args: ToolArgs, idempotency_key: str | None = None) -> MdqDispatchResult:
     """Route a tool call through the shared dispatch mechanism, capturing mdq-local metadata."""
     token = _mdq_metadata_var.set({})
     try:
-        result = await dispatch_tool(_DISPATCH_TABLE, name, args)
+        result = await dispatch_tool(_DISPATCH_TABLE, name, args, idempotency_key=idempotency_key)
         metadata = _mdq_metadata_var.get()
     finally:
         _mdq_metadata_var.reset(token)
@@ -340,11 +340,11 @@
 @app.post("/v1/call_tool", response_model=CallToolResponse)
 async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
     """Handle MCP call_tool requests with audit logging and error handling."""
     t0 = time.perf_counter()
-    request_id, session_id, _ = extract_request_context(request)
+    request_id, session_id, idempotency_key = extract_request_context(request)
     target = extract_audit_target(req.name, req.args)
 
     try:
-        r = await _dispatch_mdq_tool(req.name, req.args)
+        r = await _dispatch_mdq_tool(req.name, req.args, idempotency_key=idempotency_key)
     except (
         MdqValidationError,
         MdqAuthorizationError,
```

## Compatibility considerations

- Backward-compatible: `_dispatch_mdq_tool()` gains an optional trailing parameter with default `None`. Existing callers within the same file pass positional `(name, args)` — adding an optional trailing parameter does not break them.
- `dispatch_tool()` already has `idempotency_key: str | None = None` as an optional parameter.
- When `idempotency_key` is `None`, `dispatch.py:116` skips duplicate detection entirely — no behavioral change for current callers without the header.

## Security considerations

No new secrets exposure or unsafe operations introduced. The `idempotency_key` comes from the `x-idempotency-key` HTTP header, which is a client-provided identifier for deduplication.

## Rollback considerations

Revert the four-line diff above. If deployed partially (e.g., only the unpack fix without the dispatch wiring), the idempotency key will be captured but not propagated — the duplicate-detection feature remains inert.

## Validation plan

- Unit: Confirm the three-value unpack captures `idempotency_key` (not `request_id` or `_`) at line 343.
- Unit: Confirm `_dispatch_mdq_tool()` is called with `idempotency_key=idempotency_key` at line 347.
- Unit: Confirm `_dispatch_mdq_tool()` signature includes `idempotency_key: str | None = None` at line 264.
- Unit: Confirm `dispatch_tool()` call inside `_dispatch_mdq_tool()` forwards `idempotency_key` at line 268.
- Regression: `uv run pytest tests/mcp_servers/test_mdp_server.py -q` passes.
- Standard sequence: `uv run ruff check scripts/mcp_servers/mdq/mdq_server.py` clean; `uv run mypy scripts/mcp_servers/mdq/mdq_server.py` clean.

## Completion criteria

- [ ] Line 343 reads `request_id, session_id, idempotency_key = extract_request_context(request)` (not `request_id` or `_` as the third element).
- [ ] Line 347 passes `idempotency_key=idempotency_key` to `_dispatch_mdq_tool()`.
- [ ] Line 264 signature includes `idempotency_key: str | None = None`.
- [ ] Line 268 forwards `idempotency_key=idempotency_key` to `dispatch_tool()`.
- [ ] All validation checks pass.

## Out of scope

- Modifying `_mdq_error_handler()` at line 81 — it does not call `dispatch_tool()` and has no mechanism to forward the key.
- Modifying `dispatch.py`'s duplicate-detection logic itself.
- Adding the `x-idempotency-key` header to outgoing HTTP requests.
- Idempotency support for non-side-effecting tool calls beyond what `dispatch.py` already handles via `_is_side_effecting()`.
- Group B handlers (file/read, file/delete, file/write, rag_pipeline servers).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix three-value unpack at line 343: change `request_id, session_id, _` to `request_id, session_id, idempotency_key` | Pending | — | — | |
| 2 | Pass `idempotency_key` to `_dispatch_mdq_tool()` at line 347 | Pending | — | — | |
| 3 | Update `_dispatch_mdq_tool()` signature at line 264 to accept `idempotency_key: str | None = None` | Pending | — | — | |
| 4 | Forward `idempotency_key` to `dispatch_tool()` inside `_dispatch_mdq_tool()` at line 268 | Pending | — | — | |
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
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py
