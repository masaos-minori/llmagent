## Goal

Capture the third return value (`idempotency_key`) from `extract_request_context()` instead of overwriting `request_id`, and propagate it directly to `dispatch_tool()`, enabling end-to-end duplicate detection for side-effecting git tool calls. (REQ-001; AC-1)

## Scope

- Modify `scripts/mcp_servers/git/git_server.py`:
  - Change the three-value unpack at line 185 to capture `idempotency_key`
  - Pass `idempotency_key` directly to `dispatch_tool()` at line 246
  - No wrapper function exists — this is the simplest case among Group A files

## Assumptions

- `extract_request_context()` returns `(session_id, request_id, idempotency_key)` per `scripts/mcp_servers/server.py`
- `dispatch_tool()` already accepts `idempotency_key: str | None = None` parameter (confirmed at `scripts/mcp_servers/dispatch.py:94`)
- When `idempotency_key` is `None`, duplicate detection is skipped (per `dispatch.py:116`)
- Adding an optional trailing parameter to `dispatch_tool()` call is backward-compatible because the parameter already has a default of `None`

## Design decisions

- Use `idempotency_key` as the variable name (not `request_id`) to avoid shadowing the `request_id` variable used later in audit logging.
- Pass `idempotency_key` directly to `dispatch_tool()` rather than through a wrapper (no `_dispatch_git_tool` exists in this file).
- Forward the key via keyword argument `idempotency_key=idempotency_key` to make the intent explicit.

## Alternatives considered

- Overwriting `request_id` with the third value (current buggy pattern): rejected because it corrupts the audit log's `request_id` field.
- Using `_` to discard the third value: rejected because the key is needed for duplicate detection.
- Positional forwarding `dispatch_tool(_service.get_dispatch_table(), req.name, req.args, idempotency_key)`: rejected in favor of keyword argument for clarity.

## Implementation
### Target file

`scripts/mcp_servers/git/git_server.py`

### Procedure

1. At line 185, change the three-value unpack from `request_id, session_id, request_id = extract_request_context(request)` to `request_id, session_id, idempotency_key = extract_request_context(request)`.
2. At line 246, change `await dispatch_tool(_service.get_dispatch_table(), req.name, req.args)` to `await dispatch_tool(_service.get_dispatch_table(), req.name, req.args, idempotency_key=idempotency_key)`.

### Method

Direct edit of two lines in the same function. No new imports required. No wrapper function modification needed (unlike other Group A files).

### Details

```diff
@@ -182,7 +182,7 @@
     except ValueError as e:
         return CallToolResponse(result=f"Validation error: {e}", is_error=True)
     t0 = time.perf_counter()
-    request_id, session_id, request_id = extract_request_context(request)
+    request_id, session_id, idempotency_key = extract_request_context(request)
     repo_path = cast(str, req.args.get("repo_path", ""))
     ok, err, resolved = _resolve_repo_path(repo_path)
     if not ok:
@@ -243,7 +243,7 @@
     pre_state = RepositoryState.snapshot(
         resolved, protected_branches=_cfg.protected_branches, active_ref=active_ref
     )
-    result = await dispatch_tool(_service.get_dispatch_table(), req.name, req.args)
+    result = await dispatch_tool(_service.get_dispatch_table(), req.name, req.args, idempotency_key=idempotency_key)
     post_state = RepositoryState.snapshot(
         resolved, protected_branches=_cfg.protected_branches, active_ref=active_ref
     )
```

## Compatibility considerations

- Backward-compatible: `dispatch_tool()` already has `idempotency_key: str | None = None` as an optional parameter.
- When `idempotency_key` is `None`, `dispatch.py:116` skips duplicate detection entirely — no behavioral change for current callers without the header.
- This file has no `_dispatch_git_tool` wrapper, so there are fewer moving parts compared to other Group A files.

## Security considerations

No new secrets exposure or unsafe operations introduced. The `idempotency_key` comes from the `x-idempotency-key` HTTP header, which is a client-provided identifier for deduplication.

## Rollback considerations

Revert the two-line diff above. If deployed partially (e.g., only the unpack fix without the dispatch wiring), the idempotency key will be captured but not propagated — the duplicate-detection feature remains inert.

## Validation plan

- Unit: Confirm the three-value unpack captures `idempotency_key` (not `request_id` or `_`) at line 185.
- Unit: Confirm `dispatch_tool()` is called with `idempotency_key=idempotency_key` at line 246.
- Regression: `uv run pytest tests/mcp_servers/test_git_server.py -q` passes.
- Standard sequence: `uv run ruff check scripts/mcp_servers/git/git_server.py` clean; `uv run mypy scripts/mcp_servers/git/git_server.py` clean.

## Completion criteria

- [ ] Line 185 reads `request_id, session_id, idempotency_key = extract_request_context(request)` (not `request_id` or `_` as the third element).
- [ ] Line 246 passes `idempotency_key=idempotency_key` to `dispatch_tool()`.
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
| 1 | Fix three-value unpack at line 185: change `request_id, session_id, request_id` to `request_id, session_id, idempotency_key` | Pending | — | — | |
| 2 | Pass `idempotency_key` to `dispatch_tool()` at line 246 | Pending | — | — | |
| 3 | Add or update tests per Validation plan | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: scripts/mcp_servers/git/git_server.py
