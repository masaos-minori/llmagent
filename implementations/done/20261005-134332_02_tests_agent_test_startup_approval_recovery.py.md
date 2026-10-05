## Goal

Bring `tests/agent/test_startup_approval_recovery.py` into agreement with the gated recovery behavior: fix the failing overwrite-warning test (which asserts REQ-001-inconsistent behavior) and add regression coverage for `REQ-002` (skip active) and `REQ-003` (overwrite stale/idempotent).

## Scope

**In**:
- Modify `tests/agent/test_startup_approval_recovery.py` only: rewrite the failing test in `TestStartupOrchestratorRecoverPendingApprovals` and append one new `REQ-003` test.

**Out**:
- No source change to `scripts/agent/startup_approval_recovery.py` — that is the paired doc `20261005-134332_01_scripts_agent_startup_approval_recovery.py.md`. The new/rewritten tests assert behavior implemented there.
- No changes to unrelated test classes (`TestStartupOrchestratorStartServers`, `TestStartupVerifyMcpHealth`).

## Assumptions

1. The recovery module gates the overwrite (paired doc applied): differing current value → keep + log "Keeping existing"; `None` or equal → set (+ "Overwriting" when equal). This doc assumes that change exists; running these tests before it produces false failures.
2. `_recover_pending_approvals()` delegates to `ApprovalRecovery.recover()`, so patching `agent.workflow.approval_ops.find_all_pending_approvals` and `agent.workflow.state_store.StateStore` exercises the gated path (confirmed via Read of `scripts/agent/startup.py:138-140`).
3. `ctx.turn` is a `MagicMock`; setting `ctx.turn.pending_approval_task_id` then asserting its value reads back the assigned value (matches every existing test in this class).

## Design decisions

- **Rename the failing test to describe correct behavior.** The current name `test_startup_recovery_warns_on_pending_approval_task_id_overwrite` asserts that recovery warns on *overwrite*, but `REQ-001` requires it to *keep* the active value when they differ. Renaming to `test_startup_recovery_keeps_existing_pending_approval_task_id` keeps intent honest.
- **Flip assertions to the gated outcome.** The rewritten test sets an existing `"task-old"` and recovers `"task-456"` (differ); it now asserts the value stays `"task-old"` and a "Keeping existing ..." warning is logged exactly once.
- **Add one explicit `REQ-003` case.** The `None`/stale overwrite branch is already covered by passing tests (`test_startup_recovery_restores_pending_approval`, `test_startup_recovery_no_warning_when_task_id_not_already_set`, `test_recover_pending_approvals_against_real_db_no_attribute_error`). Add the second overwrite branch — current value *equals* the recovered value (idempotent set) — which is not yet asserted.
- **Mirror existing style.** Each test uses the same `MagicMock` ctx/view, `patch(...)` context, and `call_args[0][0]` warning-filter pattern already used in this class; no new imports required.

## Alternatives considered

- **Keep the original test name and only flip assertions.** Rejected: the name would misdescribe the (now-correct) keep behavior.
- **Delete the failing test and add two fresh tests.** Rejected: unnecessary deletion loses the regression history the name recorded; rename preserves it while correcting the assertion.
- **Add a separate `None`-case `REQ-003` test.** Rejected: redundant with three existing passing tests covering that exact branch.

## Implementation

### Target file

- `tests/agent/test_startup_approval_recovery.py`

### Procedure

1. Open `tests/agent/test_startup_approval_recovery.py`, locate `TestStartupOrchestratorRecoverPendingApprovals`.
2. Find the failing method `test_startup_recovery_warns_on_pending_approval_task_id_overwrite` (currently ~line 617) and replace it with the rewritten `REQ-002` test below (rename + flipped assertions).
3. Append the new `REQ-003` idempotent-overwrite test after it (same indentation/class body).
4. Run the recover class; confirm all 10 tests pass.
5. Run lint/typecheck/import-lint per `rules/toolchain.md`.

### Method

Replace the single failing method's body with an assertion of the gated "keep" outcome, then add a second method asserting the idempotent "overwrite-equal" outcome. Both follow the established fixture/patch/assert pattern in the class.

### Details

```python
# Replace the failing method
#   test_startup_recovery_warns_on_pending_approval_task_id_overwrite
# (asserts overwrite-on-differ, i.e. REQ-001-inconsistent) with:

    @pytest.mark.asyncio
    async def test_startup_recovery_keeps_existing_pending_approval_task_id(
        self,
    ) -> None:
        """REQ-002: Recovery keeps an active pending_approval_task_id instead of
        overwriting it when the recovered value differs."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        ctx.workflow.approval_pending = False
        ctx.turn = MagicMock()
        ctx.turn.pending_approval_id = None
        ctx.turn.pending_approval_task_id = "task-old"
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        approval = MagicMock()
        approval.approval_id = "approval-123"
        approval.reason = "waiting for deploy"

        mock_store = MagicMock()

        with (
            patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                return_value=[("task-456", approval)],
            ),
            patch("agent.workflow.state_store.StateStore", return_value=mock_store),
        ):
            with patch("shared.logger.Logger") as mock_logger:
                await startup._recover_pending_approvals()

        assert ctx.turn.pending_approval_task_id == "task-old"
        keep_calls = [
            call_args
            for call_args in mock_logger.return_value.warning.call_args_list
            if "Keeping existing pending_approval_task_id" in call_args[0][0]
        ]
        assert len(keep_calls) == 1
        assert keep_calls[0][0][1] == "task-old"
        assert keep_calls[0][0][2] == "task-456"


# Append this REQ-003 test to the same class:

    @pytest.mark.asyncio
    async def test_startup_recovery_overwrites_when_current_equals_recovered(
        self,
    ) -> None:
        """REQ-003: Recovery overwrites when the current value equals the recovered
        value (idempotent set); logs the Overwriting warning."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        ctx.workflow.approval_pending = False
        ctx.turn = MagicMock()
        ctx.turn.pending_approval_id = None
        ctx.turn.pending_approval_task_id = "task-456"
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        approval = MagicMock()
        approval.approval_id = "approval-123"
        approval.reason = "waiting for deploy"

        mock_store = MagicMock()

        with (
            patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                return_value=[("task-456", approval)],
            ),
            patch("agent.workflow.state_store.StateStore", return_value=mock_store),
        ):
            with patch("shared.logger.Logger") as mock_logger:
                await startup._recover_pending_approvals()

        assert ctx.turn.pending_approval_task_id == "task-456"
        overwrite_calls = [
            call_args
            for call_args in mock_logger.return_value.warning.call_args_list
            if "Overwriting pending_approval_task_id" in call_args[0][0]
        ]
        assert len(overwrite_calls) == 1
        assert overwrite_calls[0][0][1] == "task-456"
        assert overwrite_calls[0][0][2] == "task-456"
```

Note: the idempotent case logs "Overwriting pending_approval_task_id task-456 with task-456" because the recovery module's equal-value branch emits the "Overwriting" message (preserved from the existing scaffold); this matches the plan design ("only overwrite if current is None or identical to recovered").

## Compatibility considerations

- Test-only change; no production code touched directly here.
- Only affects `TestStartupOrchestratorRecoverPendingApprovals`. The previously-failing test is replaced (not left failing); other methods in the class are untouched and remain valid under the gated behavior.
- Cross-file dependency: these assertions require the paired source doc's line-66 gate. Implement that first, else these two tests fail spuriously.

## Security considerations

- No security impact: this is behavioral regression coverage for state-wiring correctness, not authz.

## Rollback considerations

- Test-only change: revert with `git checkout -- tests/agent/test_startup_approval_recovery.py`. No config/migration/deploy impact.

## Validation plan

| Check | Tool | Target | Expected |
|---|---|---|---|
| Unit — differs → keep (`REQ-002`) | `uv run pytest tests/agent/test_startup_approval_recovery.py::TestStartupOrchestratorRecoverPendingApprovals::test_startup_recovery_keeps_existing_pending_approval_task_id` | rewritten test | passes |
| Unit — equal → overwrite (`REQ-003`) | `uv run pytest ...::test_startup_recovery_overwrites_when_current_equals_recovered` | new test | passes |
| Unit — None → overwrite (unchanged) | `uv run pytest ...::test_startup_recovery_no_warning_when_task_id_not_already_set` | existing test | passes |
| Full recover class | `uv run pytest tests/agent/test_startup_approval_recovery.py::TestStartupOrchestratorRecoverPendingApprovals` | all 10 tests | all pass (was 1 failed / 9 passed pre-change) |
| Lint / type / imports | `ruff check`, `mypy`, `lint-imports` per `rules/toolchain.md` | `tests/agent/test_startup_approval_recovery.py` | 0 errors / no new errors / 0 violations |

## Completion criteria

- `test_startup_recovery_warns_on_pending_approval_task_id_overwrite` no longer exists; replaced by `test_startup_recovery_keeps_existing_pending_approval_task_id` asserting the value is kept and "Keeping existing ..." is logged once.
- `test_startup_recovery_overwrites_when_current_equals_recovered` exists and asserts the idempotent overwrite (`REQ-003`).
- All 10 `TestStartupOrchestratorRecoverPendingApprovals` tests pass; no new lint/type/import findings.

## Out of scope

- Source fix in `scripts/agent/startup_approval_recovery.py` (paired doc).
- Changes to MCP-health or server-startup test classes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite failing overwrite-warning test to REQ-001-compliant keep behavior (`REQ-002`) | Completed | — | — | Rename + flip assertions (see Details) |
| 2 | Add REQ-003 idempotent-overwrite regression test | Completed | — | — | Covers equal-value branch not otherwise asserted |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. full recover class | Completed | — | — | Requires paired source doc applied first |
| 4 | Update documentation (N/A per plan) | Completed | — | — |  |

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
- **Requirement ID**: `REQ-002` — test verifies recovery respects existing approval state; `REQ-003` — test verifies recovery correctly overwrites stale state
- **Source issue**: issues/20261004-143008_ar009_pending_approval_overwrite.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182816_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-134332
- **Related target files**: tests/agent/test_startup_approval_recovery.py