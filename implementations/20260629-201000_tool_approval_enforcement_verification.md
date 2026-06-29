# Implementation Design: Tool Approval Enforcement in execute_all_tool_calls()

## Goal

Confirm that mandatory tool approval checks are enforced inside `execute_all_tool_calls()` so that write, delete, shell, and GitHub write tools cannot execute without passing `run_approval_checks()`.

## Scope

- **In-Scope**:
  - Verification of existing approval gate integration in `tool_runner.py`
  - Verification of `run_approval_checks()` and plan-mode/gitops blocks in `tool_approval.py`
  - Verification that `llm_turn_runner.py` has no bypass path
  - Review of existing test coverage

## Investigation Result

**All required changes are already implemented.** No code changes needed.

### Approval Gate Integration (COMPLETE)
- `_run_approval_gate()` at line 471 of `tool_runner.py` — validates tool calls before execution
- `_build_denied_messages()` at line 490 of `tool_runner.py` — produces tool role history entries for denied calls
- Integrated into `execute_all_tool_calls()` at lines 454, 465

### Approval Logic (COMPLETE)
- `run_approval_checks()` in `tool_approval.py` handles plan-mode blocking (`plan_blocked_tools`)
- `check_approval()` handles `gitops_push_blocked` for GitHub write tools
- `skip_in_workflow_mode` flag preserves workflow-level approval separation
- `audit_approval()` emits audit events for all decisions

### Test Coverage (COMPLETE)
- `test_write_tool_requires_approval_without_gateway` — line 337 of test_tool_runner.py
- `test_denied_tool_call_is_returned_as_tool_message` — line 365
- `test_plan_mode_blocked_tool_is_not_executed` — line 394
- `test_execute_all_tool_calls_does_not_bypass_approval` — line 419
- `test_all_calls_execute_without_gateway` updated to patch `run_approval_checks` — line 303

### Remaining Actions
- UNK-01: `ctx.workflow.approval_pending` attribute presence is guarded by `getattr` with default `False` — acceptable pattern, no typing guarantee needed
- UNK-02: `llm_turn_runner.py` calls `execute_all_tool_calls()` at line 92 with no bypass — confirmed

## Acceptance Criteria

- [x] Approval gate runs before DAG or standard execution
- [x] Denied tool calls returned as tool messages in history
- [x] Plan-mode blocked tools not executed
- [x] No bypass path in `llm_turn_runner.py`
- [x] All 21 tests in test_tool_runner.py pass
- [x] All 88 tests in approval test files pass
