## Goal

Forward the execution context from the invoker to the transport and surface the dispatch-stage intent signal on the result (`REQ-002` propagation, `REQ-005` dispatch signal).

## Scope
**Release unit**: contract-chain

## Assumptions
- The intent-row writes themselves stay agent-side (`tool_runner`, row 4); the shared layer only carries the context and marks dispatch success/failure on the `ToolCallResult`.

## Design decisions
- Add `context: ToolExecutionContext | None = None` to the transport-invocation path in `ToolTransportInvoker` (class at :35, transport call in the MCP-invoke method) and pass it to `HttpTransport`'s call (row 16 signature).
- Populate `ToolCallResult.context` (:44 region, row 13 field) on every result this layer builds, including transport-failure results — a post-send failure result carrying the context is the signal that leaves the row at `dispatched` (row 4/10, AC-6).

## Alternatives considered
- Writing the intent row from the shared layer: rejected — `shared` is a leaf (`.importlinter`) and cannot reach the agent-side recorder.

## Implementation
### Target file
`scripts/shared/tool_transport_invoker.py`

### Procedure
Extend the invoke signature and the internal `HttpTransport` call sites with `context`; set `context` on constructed `ToolCallResult` values.

### Method
Parameter threading plus result-field population; health/lifecycle/semaphore logic (:26-33 region) untouched.

### Details
- Cache-hit and circuit-open short-circuit results carry the context too (identity is known regardless of transport outcome).

### Companion test files
- `tests/shared/test_tool_transport_invoker.py`
  - Procedure: assert the context reaches the transport mock and lands on returned results, including failure paths.
  - Validation: `uv run pytest tests/shared/test_tool_transport_invoker.py` passes.

## Compatibility considerations
Defaulted parameter keeps existing call sites compiling until rows 4/14 pass the context.

## Security considerations
N/A: propagation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/shared/test_tool_transport_invoker.py && uv run lint-imports`.

## Completion criteria
Every result returned through the invoker chain carries the call's `ToolExecutionContext`; the transport receives it verbatim.

## Out of Scope
Header semantics (row 16); intent-row state machine (rows 4, 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/shared/tool_transport_invoker.py`, `tests/shared/test_tool_transport_invoker.py`
