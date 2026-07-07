## Goal
Remove ID-less approval tests from `tests/test_cmd_workflow.py`; add validation-error tests for `/approve` and `/reject` without explicit ID; add `approval.workflow_id` direct-access test.

## Scope
**In**: `tests/test_cmd_workflow.py` — remove count-1 ID-less tests; add explicit-ID required tests; add `_emit_approval_audit` uses `approval.workflow_id` test.
**Out**: Other workflow command tests (status, list, reject); approval_ops.py tests.

## Assumptions
- Tests named `test_approve_without_id_when_one_pending_succeeds`, `test_reject_without_id_autoselects` are removed.
- New tests assert validation error message contains "Approval ID required".
- `_emit_approval_audit()` now accepts `ApprovalRecord` directly (see cmd_workflow.py doc).

## Implementation

**Target file**: `tests/test_cmd_workflow.py`

**Procedure**:
1. **Remove**:
   - `test_approve_without_id_when_exactly_one_pending_succeeds`
   - `test_approve_uses_latest_pending_when_no_id_given`
   - `test_reject_without_id_when_exactly_one_pending_succeeds`
   - `test_reject_uses_latest_pending_when_no_id_given`
   - Any test that asserts ID-less approve/reject succeeds with count==1

2. **Add**:
   ```python
   def test_approve_without_id_returns_validation_error(cmd_handler):
       result = cmd_handler.approve(arg="")
       assert "Approval ID required" in result.message
       assert result.is_error

   def test_reject_without_id_returns_validation_error(cmd_handler):
       result = cmd_handler.reject(arg="")
       assert "Approval ID required" in result.message
       assert result.is_error

   def test_approve_with_valid_id_succeeds(cmd_handler, mock_store):
       approval = ApprovalRecord(approval_id="apr-1", task_id="t-1", workflow_id="wf-1", status="pending")
       mock_store.find_approval_by_id.return_value = approval
       result = cmd_handler.approve(arg="apr-1 looks good")
       assert not result.is_error

   def test_approve_with_unknown_id_returns_not_found(cmd_handler, mock_store):
       mock_store.find_approval_by_id.return_value = None
       result = cmd_handler.approve(arg="apr-unknown")
       assert "not found" in result.message.lower()

   def test_emit_approval_audit_uses_approval_workflow_id(cmd_handler, mocker):
       approval = ApprovalRecord(approval_id="apr-1", task_id="t-1", workflow_id="wf-direct-1", status="pending")
       audit_spy = mocker.patch.object(cmd_handler, "_emit_approval_audit")
       cmd_handler._cmd_approve(approval)
       # assert audit was called with approval object carrying workflow_id
       call_args = audit_spy.call_args
       assert call_args[0][0].workflow_id == "wf-direct-1"  # approval.workflow_id, not task join
   ```

3. **Update existing tests** that call `_emit_approval_audit(task_id, ...)`:
   - Update to `_emit_approval_audit(approval_record, ...)` with new signature

**Method**: Targeted test removal + new test additions.

## Validation plan
- `uv run pytest tests/test_cmd_workflow.py -x -q`
- `grep -n "without_id.*succeed\|latest_pending\|count.*1" tests/test_cmd_workflow.py` → 0

---
*Plans: 20260707-105306 (req10) Phase 5, 20260707-105307 (req11) Phase 7*
