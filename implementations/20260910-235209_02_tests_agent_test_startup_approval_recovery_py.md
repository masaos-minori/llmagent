# Port 9 approval-recovery scenarios to `tests/agent/test_startup_approval_recovery.py`

## Goal

Port all 9 test methods from `TestStartupOrchestratorRecoverPendingApprovals` in `tests/agent/test_startup.py` to `tests/agent/test_startup_approval_recovery.py`, correcting mock patch targets from `agent.startup.*` to `agent.workflow.approval_ops.*` / `agent.workflow.state_store.*` to match where `ApprovalRecovery.recover()` actually imports them.

## Scope

- Append 9 new test methods to `tests/agent/test_startup_approval_recovery.py`:
  1. `test_startup_recovery_restores_pending_approval`
  2. `test_startup_recovery_shows_last_of_multiple_pending_approvals`
  3. `test_startup_recovery_selects_newest_not_oldest_pending_approval` (regression guard)
  4. `test_startup_recovery_warning_contains_task_and_approval_id`
  5. `test_startup_recovery_warns_on_pending_approval_task_id_overwrite`
  6. `test_startup_recovery_no_warning_when_task_id_not_already_set`
  7. `test_startup_recovery_no_pending_approval`
  8. `test_recover_pending_approvals_against_real_db_no_attribute_error`
  9. `test_recover_pending_approvals_store_closed_on_exception`
- For each test, change `mock.patch("agent.startup.find_all_pending_approvals", ...)` to `mock.patch("agent.workflow.approval_ops.find_all_pending_approvals", ...)` and `mock.patch("agent.startup.StateStore", ...)` to `mock.patch("agent.workflow.state_store.StateStore", ...)`.

## Assumptions

- `ApprovalRecovery.recover()` uses local imports from `agent.workflow.approval_ops` and `agent.workflow.state_store` (confirmed in `startup_approval_recovery.py` lines 32-33).
- `find_all_pending_approvals(db: SQLiteHelper) -> list[tuple[str, ApprovalRecord]]` — the mock's return value must be compatible with this signature.
- `StateStore` has a constructor that accepts a database connection via `get_connection()`.
- The existing 16 tests in `test_startup_approval_recovery.py` remain unaffected by adding the 9 new tests.

## Design decisions

- Create a new test class `TestStartupOrchestratorRecoverPendingApprovals` in `test_startup_approval_recovery.py` to mirror the original class name, making it clear these are ported tests.
- Use `agent.workflow.approval_ops.find_all_pending_approvals` and `agent.workflow.state_store.StateStore` as mock patch targets instead of `agent.startup.*`, since those are the actual import locations in `ApprovalRecovery.recover()`.
- Preserve the exact assertion logic from each original test; only the mock patch targets change.
- For `test_recover_pending_approvals_against_real_db_no_attribute_error`, keep the real-database approach but ensure the mock patches target the correct modules.

## Alternatives considered

- Renaming the class to avoid confusion with the old orphaned class: rejected because keeping the same name makes it obvious these are ported tests and helps traceability.
- Adding a docstring to each ported test noting the original test name: rejected because the test names themselves are identical, providing sufficient traceability.

## Compatibility considerations

- These tests exercise `StartupOrchestrator._recover_pending_approvals()` which delegates to `self._approval_recovery.recover()`.
- The `_make_startup()` helper already exists in `test_startup_approval_recovery.py` and can be reused.
- `ApprovalRecord` type may need to be imported if not already available.

## Security considerations

- No security surface change. This is a test-only addition.

## Rollback considerations

- Reverting means removing the appended test methods from `test_startup_approval_recovery.py`.

## Validation plan

- Run `uv run pytest tests/agent/test_startup_approval_recovery.py -q` and confirm all tests pass (original + ported).
- Run `uv run pytest tests/agent/test_startup.py -q` and confirm no AttributeError for `find_all_pending_approvals`/`StateStore`.

## Completion criteria

- All 9 test methods exist in `tests/agent/test_startup_approval_recovery.py`.
- Mock patch targets use `agent.workflow.approval_ops.find_all_pending_approvals` and `agent.workflow.state_store.StateStore`.
- `uv run pytest tests/agent/test_startup_approval_recovery.py -q` passes fully.

## Out of scope

- Deleting `TestStartupOrchestratorRecoverPendingApprovals` from `test_startup.py` (handled separately).
- Modifying `scripts/agent/startup.py` or `scripts/agent/startup_approval_recovery.py`.
- Fixing the ~36 unrelated pre-existing failures in `test_startup.py`.

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Port test_startup_recovery_restores_pending_approval | Completed | 20260911-14:38 | 20260911-14:38 | Mock targets corrected |
| 2 | Port test_startup_recovery_shows_last_of_multiple_pending_approvals | Completed | 20260911-14:38 | 20260911-14:38 | |
| 3 | Port test_startup_recovery_selects_newest_not_oldest_pending_approval | Completed | 20260911-14:38 | 20260911-14:38 | Regression guard |
| 4 | Port test_startup_recovery_warning_contains_task_and_approval_id | Completed | 20260911-14:38 | 20260911-14:38 | |
| 5 | Port test_startup_recovery_warns_on_pending_approval_task_id_overwrite | Completed | 20260911-14:38 | 20260911-14:38 | Logger mock path fixed |
| 6 | Port test_startup_recovery_no_warning_when_task_id_not_already_set | Completed | 20260911-14:38 | 20260911-14:38 | Logger mock path fixed |
| 7 | Port test_startup_recovery_no_pending_approval | Completed | 20260911-14:38 | 20260911-14:38 | |
| 8 | Port test_recover_pending_approvals_against_real_db_no_attribute_error | Completed | 20260911-14:38 | 20260911-14:38 | eventbus_db_path added |
| 9 | Port test_recover_pending_approvals_store_closed_on_exception | Completed | 20260911-14:38 | 20260911-14:38 | |
| 10 | Verify pytest passes | Completed | 20260911-14:38 | 20260911-14:38 | All 25 tests pass |

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
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: issues/20260909-105724_startup02_recover-pending-approvals-test-targets-removed-module-attribute.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-192919_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-235209
- **Related target files**: tests/agent/test_startup_approval_recovery.py
