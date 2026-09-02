# Implementation Procedure: Fix UNKNOWN classification handling in recover_corruption()

## Goal

Ensure `DbCondition.UNKNOWN` integrity-check results preserve the target database and require operator intervention, per REQ-001 and REQ-002 (ADR-008 INV-17).

## Scope

**In-Scope**: Modify `recover_corruption()` branch logic to distinguish `UNKNOWN` from `CORRUPTION`; update docstring action value list.

**Out-of-Scope**: Change `_classify_error()` classification logic; modify CORRUPTION branch restore behavior for rag/session; add new DbCondition values; extend backup-rotation coverage; modify RecoveryResult model fields.

## Assumptions

- The existing CORRUPTION branch behavior for rag/session (auto-restore) is an accepted ADR-008 decision and must not be changed.
- The workflow/eventbus `no_recovery_allowed` path is already correct and serves as the pattern for the UNKNOWN branch.
- `RecoveryResult` model supports adding a new `action` value for "preserved" outcome.

## Design decisions

- Add a parallel check alongside the existing `condition in (LOCK_CONTENTION, PERMISSION_FAILURE, INVALID_FORMAT)` branch. When `condition == DbCondition.UNKNOWN`, return a `RecoveryResult` with `success=False`, `action="preserved_operator_intervention_required"`, and detail explaining that operator intervention is needed.
- Use `"preserved_operator_intervention_required"` as the action value — consistent naming convention with existing values like `"no_recovery_allowed"`.
- Place the UNKNOWN check after the LOCK_CONTENTION/PERMISSION_FAILURE/INVALID_FORMAT branch but before the rag/session restore logic, mirroring the placement of the workflow/eventbus `no_recovery_allowed` block.

## Alternatives considered

- **Alternative 1: Extend `_run_integrity_check()` to return a different condition for unknown errors.** Rejected: OUT_OF_SCOPE per plan — changing `_classify_error()` classification logic is out of scope.
- **Alternative 2: Return `action="error"` for UNKNOWN.** Rejected: "error" is used for operational failures (LOCK_CONTENTION, etc.); UNKNOWN requires explicit operator intervention messaging, not just error reporting.
- **Alternative 3: Merge UNKNOWN into the CORRUPTION branch.** Rejected: defeats the purpose of INV-17 — UNKNOWN must be handled differently from confirmed corruption.

## Implementation

### Target file

`scripts/db/recovery.py`

### Procedure

1. After the existing `condition in (LOCK_CONTENTION, PERMISSION_FAILURE, INVALID_FORMAT)` branch (line ~204-214), add a new `elif condition == DbCondition.UNKNOWN:` branch.
2. Inside the new branch, return a `RecoveryResult(success=False, action="preserved_operator_intervention_required", detail=f"Unknown integrity-check failure ({detail}): operator intervention required", dry_run=dry_run)`.
3. Update the docstring `action` value list (lines ~178-184) to include `"preserved_operator_intervention_required"` as a documented possible value.

### Method

Insert the UNKNOWN branch between the existing conditional branches and the "# It's CORRUPTION or UNKNOWN" comment:

```python
    if condition in (
        DbCondition.LOCK_CONTENTION,
        DbCondition.PERMISSION_FAILURE,
        DbCondition.INVALID_FORMAT,
    ):
        return RecoveryResult(
            success=False,
            action="error",
            detail=f"{condition.value}: {detail}",
            dry_run=dry_run,
        )

    # NEW: UNKNOWN classification — preserve DB, require operator intervention
    elif condition == DbCondition.UNKNOWN:
        return RecoveryResult(
            success=False,
            action="preserved_operator_intervention_required",
            detail=f"Unknown integrity-check failure ({detail}): operator intervention required",
            dry_run=dry_run,
        )

    # It's CORRUPTION or UNKNOWN
    ...
```

### Details

- Line reference: Insert after line ~214 (end of LOCK_CONTENTION/PERMISSION_FAILURE/INVALID_FORMAT branch), before line ~216 ("# It's CORRUPTION or UNKNOWN").
- The `detail` field includes the original error detail string (`{detail}`) for debugging context.
- The `dry_run` parameter is forwarded unchanged from the caller.
- Docstring update: Add `"preserved_operator_intervention_required"` to the action value list near lines ~178-184.

## Compatibility considerations

- The new `action` value `"preserved_operator_intervention_required"` is a new consumer-facing string. Any code that matches on specific action values will need to handle this case.
- The `detail` message format follows the existing pattern: `{condition_type} ({detail}): {explanation}`.
- No API contract change — `RecoveryResult` fields remain the same.

## Security considerations

- This change improves security posture by preventing automatic restoration based on unclassifiable failures, which could discard legitimate data if the failure was transient rather than actual corruption.
- No new secrets, credentials, or sensitive data exposure.

## Rollback considerations

- To rollback: remove the added `elif condition == DbCondition.UNKNOWN:` branch and revert the docstring update.
- The existing CORRUPTION branch logic remains intact — no structural dependency on the UNKNOWN branch.
- If tests fail due to the new action value, revert the action value string to its previous form.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/recovery.py | Unit: assert UNKNOWN condition does not call `_restore_from_backup()` | `uv run pytest tests/db/test_db_maintenance.py -k recovery` | Test passes; no backup restore triggered |
| scripts/db/recovery.py | Integration: verify RecoveryResult action value for UNKNOWN | `uv run pytest tests/integration/test_session_recovery.py -k recovery` | Action value matches expected string |
| scripts/db/recovery.py | Full suite regression | `uv run pytest` | All tests pass |
| scripts/db/recovery.py | Lint/type validation | `ruff check scripts/db/recovery.py && mypy scripts/db/recovery.py` | No errors |

## Completion criteria

- [ ] `DbCondition.UNKNOWN` integrity-check result on `rag`/`session` no longer triggers `_restore_from_backup()`.
- [ ] `recover_corruption()` returns a `RecoveryResult` whose `action` is `"preserved_operator_intervention_required"` for Unknown outcomes.
- [ ] Docstring action value list includes `"preserved_operator_intervention_required"`.
- [ ] Tests pass: `uv run pytest tests/db/test_db_maintenance.py tests/integration/test_session_recovery.py`.
- [ ] Standard validation sequence passes: format → lint → type → arch → security → test → coverage.

## Out of scope

- Adding unit tests for the UNKNOWN branch (covered in separate implementation procedure for test files).
- Updating ADR-008 Known Deviations entry (covered in separate implementation procedure for documentation files).
- Modifying `_classify_error()` to improve classification accuracy.
- Changing CORRUPTION branch behavior for rag/session.

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260831-181721_adr008_01_recover_corruption_unknown_classification_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-064946_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-064946
- **Related target files**: scripts/db/recovery.py
