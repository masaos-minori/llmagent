## Goal

Make the web-search dispatch wrapper accept the shared execution context (REQ-002) so its callers use one dispatcher signature.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- `dispatch_tool` takes a context in place of `idempotency_key` after the dispatcher procedure (earlier `seq`), and `extract_execution_context` exists after the `server.py` procedure; this document runs after both within the release unit.
- The HTTP middleware already rejects a keyless side-effecting `POST /v1/call_tool`, so production HTTP behavior is unchanged; only the programmatic path gains the key rule. Web search tools are read-only.
- Existing tests that pass `idempotency_key=` to ``dispatch_web_tool`` are Fallout and are updated with this change (Plan UNK-03); the named validation target is `tests/mcp_servers/web_search/test_web_search_server.py`.

## Design decisions

- The edit is mechanical: build the context once per request and pass it on; no tool behavior changes.
- Context-building errors are validation errors returned before dispatch, so a malformed `dry_run` never creates durable state.

## Alternatives considered

Keeping the wrapper's `idempotency_key` parameter and building the context inside it was rejected: the wrapper would then lose the request and session ids and the header cross-check.

## Implementation
### Target file
`scripts/mcp_servers/web_search/formatters.py`

### Procedure
Change the signature and the `dispatch_tool` call of `dispatch_web_tool`.

### Method
- In `dispatch_web_tool` replace the `idempotency_key: str | None = None` parameter with `context: ExecutionContext | None = None` and pass `context=context` to `dispatch_tool`.
- Import `ExecutionContext` from `mcp_servers.execution_context`.
- Update the function docstring: the context carries the key and the mode.

### Details
- Do not change the dispatch table or the fetch and search handlers.

## Compatibility considerations

The wrapper signature changes; every in-tree caller is in this file, and tests are updated as Fallout. HTTP wire behavior is unchanged apart from the two additive response fields.

## Security considerations

N/A: read-only tools; the dispatcher accepts a keyless read-only call as before.

## Rollback considerations

Revert the release unit together with the dispatcher.

## Validation plan

- `uv run pytest tests/mcp_servers/web_search/test_web_search_server.py`
- `uv run mypy scripts/mcp_servers/web_search/formatters.py`
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/mcp_servers/web_search/formatters.py`
