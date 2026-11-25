## Goal

Route this read-only server's HTTP and programmatic entry points through the shared execution context (REQ-002) so both paths use one dispatcher signature and return the same metadata.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- `dispatch_tool` takes a context in place of `idempotency_key` after the dispatcher procedure (earlier `seq`), and `extract_execution_context` exists after the `server.py` procedure; this document runs after both within the release unit.
- The HTTP middleware already rejects a keyless side-effecting `POST /v1/call_tool`, so production HTTP behavior is unchanged; only the programmatic path gains the key rule. MDQ tools are read-only today (the key rule does not apply); the metadata still flows so the contract is uniform.
- Existing tests that pass `idempotency_key=` to ``_dispatch_mdq_tool`` are Fallout and are updated with this change (Plan UNK-03); the named validation target is `tests/mcp_servers/mdq/test_mdq_exception_handlers.py`.

## Design decisions

- The edit is mechanical: build the context once per request and pass it on; no tool behavior changes.
- Context-building errors are validation errors returned before dispatch, so a malformed `dry_run` never creates durable state.

## Alternatives considered

Keeping the wrapper's `idempotency_key` parameter and building the context inside it was rejected: the wrapper would then lose the request and session ids and the header cross-check.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure
Change the dispatch wrapper, the HTTP handler, and the programmatic override of `scripts/mcp_servers/mdq/mdq_server.py`.

### Method
- In ``_dispatch_mdq_tool`` replace the `idempotency_key: str | None = None` parameter with `context: ExecutionContext | None = None` and pass it to `dispatch_tool` as `context=context`.
- In the HTTP `call_tool` handler build the context once with `extract_execution_context(request, req.name, req.args)` (imported from `mcp_servers.server`); an `ExecutionContextError` returns `CallToolResponse(result=f"Validation error: {exc}", is_error=True)` before any dispatch.
- Keep `extract_request_context` for the audit ids; drop the now-unused `idempotency_key` local if nothing else reads it.
- In the programmatic `dispatch(self, name, args, context=None)` override pass `context` to the wrapper.
- Import `ExecutionContext` and `ExecutionContextError` from `mcp_servers.execution_context`.
- Extend `MdqDispatchResult` with `execution_mode: str = ""` and `side_effect_applied: bool = False`, copy both from the dispatcher result in `_dispatch_mdq_tool`, and rebuild the shared `DispatchResult` in `call_tool` and in `dispatch` with those two fields (today both rebuild it from `output` and `is_error` only, which drops `dedup_state` and would drop the new metadata).

### Details
- Do not change authentication, posture gating, audit fields, or tool tables.
- A server tool table is not edited: preview capability is already declared per tool and is read at bootstrap.

## Compatibility considerations

The wrapper signature changes; every in-tree caller is in this file, and tests are updated as Fallout. HTTP wire behavior is unchanged apart from the two additive response fields.

## Security considerations

N/A: read-only tools; the dispatcher accepts a keyless read-only call as before.

## Rollback considerations

Revert the release unit together with the dispatcher.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_exception_handlers.py`
- `uv run mypy scripts/mcp_servers/mdq/mdq_server.py`
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-173444 | 20261125-173444 | changed; MdqDispatchResult carries dedup_state as well as the two metadata fields so the rebuild no longer drops it; audit ids read from extract_request_context per Method; stale check clean |
| 2 | Update the existing tests that call the changed wrapper (found with `rg`) per Validation plan | Completed | 20261125-173444 | 20261125-173444 | no test call site passed idempotency_key=; 416 passed, 1 skipped |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-180342 | 20261125-180342 | — release unit R1-mode-contract: end-of-unit full-suite run pending; Step 5 N/A: docs work is the plan row docs/22_mcp/mcp_03_01_dispatch-and-routing.md end-of-batch full-suite run: 14369 passed, 4 skipped; diff-cover 92% (>=90) on changed lines; run_validation_gates.py passes |

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
- **Related target files**: `scripts/mcp_servers/mdq/mdq_server.py`