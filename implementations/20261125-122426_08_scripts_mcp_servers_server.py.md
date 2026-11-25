## Goal

Give every server one way to build the context from a request, widen the base programmatic `dispatch` to accept it, and inject the preview-capability map at bootstrap (REQ-002, REQ-006, REQ-007).

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- `extract_request_context` keeps its three-tuple contract because other code reads it; the new helper wraps it.
- The `run_http` seam for retry policies is the right place for the capability map: it runs before the posture gate and before any socket exists.
- `mcp_servers/execution_context.py` is imported at module top level here; it imports nothing from this module, so there is no cycle.

## Design decisions

- `extract_execution_context(request, tool, args)` reads the key, session, and request ids through `extract_request_context` and the `x-execution-mode` header, then delegates to `build_execution_context`.
- The keyless-POST middleware stays as it is: it already rejects every keyless side-effecting `POST /v1/call_tool`, previews included.

## Alternatives considered

Resolving the mode inside a middleware was rejected: the arguments are validated per tool after the body is parsed, and each server already owns that step.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
Add the request helper, change the base `dispatch` signature, and wire the capability seam.

### Method
- Add `extract_execution_context` (new) taking `(request, tool, args) -> ExecutionContext` next to `extract_request_context`; it raises `ExecutionContextError` for a header disagreement or a malformed `dry_run`.
- Change `MCPServer.dispatch(self, name, args)` to `dispatch(self, name, args, context=None)` with `context: ExecutionContext | None`.
- In `run_http`, import `configure_tool_preview_capabilities` with the existing lazy dispatcher import and call it with `getattr(self, "mcp_tools", ())` immediately after `configure_tool_retry_policies`.

### Details
- Update the class docstring sentence about overriding `dispatch()` to mention the optional context.
- Do not change `attach_auth_middleware`, `require_auth_token`, or `_read_call_tool_body`.

### Companion test files
- `tests/mcp_servers/test_mcp_server_base.py`
  - Procedure: Add cases: the base `dispatch` accepts and ignores a context and still raises `NotImplementedError`; extract_execution_context builds a context from request headers and state; `run_http` bootstrap configures the preview map (patch the configure function and assert the call).
  - Validation: `uv run pytest tests/mcp_servers/test_mcp_server_base.py`

## Compatibility considerations

Every subclass `dispatch` override is updated by its own server document in the same release unit; an override with the old signature would break at call time, so the units land together.

## Security considerations

The header cross-check prevents a client from labelling a real execution as a preview (or the reverse) against the arguments it sends.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/mcp_servers/test_mcp_server_base.py tests/mcp_servers/test_server_idempotency_boundary.py tests/mcp_servers/test_mcp_launcher.py`
- `uv run mypy scripts/mcp_servers/server.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- Servers can obtain a context with one call; the base `dispatch` accepts a context.
- Bootstrap injects the preview-capability map beside the retry policies.

## Out of Scope

- Server-specific edits (their own documents).
- Changing the keyless-POST middleware.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-002, REQ-006, REQ-007
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/mcp_servers/server.py`, `tests/mcp_servers/test_mcp_server_base.py`
