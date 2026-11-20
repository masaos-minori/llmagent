## Goal

Accept the execution context in `ToolExecutor.execute` and forward it to the invoker (`REQ-002` context propagation, AC-2).

## Scope
**Release unit**: contract-chain

## Assumptions
- `ToolExecutor` extends `ToolTransportInvoker` (class at :37, verified 2026-11-20; the document previously cited line 34); the invoker-side signature is row 15's change — the two signatures land in the same commit set.

## Design decisions
- Add a `context: ToolExecutionContext | None = None` parameter to `execute` (:97-114) and `_raw_execute` (:88-95) and pass it unchanged to the invoker call (`_run_precall_gates`, row 15 signature).
- Routing-failure results (`error_type="routing"`; the docstring contract is at :102-107, the build site at :110-114 — the previously cited ":30-33" refers to the `ToolCallResult` docstring in `transport_dto.py`) keep `context=None`/`dispatch_stage=""` semantics where no transport call happens.

## Alternatives considered
- Passing the context through a module-level argument object: rejected — an explicit parameter keeps mypy coverage of the propagation chain (AC-2 auditability).

## Implementation
### Target file
`scripts/shared/tool_executor.py`

### Procedure
Thread the `context` parameter through `ToolExecutor`'s execute delegation into the inherited invoker call.

### Method
Signature extension with a defaulted parameter; no routing logic changes.

### Details
- Update the module docstring (:6-12 region) to mention the context-carrying contract.

### Companion test files
- `tests/shared/test_tool_executor.py`
  - Procedure: add a case asserting the context given to `execute` reaches the invoker call unchanged.
  - Validation: `uv run pytest tests/shared/test_tool_executor.py` passes.

## Compatibility considerations
Existing callers that omit `context` keep the pre-change behavior until rows 4/16 require it for side effects (AC-3 enforcement lives in the transport gate).

## Security considerations
N/A: propagation only; no new data in this file.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/shared/test_tool_executor.py tests/shared/test_tool_executor_routing.py && uv run lint-imports`.

## Completion criteria
Every successful `ToolExecutor.execute` forwards the same `ToolExecutionContext` object it received to the transport layer.

## Out of Scope
Context definition (row 13); invoker/transport handling (rows 15-16).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | `context` param on `execute`/`_raw_execute`, forwarded to `_run_precall_gates`; routing errors keep context=None |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | companion pins added in tests/shared/test_tool_executor_routing.py (TestNoContextRefusalAtRoutingLayer) + test_tool_executor.py `_ctx` adaptation |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff+mypy(445 clean)+tests/shared (1280 passed)+lint-imports (6 kept); full suite at batch end |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-21 | 2026-11-21 | Docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/shared/tool_executor.py`, `tests/shared/test_tool_executor.py`
