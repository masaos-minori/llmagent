## Goal
Update all `request_approval()` calls in `tests/test_approval_ops.py` to supply `workflow_id`; add tests for `workflow_id` persistence and row-mapping population.

## Scope
**In**: `tests/test_approval_ops.py` (or equivalent) — update existing calls; add 3 new tests.
**Out**: Other approval_ops tests (status transition, stage_id); cmd_workflow tests (see test_cmd_workflow.py doc).

## Assumptions
- `request_approval(db, task_id)` calls exist without `workflow_id` — all must be updated.
- `ApprovalRecord.workflow_id` is populated after Plan 11 (req11) schema and ops changes.
- Tests use an in-memory SQLite or `tmp_path` SQLite with the approvals table schema.

## Implementation

**Target file**: `tests/test_approval_ops.py`

**Procedure**:
1. **Update existing `request_approval()` calls**:
   - `grep -n "request_approval(" tests/test_approval_ops.py` — find all
   - Add `workflow_id="wf-test-1"` to each call:
     ```python
     # Before:
     approval = request_approval(db, task_id="t-1", stage_id="execute")

     # After:
     approval = request_approval(db, task_id="t-1", workflow_id="wf-test-1", stage_id="execute")
     ```

2. **Add new tests**:
   ```python
   def test_request_approval_persists_workflow_id(db):
       approval = request_approval(db, task_id="t-1", workflow_id="wf-stored-1")
       row = db.fetchone("SELECT workflow_id FROM approvals WHERE approval_id=?", (approval.approval_id,))
       assert row["workflow_id"] == "wf-stored-1"

   def test_find_approval_by_id_populates_workflow_id(db):
       request_approval(db, task_id="t-1", workflow_id="wf-find-1")
       found = find_approval_by_id(db, approval_id=...)
       assert found.workflow_id == "wf-find-1"

   def test_approval_record_workflow_id_not_empty_after_creation(db):
       approval = request_approval(db, task_id="t-1", workflow_id="wf-nonempty-1")
       assert approval.workflow_id  # non-empty string
   ```

3. **Update `ApprovalRecord` construction** in tests that manually create records:
   - Add `workflow_id="wf-test-1"` to any `ApprovalRecord(...)` constructor call that omits it

**Method**: Call-site update + new test additions.

**Details**:
- `db` fixture must have the updated `approvals` schema including `workflow_id` column.
- If the test DB is set up by `create_workflow_schema()`, ensure it's the updated version (after Plan 11 adds the column).

## Validation plan
- `uv run pytest tests/test_approval_ops.py -x -q`
- `grep -n "request_approval(" tests/test_approval_ops.py | grep -v "workflow_id"` → 0

---
*Plan: 20260707-105307 (req11) Phase 7*
