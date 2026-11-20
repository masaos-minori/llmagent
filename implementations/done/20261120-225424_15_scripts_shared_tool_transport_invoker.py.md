## Goal

Forward the execution context from the invoker to the transport and surface the dispatch-stage intent signal on the result (`REQ-002` propagation, `REQ-005` dispatch signal).

## Scope
**Release unit**: contract-chain

## Assumptions
- The intent-row writes themselves stay agent-side (`tool_runner`, row 4); the shared layer only carries the context and marks dispatch success/failure on the `ToolCallResult`.

## Design decisions
- Add `context: ToolExecutionContext | None = None` to the transport-invocation path in `ToolTransportInvoker` (class at :36, verified 2026-11-20; previously cited :35) — `invoke` (:341-350), `_run_precall_gates` (:285-339), `_invoke_and_record` (:269-283), `_execute_with_semaphore` (:258-267) — and pass it to `HttpTransport.call` (row 16 signature).
- Populate `ToolCallResult.context` and `dispatch_stage` (row 13 fields) on every result this layer builds, including transport-failure results — a post-send failure result carrying the context is the signal that leaves the row at `dispatched` (row 4/10, AC-6). Mechanism (resolved 2026-11-20): `TransportError` gains a `stage` attribute set at its raise sites in `http_transport.py` (row 16); `_record_transport_error` (:240-249) copies it onto the error result; every invoker-side `_error_result` (:146-166) site (health :168-227, disabled :306-312, lifecycle :314-320, missing transport :322-326) uses `dispatch_stage=""` because nothing was dispatched. Health/lifecycle/semaphore gate logic itself stays unchanged.

## Alternatives considered
- Writing the intent row from the shared layer: rejected — `shared` is a leaf (`.importlinter`) and cannot reach the agent-side recorder.

## Implementation
### Target file
`scripts/shared/tool_transport_invoker.py`

### Procedure
Extend the invoke signature and the internal `HttpTransport` call sites with `context`; set `context` on constructed `ToolCallResult` values.

### Method
Parameter threading plus result-field population; gate logic untouched (verified anchors: semaphore :100-140, health :168-227; the previously cited ":26-33" is the module's concurrency-constant region).

### Details
- Every invoker-built result carries the context (identity is known regardless of outcome). Verification note 2026-11-20: this layer has no cache-hit short-circuit path — cache hits exist server-side (`dispatch.py::_duplicate_cache`) only; the invoker-built results are the health-gate, disabled-server, lifecycle, and missing-transport error results plus the transport results from `HttpTransport.call`.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | `context` param on invoke/_run_precall_gates/_invoke_and_record/_execute_with_semaphore/_error_result/_check_health/_handle_lifecycle_error; `_record_transport_error` copies `e.stage` onto the result |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | new TestExecutionContextPropagation class in tests/shared/test_tool_transport_invoker.py; existing fake-transport signatures widened for the context kwarg |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff+mypy+tests/shared (1280 passed); full suite at batch end |
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
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/shared/tool_transport_invoker.py`, `tests/shared/test_tool_transport_invoker.py`
