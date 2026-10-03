# Unify duplicated MCP transport gate chain between live and test-only paths

## Priority
Medium

## Summary
`ToolExecutor._raw_execute()` (the production invocation path) and `ToolTransportInvoker.invoke()` (called only from tests) implement nearly identical health/lifecycle/transport gate chains as independent copies. Unify them onto a single private helper so the live path cannot silently diverge from the tested one.

## Background
MCP tool calls reach the network through `shared/tool_executor.py::ToolExecutor._raw_execute()`, which runs a gate chain (`_check_health` -> `_ensure_lifecycle_ready` -> transport resolution -> semaphore -> `_invoke_and_record`). The base class `shared/tool_transport_invoker.py::ToolTransportInvoker` also defines a public `invoke()` method that repeats the same gates (`_check_health` -> disabled-server check -> lifecycle -> transport resolution -> semaphore -> `_invoke_and_record`). A repository-wide search shows `invoke()` is referenced only inside `tests/shared/` and never from `scripts/`.

## Problem
Two independent but near-identical gate implementations exist for the same trust boundary. The rich test suite (health HALF_OPEN trial, unavailable->error-result, lifecycle failure, semaphore recording) exercises `invoke()`, while the live `_raw_execute()` path is exercised by fewer, thinner tests. If a guard is added to one copy and forgotten in the other, the divergence is invisible to CI because the two methods are validated separately.

## Reason for Change
The duplication is a latent correctness/maintainability risk at the one place where every MCP call is gated before hitting the network. A gap introduced into the live `_raw_execute()` path would not be caught by `invoke()`'s test coverage, and vice versa.

## Implementation Intent
Extract the shared gating steps into a single private helper on `ToolTransportInvoker` and have both `invoke()` and `ToolExecutor._raw_execute()` delegate to it. Preserve exact current behavior: gate order, HALF_OPEN trial dispatch, disabled-server rejection, lifecycle error normalization, transport-missing error result, and per-server-key semaphore application. Do not change which errors become `ToolCallResult` vs which propagate as exceptions.

## Target Files or Areas
- `scripts/shared/tool_transport_invoker.py`
- `scripts/shared/tool_executor.py`
- `tests/shared/test_tool_transport_invoker*.py`
- `tests/shared/test_tool_executor*.py`

## Required Changes
- Introduce one private gate helper (for example `_run_precall_gates`) that returns the first `ToolCallResult` error encountered, or `None` when all gates pass.
- Route both `ToolTransportInvoker.invoke()` and `ToolExecutor._raw_execute()` through that helper, keeping the async lifecycle await in the same relative position today.
- Remove the duplicated inline gate blocks from both callers.
- Keep `invoke()` callable (it is used by existing tests); do not delete the public method.

## Constraints
- Behavior-preserving refactor only. No change to public contracts, error types, log messages, or gate ordering.
- Must remain compatible with `asyncio.Semaphore` creation semantics and the existing `_invoke_and_record` recording contract.
- Do not alter the health registry or lifecycle protocol interfaces.

## Acceptance Criteria
- Both `invoke()` and `_raw_execute()` resolve through the single shared helper; no remaining duplicate gate block.
- Existing behavior for each gate outcome (healthy, HALF_OPEN trial, unavailable, disabled, lifecycle-failed, transport-missing) is unchanged.
- Full existing test suite for both modules passes without modification of expected outcomes.
- `ruff`, `mypy`, and `bandit` remain clean on touched files.

## Testing Expectations
- Run the existing `tests/shared/test_tool_transport_invoker*.py` and `tests/shared/test_tool_executor*.py` suites and confirm they still pass unmodified.
- Add a characterization test asserting that `invoke()` and `_raw_execute()` produce identical results for a representative healthy call and a representative failed call (same `ToolCallResult`, same `server_key`, same `error_type`).
- Confirm `ruff check` / `mypy` / `bandit` pass on the touched files.

## Documentation Impact
None required. If `docs/` describes the invocation gate order, verify it still matches after unification; update only if it drifts.

## Out of Scope
- Any change to the gating policy itself (which conditions are fatal/warning, health states, lifecycle contract).
- Adding new gates or changing retry/timeout behavior.
- Refactoring unrelated methods in these modules.

## Dependencies
- N/A: none

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
This is a behavior-preserving refactor. Extract the shared pre-call gates into one private helper on `ToolTransportInvoker` and make both `invoke()` and `ToolExecutor._raw_execute()` delegate to it. Do NOT change gate order, error classification, log output, or public signatures. Lock behavior with a characterization test comparing `invoke()` and `_raw_execute()` before editing. Stop and report if the two methods currently differ in any observable way you cannot reconcile.

## Traceability
- **Workflow phase**: python-code-review via issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-154614
- **Related target files**: scripts/shared/tool_transport_invoker.py, scripts/shared/tool_executor.py
