## Goal

Only overwrite `pending_approval_task_id` during recovery when the current value is stale (from a previous session), preventing silent overwrites of active approvals.

## Scope

- Modify `scripts/agent/startup_approval_recovery.py`: add comparison before overwriting `pending_approval_task_id`
- Update warning message to include both old and new values

## Assumptions

- The recovered task ID is from a previous session and should be considered stale if a current value exists
- There is no reliable way to determine which approval is "current" vs "stale" without additional metadata
- The simplest approach is to prefer the current value when both exist

## Design decisions

- If `pending_approval_task_id` already has a value and it differs from the recovered value, keep the current value (assuming it's active)
- Only overwrite if the current value is None or identical to the recovered value
- Update warning message to include both old and new values for transparency

## Alternatives considered

- Adding timestamp-based staleness detection — requires changes to TurnState, over-engineering
- Using session IDs to distinguish stale from current — requires changes to TurnState, over-engineering

## Implementation
### Target file
`scripts/agent/startup_approval_recovery.py`

### Procedure
Add comparison logic before overwriting `pending_approval_task_id` in recover(). Update warning message to include both values.

### Method
1. Locate lines 50-56 in `scripts/agent/startup_approval_recovery.py` (recovery overwrite logic)
2. Replace unconditional overwrite with conditional check
3. Update warning message to include both old and new values

### Details
```python
# Before (lines 50-56):
if ctx.turn.pending_approval_task_id is not None:
    logger.warning(
        "Overwriting pending_approval_task_id %s with %s during recovery",
        ctx.turn.pending_approval_task_id,
        task_id,
    )
ctx.turn.pending_approval_task_id = task_id

# After:
current_value = ctx.turn.pending_approval_task_id
if current_value is not None and current_value != task_id:
    # Current value appears to be active (not stale) — keep it
    logger.info(
        "Keeping existing pending_approval_task_id %s instead of recovering %s",
        current_value,
        task_id,
    )
elif current_value is None or current_value == task_id:
    # No current value or same value — safe to set
    ctx.turn.pending_approval_task_id = task_id
else:
    # Different value but we can't determine staleness — log warning
    logger.warning(
        "Conflicting pending_approval_task_id: keeping %s, discarding recovered %s",
        current_value,
        task_id,
    )
```

The key change is adding a conditional check before overwriting. This prevents silent overwrites of active approvals while still allowing recovery of stale state.

## Compatibility considerations

This change is backward-compatible — it adds a protection mechanism that was previously absent. No existing behavior is lost for cases where the current value is None or identical to the recovered value.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original unconditional overwrite if callers depend on immediate recovery. This would restore the previous behavior but reintroduce silent overwrite risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup_approval_recovery.py | Unit test — verify recovery respects existing approval | uv run pytest tests/agent/test_startup_approval_recovery.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Recovery does not overwrite an active approval without justification (REQ-001)
- [ ] Warning message includes both old and new values (REQ-004)
- [ ] All new tests pass when run individually

## Out of scope

- Changes to the approval recovery query logic
- Changes to the StateStore API
- Creating new test file (handled in separate document)

## Implementation outcome

Deviation from procedure: the inline draft was NOT applied. Origin/master already ships
this fix in `ApprovalRecovery.recover()`. The keep-existing guard was introduced in commit
`10308ed7` and the unconditional-set branch was refined in `c0a589e1`. Current behavior is
Explicit in code and Verified by test:

- REQ-001 (does not overwrite an active approval without justification): when
  `pending_approval_task_id` already holds a value that differs from the recovered
  `task_id`, `recover()` logs a "Keeping existing pending_approval_task_id ... instead of
  overwriting with ..." warning and skips the assignment. The assignment runs only when the
  value is unset or equals the recovered id.
- REQ-004 (warning includes both old and new values): both branches of the guard log the
  existing id and the recovered id.

Structural deviation: the draft used a single `if`/`elif`/`else` with a `logger.info`
branch for the keep case; origin uses two `logger.warning` branches inside an `is not None`
guard plus a separate final guarded assignment. Both satisfy the same two requirements.

Traceability numbering mismatch: this procedure lists REQ-001 and REQ-004, while the shipped
tests label the equivalent behavior REQ-002 (`test_startup_recovery_keeps_existing_pending_approval_task_id`)
and REQ-003 (`test_startup_recovery_overwrites_when_current_equals_recovered`). The
requirement intent matches; only the numeric labels differ.

Existing regression coverage passes: `tests/agent/test_startup_approval_recovery.py` ran
clean (27 passed), including the keep-existing, overwrite-on-equal, and no-warning-when-unset
cases. No new file was created and no code was changed. Accepting the upstream implementation
and closing the workflow.

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Conditional-overwrite guard present in origin `10308ed7` / refined `c0a589e1`; no code authored by this workflow (see outcome). |
| 2 | Add or update tests per Validation plan | Done | — | — | `tests/agent/test_startup_approval_recovery.py` present in origin; 27 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | 27 passed; ruff/bandit clean (no code change). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | Out of scope per procedure. |

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
- **Source issue**: issues/20261004-143008_ar009_pending_approval_overwrite.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182816_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195608
- **Related target files**: scripts/agent/startup_approval_recovery.py
