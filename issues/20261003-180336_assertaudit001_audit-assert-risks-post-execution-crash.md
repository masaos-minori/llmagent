# Audit assert risks post-execution crash

## Priority
Medium

## Summary
`audit_tool_exec()`, `audit_approval()`, and `log_approval_decision()` in `scripts/agent/tool_audit.py` each guard a precondition with a bare `assert ctx.workflow.workflow_id, ...` instead of an explicit exception. This violates the project's own rule against using `assert` for business-logic preconditions, is stripped entirely under `python -O`, and — if the current universal per-turn workflow-wrapping invariant it depends on is ever removed — would raise an uncaught `AssertionError` after a tool has already executed (and possibly produced real side effects).

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's tool-execution/audit subsystem (`scripts/agent/tool_audit.py`), cross-checked against this project's Pythonic safety constraint: "Never use `except Exception`... Use explicit exceptions instead of `assert` in business logic."

## Problem
`audit_tool_exec()`, `audit_approval()`, and `log_approval_decision()` (`scripts/agent/tool_audit.py`) each contain:
```python
assert ctx.workflow.workflow_id, "workflow_id required: ... called outside workflow context"
```
`ctx.workflow.workflow_id` defaults to `None` (`scripts/agent/context.py`, `WorkflowState.workflow_id: str | None = None`) and is only set while a workflow task is active. Tracing the call chain confirms `scripts/agent/workflow_engine_adapter.py::execute_turn()` wraps every REPL turn (plain chat included) in `_init_workflow_task()`/`_activate_workflow()` before any tool executes, so the assert's precondition currently always holds in practice and is never exercised as failing — `tests/agent/test_tool_runner.py::_make_ctx()` also hardcodes a non-empty `workflow_id` for all test cases, so the failing path is untested.

## Reason for Change
An `assert` (a) is stripped entirely under `python -O`, silently allowing an empty `workflow_id` into a persisted audit event instead of rejecting it, and (b) would raise an uncaught `AssertionError` **after** a tool has already executed (and possibly produced real side effects) if this per-turn workflow-wrapping invariant is ever removed or bypassed by a future refactor — aborting the batch mid-flight with no audit record for that call and leaving sibling results in the same `asyncio.gather` batch uncollected. This is fragile, undocumented coupling between `tool_audit.py`'s invariant and `workflow_engine_adapter.py`'s universal-wrapping behavior.

## Implementation Intent
Replace each `assert` with an explicit, handled error condition: if the caller cannot meaningfully produce an audit record without a `workflow_id`, log a clear warning and skip (rather than silently proceeding or crashing), making the failure mode deliberate rather than an `AssertionError` surfacing post-execution.

## Target Files or Areas
- `scripts/agent/tool_audit.py` (`audit_tool_exec()`, `audit_approval()`, `log_approval_decision()`)

## Required Changes
- Replace each `assert ctx.workflow.workflow_id, ...` with an explicit check that raises a project-appropriate exception or logs-and-skips (decide based on whether a missing `workflow_id` should ever be tolerated at these call sites — if it should never happen, raise explicitly rather than assert).
- Add a test exercising each of the three functions with `ctx.workflow.workflow_id = None`, asserting the new explicit handling (not an `AssertionError`, and not a silent `-O`-stripped no-op).

## Constraints
- Do not change the functions' behavior when `workflow_id` is present (the common, currently-exercised path).
- Do not alter `workflow_engine_adapter.py`'s per-turn wrapping behavior as part of this fix — that invariant is out of scope here.

## Acceptance Criteria
- None of the three functions relies on `assert` for this precondition.
- A missing `workflow_id` produces a deliberate, documented failure mode (explicit exception or logged skip), not a raw `AssertionError`, and is not silently bypassed under `python -O`.

## Testing Expectations
Unit tests for each of the three functions with `workflow_id = None`, asserting the new explicit behavior. Run `tests/agent/test_tool_audit.py` after the change.

## Documentation Impact
N/A: no operator-facing documentation describes this precondition today; this is an internal robustness fix.

## Out of Scope
- `workflow_engine_adapter.py`'s per-turn workflow-wrapping invariant itself (not changed, only relied upon less fragile-ly).
- The audit-record content/schema beyond this precondition handling.

## Dependencies
N/A: none. Note: `log_approval_decision` has no caller under `scripts/` (only tests call it), so it may be dead code; decide whether that function needs the fix or should be removed. `audit_tool_exec` also gains a denial path in `issues/20261003-180330_toolaudit001_audit-drops-denied-gateway-tool-calls.md`, which reaches this assert.

## Unresolved Questions
N/A: none for the fix itself — whether a missing `workflow_id` should raise vs. log-and-skip is a design choice to make during implementation based on whether any legitimate call path can reach these functions outside a workflow context today (current evidence says no, but the fix should not assume that remains true).

## AI Implementation Instruction
Replace each `assert` with an explicit `if not ctx.workflow.workflow_id: ...` branch; choose raise-vs-skip based on whether failing loudly or logging-and-continuing better serves the audit trail's purpose (prefer raising, since a missing `workflow_id` here indicates an invariant violation that merits attention, not routine operation). Do not touch the per-turn workflow-wrapping logic in `workflow_engine_adapter.py`. Add the regression tests described above before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180336
- **Related target files**: scripts/agent/tool_audit.py, scripts/agent/context.py, scripts/agent/workflow_engine_adapter.py
