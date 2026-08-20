# Implementation Procedure: Fix AttributeError on sqlite3.Row.get() in find_all_pending_approvals

## Goal
Eliminate the unconditional `AttributeError: 'sqlite3.Row' object has no attribute 'get'` raised by `find_all_pending_approvals()` in `scripts/agent/workflow/approval_ops.py` whenever a pending approval gate exists from a previous session, so that `StartupOrchestrator._recover_pending_approvals()` — and therefore agent startup as a whole — no longer fails in this scenario.

## Goal
Eliminate the unconditional `AttributeError: 'sqlite3.Row' object has no attribute 'get'` raised by `find_all_pending_approvals()` in `scripts/agent/workflow/approval_ops.py` whenever a pending approval gate exists from a previous session, so that `StartupOrchestrator._recover_pending_approvals()` — and therefore agent startup as a whole — no longer fails in this scenario.

## Scope
- Target files:
  - `scripts/agent/workflow/approval_ops.py` - Fix the unsafe `r.get("expires_at")` access
  - `tests/agent/workflow/test_approval_ops.py` - Add unit test for `find_all_pending_approvals()`
  - `tests/agent/test_startup.py` - Add integration test for `_recover_pending_approvals()`

## Assumptions
- `StateStore.__init__()` always opens its connection with `row_factory=True` (`scripts/agent/workflow/state_store.py:31`), so every row reaching `find_all_pending_approvals()` is a `sqlite3.Row`
- `sqlite3.Row` has no `.get()` method in Python 3.13 (project targets py313 per `rules/coding.md`)
- The existing codebase convention for optional `sqlite3.Row` key access is `"key" in r.keys()` (used at `approval_ops.py:28` for `workflow_id`), not `dict(r).get(...)`
- No behavioral change to returned `ApprovalRecord.expires_at` value intended

## Design decisions
- Replace `r.get("expires_at")` with `r["expires_at"] if "expires_at" in r.keys() else None`
- This follows the existing pattern in `_approval_from_row()` at line 28 (`"workflow_id" in r.keys()`)
- `sqlite3.Row.__getitem__` returns Python `None` for SQL `NULL` values, so `NULL` case is handled correctly
- The `"expires_at"` key is always present in `r.keys()` because the SQL query explicitly selects `a.expires_at` (column is nullable but always present in result set)

## Implementation steps

### Phase 1: Core fix
1. In `scripts/agent/workflow/approval_ops.py` line 201, replace:
   ```python
   _approval_from_row(r, status="pending", expires_at=r.get("expires_at")),
   ```
   with:
   ```python
   _approval_from_row(
       r,
       status="pending",
       expires_at=r["expires_at"] if "expires_at" in r.keys() else None,
   ),
   ```

### Phase 2: Unit test
1. In `tests/agent/workflow/test_approval_ops.py`, add `class TestFindAllPendingApprovals` using existing `store` fixture:
   - Create a task via `_make_task(store._db)` (sets `status='pending_approval'`)
   - Call `request_approval(store._db, task_id=task.task_id, workflow_id="wf-test-1")`
   - Call `find_all_pending_approvals(store._db)` directly (not mocked)
   - Assert: returns exactly one `(task_id, ApprovalRecord)` tuple, `approval.status == "pending"`, no `AttributeError`
   - Add second test inserting two pending approvals, asserting both returned ordered by `created_at DESC`

### Phase 3: Integration test
1. In `tests/agent/test_startup.py`, add test to `TestStartupOrchestratorRecoverPendingApprovals`:
   - Do NOT patch `agent.startup.find_all_pending_approvals`
   - Patch `db.helper.build_db_config` to temp-path `DbConfig` (same pattern as `test_approval_ops.py::workflow_db`)
   - Call `create_workflow_schema()`, create task + `request_approval()` via real `agent.workflow.task_ops` / `agent.workflow.approval_ops`
   - Construct real `StartupOrchestrator(ctx, view)` with `MagicMock` `ctx`/`view`
   - Call `await startup._recover_pending_approvals()`
   - Assert: completes without raising, `ctx.workflow.approval_pending is True`, `ctx.turn.pending_approval_id` / `ctx.turn.pending_approval_task_id` set correctly

## Validation plan
- `uv run pytest tests/agent/workflow/test_approval_ops.py -v` — all existing + new tests pass
- `uv run pytest tests/agent/test_startup.py -v -k RecoverPendingApprovals` — new integration test passes
- `uv run pytest -v` — no regressions
- `uv run ruff format scripts/ tests/ && uv run ruff check scripts/ tests/` — clean
- `uv run mypy scripts/` — no new errors
- `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — ≥90% on changed lines

## Traceability
- Source requirement: requires/done/20260818-224751_require.md
- Source plan: plans/20260819-183904_plan.md
- Target files: scripts/agent/workflow/approval_ops.py, tests/agent/workflow/test_approval_ops.py, tests/agent/test_startup.py