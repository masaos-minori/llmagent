## Goal

Route this server's HTTP and programmatic entry points through the shared execution context (REQ-002, REQ-006), so both return the same structured result and a side-effecting programmatic call needs a key.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- `dispatch_tool` takes a context in place of `idempotency_key` after the dispatcher procedure (earlier `seq`), and `extract_execution_context` exists after the `server.py` procedure; this document runs after both within the release unit.
- The HTTP middleware already rejects a keyless side-effecting `POST /v1/call_tool`, so production HTTP behavior is unchanged; only the programmatic path gains the key rule.
- Existing tests that pass `idempotency_key=` to ``_dispatch_write_tool`` are Fallout and are updated with this change (Plan UNK-03); the named validation target is `tests/mcp_servers/file/test_file_write_mcp_service.py`.

## Design decisions

- The edit is mechanical: build the context once per request and pass it on; no tool behavior changes.
- Context-building errors are validation errors returned before dispatch, so a malformed `dry_run` never creates durable state.

## Alternatives considered

Keeping the wrapper's `idempotency_key` parameter and building the context inside it was rejected: the wrapper would then lose the request and session ids and the header cross-check.

## Implementation
### Target file
`scripts/mcp_servers/file/write_server.py`

### Procedure
Change the dispatch wrapper, the HTTP handler, and the programmatic override of `scripts/mcp_servers/file/write_server.py`.

### Method
- In ``_dispatch_write_tool`` replace the `idempotency_key: str | None = None` parameter with `context: ExecutionContext | None = None` and pass it to `dispatch_tool` as `context=context`.
- In the HTTP `call_tool` handler build the context once with `extract_execution_context(request, req.name, req.args)` (imported from `mcp_servers.server`); an `ExecutionContextError` returns `CallToolResponse(result=f"Validation error: {exc}", is_error=True)` before any dispatch.
- Keep `extract_request_context` for the audit ids; drop the now-unused `idempotency_key` local if nothing else reads it.
- In the programmatic `dispatch(self, name, args, context=None)` override pass `context` to the wrapper.
- Import `ExecutionContext` and `ExecutionContextError` from `mcp_servers.execution_context`.
- The write formatters emit `Dry-run: ...` text that the old marker scan never matched; no formatter text changes, because the mode no longer depends on it.

### Details
- Do not change authentication, posture gating, audit fields, or tool tables.
- A server tool table is not edited: preview capability is already declared per tool and is read at bootstrap.

## Compatibility considerations

The wrapper signature changes; every in-tree caller is in this file, and tests are updated as Fallout. HTTP wire behavior is unchanged apart from the two additive response fields.

## Security considerations

A malformed or contradictory execution-mode header is rejected before dispatch; keyless side-effecting programmatic calls are rejected by the dispatcher.

## Rollback considerations

Revert the release unit together with the dispatcher.

## Validation plan

- `uv run pytest tests/mcp_servers/file/test_file_write_mcp_service.py`
- `uv run mypy scripts/mcp_servers/file/write_server.py`
- `uv run ruff check` and `uv run ruff format`
- The cross-server contract test in `tests/mcp_servers/test_dry_run_contract.py` exercises this server's entry points.

## Completion criteria

- No `idempotency_key=` argument is passed to `dispatch_tool` from this file.
- HTTP `call_tool` and the programmatic `dispatch` both pass a context.

## Out of Scope

- Dispatcher behavior and the response model.
- Other servers (their own documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Update the existing tests that call the changed wrapper (found with `rg`) per Validation plan | Pending | — | — |  |
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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/mcp_servers/file/write_server.py`
