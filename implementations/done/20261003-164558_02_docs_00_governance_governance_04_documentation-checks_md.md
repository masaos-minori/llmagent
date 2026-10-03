## Goal

Update the check description in `governance_04_documentation-checks.md` if the exit behavior decision changes the documented behavior of `check_needs_confirmation_inventory.py` (REQ-003).

## Scope

- Update the check description for `check_needs_confirmation_inventory.py` in `governance_04_documentation-checks.md` if the exit behavior changes.
- Document whether WARNING-level findings cause a non-zero exit code.

## Assumptions

- The decision made in Row 1 will determine whether this update is needed.
- If the decision is "warnings → exit 0", no change to this document is needed.
- If the decision is "warnings → exit non-zero", the check description must reflect the new behavior.

## Design decisions

- Only update the check description if the exit behavior changes from the current documented behavior.
- Use clear language to indicate whether WARNING-level findings block verification.

## Alternatives considered

- Leave the check description unchanged regardless of the decision — rejected because the documentation should accurately reflect the checker's behavior.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Determine the exit behavior decision from Row 1.
2. If the decision changes the exit behavior, update the check description.
3. Verify the documentation is consistent with the implementation.

### Method

- Locate the `check_needs_confirmation_inventory.py` section in `governance_04_documentation-checks.md` (around line 90-97).
- Current description states:
  > Verifies the NC inventory stays in sync with `docs/*.md`.
  > 
  > **Checks:**
  > - "Needs confirmation" mentions in docs are registered in the centralized inventory (`governance_03_issue-and-uncertainty-management.md`)
  > - Resolved NC items do not leave markers in source documents
  > - Field count declarations match actual list item counts

- If the exit behavior changes, add a note about the exit code behavior:
  ```markdown
  **Exit behavior:** WARNING-level findings cause a non-zero exit code.
  ```
  Or if detection-only:
  ```markdown
  **Exit behavior:** WARNING-level findings do NOT cause a non-zero exit code (exit 0).
  ```

### Details

Current state of the check description (lines 90-97):
```markdown
### 3. Needs Confirmation Inventory Check (`check_needs_confirmation_inventory.py`)

Verifies the NC inventory stays in sync with `docs/*.md`.

**Checks:**
- "Needs confirmation" mentions in docs are registered in the centralized inventory (`governance_03_issue-and-uncertainty-management.md`)
- Resolved NC items do not leave markers in source documents
- Field count declarations match actual list item counts
```

The Governance Verification Matrix also references this check:
- GV-009: Needs Confirmation owner and deadline — Auto, `check_needs_confirmation_inventory.py`, PR, Warning

If the exit behavior changes, consider updating GV-009's Gate column from "Warning" to "Blocking" if appropriate.

## Compatibility considerations

- Updating the check description affects how users interpret the checker's behavior.
- If the gate status changes from "Warning" to "Blocking", downstream workflows may need updates.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Reverting the documentation change is straightforward — restore the previous text. If the decision was made incorrectly, revert both the code change (Row 1) and this documentation update.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_04_documentation-checks.md | Documentation consistency | Manual review | Check description reflects the decision |

## Completion criteria

- The check description accurately reflects the exit behavior decision.
- The Governance Verification Matrix (GV-009) is consistent with the decision if applicable.

## Out of scope

- Resolving the actual orphaned markers themselves (handled by other issues).
- Changing the checker's warning format or severity levels.
- Adding new checks beyond the exit-status decision.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Determine exit behavior decision from Row 1 | Pending | — | — | |
| 2 | Update check description if needed | Pending | — | — | |
| 3 | Verify documentation consistency | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261002-155701_ncinv002_exit_status_for_untracked_markers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261003-150911_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-164558
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
