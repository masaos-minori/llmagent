## Goal

Add an explicit `UNKNOWN` branch in `recover_corruption()` that preserves the target database and requires operator intervention, per ADR-008 INV-17.

## Scope

Modify `scripts/db/recovery.py` only — add one conditional branch in `recover_corruption()` and update its docstring.

## Assumptions

- The existing CORRUPTION branch behavior for rag/session (auto-restore) is an accepted ADR-008 decision and must not be changed.
- The workflow/eventbus `no_recovery_allowed` path is already correct and serves as the pattern for the UNKNOWN branch.
- `RecoveryResult` model supports adding a new `action` value for "preserved" outcome.

## Design decisions

- Add a parallel check alongside the existing `condition in (LOCK_CONTENTION, PERMISSION_FAILURE, INVALID_FORMAT)` branch. When `condition == DbCondition.UNKNOWN`, return a `RecoveryResult` with `success=False`, `action="preserved_operator_intervention_required"`, and detail explaining that operator intervention is needed. This mirrors the workflow/eventbus `no_recovery_allowed` pattern without modifying the CORRUPTION branch's restore behavior for rag/session.

## Alternatives considered

- Modifying the existing conditional logic to split UNKNOWN before the CORRUPTION fall-through would require restructuring the entire block and risks regressing CORRUPTION behavior.
- Adding a separate helper function like `_handle_unknown()` would introduce unnecessary indirection for a single-branch addition.

## Implementation

### Target file

`scripts/db/recovery.py`

### Procedure

1. Locate the comment `# It's CORRUPTION or UNKNOWN` at line 216.
2. Insert a new `if condition == DbCondition.UNKNOWN:` branch immediately after the existing `condition in (LOCK_CONTENTION, PERMISSION_FAILURE, INVALID_FORMAT)` branch (after line 214), before the `# It's CORRUPTION or UNKNOWN` comment.
3. Return a `RecoveryResult` with `success=False`, `action="preserved_operator_intervention_required"`, and a detail string explaining operator intervention is required.
4. Update the docstring of `recover_corruption()` to include `"preserved_operator_intervention_required"` in the list of possible `action` values.

### Method

```python
# After line 214 (end of LOCK_CONTENTION/PERMISSION_FAILURE/INVALID_FORMAT branch):
if condition == DbCondition.UNKNOWN:
    return RecoveryResult(
        success=False,
        action="preserved_operator_intervention_required",
        detail=f"Unknown integrity-check failure: operator intervention required ({detail})",
        dry_run=dry_run,
    )

# Then keep the existing flow:
# It's CORRUPTION or UNKNOWN
...
```

### Details

- **Line 214→215 insertion point**: After the closing paren of the `condition in (...)` branch's `return RecoveryResult(...)`.
- **New branch body**: Mirror the structure of the `no_recovery_allowed` branch (lines 228-233) but use `action="preserved_operator_intervention_required"` instead of `action="no_recovery_allowed"`.
- **Docstring update**: In `recover_corruption()` docstring, add `"preserved_operator_intervention_required"` to the documented `action` return values.
- **No changes to**: `_restore_from_backup()` call path, CORRUPTION branch logic, domain policy check (workflow/eventbus), or any other control flow.

## Compatibility considerations

- New `action` value `"preserved_operator_intervention_required"` must be documented so consumers know how to handle it.
- The value name follows the existing convention: snake_case, descriptive, no abbreviations.

## Security considerations

None significant. This change adds a preservation path rather than removing one.

## Rollback considerations

If the UNKNOWN branch causes unexpected behavior, revert by removing the inserted branch and restoring the original fall-through to `_restore_from_backup()`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `scripts/db/recovery.py` | Unit: assert UNKNOWN condition does not call `_restore_from_backup()` | `uv run pytest tests/db/test_db_maintenance.py -k recovery` | Test passes; no backup restore triggered |
| `scripts/db/recovery.py` | Integration: verify RecoveryResult action value for UNKNOWN | `uv run pytest tests/integration/test_session_recovery.py -k recovery` | Action value matches `"preserved_operator_intervention_required"` |
| `scripts/db/recovery.py` | Full suite regression | `uv run pytest` | All tests pass |
| `scripts/db/recovery.py` | Lint/type validation | `ruff check scripts/db/recovery.py && mypy scripts/db/recovery.py` | No errors |

## Completion criteria

- [ ] `DbCondition.UNKNOWN` branch added in `recover_corruption()` between the existing conditional branch and the CORRUPTION fall-through
- [ ] `RecoveryResult` returned with `success=False`, `action="preserved_operator_intervention_required"`
- [ ] Docstring updated to document the new `action` value
- [ ] CORRUPTION branch behavior unchanged (verified via targeted test)
- [ ] All validation checks pass

## Out of scope

- Modifying `_restore_from_backup()` behavior
- Changing CORRUPTION branch logic for rag/session
- Adding new DbCondition enum values
- Extending backup-rotation coverage
- Modifying any file outside `scripts/db/recovery.py`

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
- **Generated at**: 20260902-105941
- **Related target files**: scripts/db/recovery.py
