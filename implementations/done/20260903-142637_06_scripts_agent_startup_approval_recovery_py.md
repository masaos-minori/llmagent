# Implementation Procedure: scripts/agent/startup_approval_recovery.py

## Goal

Create a new module/class that owns the approval recovery concern: restoring workflow approval-pending state from a previous session (REQ-005).

## Scope

- Extract `_recover_pending_approvals` from `StartupOrchestrator` into a dedicated class
- Preserve all current behavior: pending approval lookup, StateStore connection lifecycle, context state restoration
- Preserve all log message strings and `_view.write_*` output text from these methods

## Assumptions

- The class will be named `ApprovalRecovery` and instantiated with `(ctx, view)` in `StartupOrchestrator.__init__`
- `find_all_pending_approvals` and `StateStore` are imported from `agent.workflow.approval_ops` and `agent.workflow.state_store` respectively
- The class does NOT own `_classify_memory_failure` — that belongs to `PromptSetup`

## Design decisions

- **Constructor injection**: Accept `AgentContext` and `CLIView` in `__init__`, matching the existing `StartupOrchestrator` pattern.
- **Single public method**: Expose one public method `recover()` that replaces the entire `_recover_pending_approvals` method body.
- **No instance state beyond constructor args**: All operations flow through the returned context state.
- **No circular dependency risk**: Import `find_all_pending_approvals` and `StateStore` lazily where needed.

## Alternatives considered

- **Functional approach**: Module-level function instead of a class. Rejected: class better encapsulates the approval recovery concept and matches constructor-injection/delegation pattern used elsewhere.

## Implementation

### Target file

`scripts/agent/startup_approval_recovery.py`

### Procedure

Create new file with `ApprovalRecovery` class containing extracted method.

### Method

New file creation.

### Details

**Phase 2: Module Extraction** (REQ-005)

1. Create `scripts/agent/startup_approval_recovery.py`:

```python
"""scripts/agent/startup_approval_recovery.py

Approval recovery: restore workflow approval-pending state from a previous session.

Extracted from scripts/agent/startup.py (REQ-005).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.output_tags import OutputTag

if TYPE_CHECKING:
    from agent.cli_view import CLIView


class ApprovalRecovery:
    """Owns approval recovery from previous sessions."""

    def __init__(self, ctx: Any, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    async def recover(self) -> None:
        """Restore workflow approval-pending state from a previous session."""
        ctx = self._ctx
        store = StateStore()
        try:
            results = find_all_pending_approvals(store.get_connection())
        finally:
            store.close()
        if not results:
            logger.warning(
                "No pending approvals found; existing approvals may have expired"
            )
            return
        # Recover the most recent pending approval first
        task_id, approval = results[0]
        ctx.workflow.approval_pending = True
        ctx.turn.pending_approval_id = approval.approval_id
        if ctx.turn.pending_approval_task_id is not None:
            logger.warning(
                "Overwriting pending_approval_task_id %s with %s during recovery",
                ctx.turn.pending_approval_task_id,
                task_id,
            )
        ctx.turn.pending_approval_task_id = task_id
        logger.warning(
            "Recovered %d pending approval(s); showing last: task=%s approval=%s reason=%s",
            len(results),
            task_id,
            approval.approval_id,
            approval.reason or "none",
        )
        self._view.write_warning(
            f"{OutputTag.WORKFLOW} Pending approval from previous session — "
            f"{len(results)} pending approval(s); last: task={task_id} approval={approval.approval_id} reason={approval.reason or 'none'}.\n"
            f"Use /approve {approval.approval_id} [reason] or /reject {approval.approval_id} [reason]."
        )
```

Note: Need to add `Any` import, `logger` initialization, `find_all_pending_approvals`, `StateStore` imports inside the method body to avoid circular dependency.

2. In `startup.py` seq 01 doc, replace `_recover_pending_approvals` body with delegation call.

## Compatibility considerations

- **Critical**: `StartupOrchestrator.run()` must still receive `None` from `recover()` (no return value). Any change to the return type breaks the caller.
- **Rollback semantics**: If `recover()` raises, `run()`'s exception handler must still call `shutdown_all()`.
- **Log messages**: All `logger.info/warning/error` strings must match original exactly.
- **Output text**: All `_view.write_*` calls must produce identical text output.
- **Context state**: `ctx.workflow.approval_pending`, `ctx.turn.pending_approval_id`, `ctx.turn.pending_approval_task_id` assignments must occur identically.

## Security considerations

- No security-sensitive changes. `_mask_secrets` is not called in this module's methods.
- `StartupInterrupted` is not raised by any method in this module.

## Rollback considerations

- If extraction breaks behavior, revert to original `_recover_pending_approvals` method in `startup.py`.
- Delete `scripts/agent/startup_approval_recovery.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `scripts/agent/startup_approval_recovery.py` | Unit — approval recovery | New tests (pending approval scenarios) | All pass |
| `scripts/agent/startup.py` | Integration — verify delegated method produces identical state | `uv run pytest tests/agent/test_startup.py` | No new failures |

## Completion criteria

- [ ] `ApprovalRecovery` class exists in `scripts/agent/startup_approval_recovery.py`
- [ ] `recover()` returns `None`
- [ ] Pending approval lookup logic preserved verbatim
- [ ] StateStore connection lifecycle preserved (open → query → close in finally)
- [ ] Context state restoration preserved
- [ ] Warning display preserved
- [ ] `ruff`, `mypy`, `bandit` clean on new file
- [ ] All four test files pass unchanged in outcome

## Out of scope

- Changing approval recovery logic or adding new recovery paths
- Modifying `repl_health.py`, `http_lifecycle.py`, or `factory.py` internals
- Performance optimization

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: scripts/agent/startup_approval_recovery.py
