## Goal

Update ADR-008's Known Deviations section to mark the INV-17 gap resolved once the UNKNOWN branch fix is implemented.

## Scope

Documentation-only: modify `docs/adr/ADR-008-sqlite-4db-separation.md` Known Deviations section.

## Assumptions

- The UNKNOWN branch fix described in `implementations/20260902-105941_01_scripts_db_recovery_py.md` is complete and validated before updating this ADR.
- The Known Deviations entry format should remain consistent with existing entries (Known Issue type + Summary + Impact + Resolution Target).

## Design decisions

- Update the existing Known Issue text in place rather than removing the entry entirely — this preserves the historical record of what was identified and resolved.
- Change the entry from describing an open gap to documenting a resolved deviation.

## Alternatives considered

- Removing the Known Issue entry entirely would lose the audit trail of what was identified and why.
- Moving the entry to a separate "Resolved Issues" subsection would fragment the Known Deviations section unnecessarily.

## Implementation

### Target file

`docs/adr/ADR-008-sqlite-4db-separation.md`

### Procedure

1. Locate the Known Deviations entry at line 435 that describes the INV-17 violation.
2. Update the entry text to reflect that the gap is now resolved.
3. Update the Type field from "Implementation Gap" to "Resolved".
4. Update the Resolution Target field to indicate resolution date or reference the related implementation procedure.

### Method

Replace the Known Deviations entry at line 435 with:

```markdown
- **Resolved Issue**: `recover_corruption()` (`scripts/db/recovery.py`) previously treated Unknown classification (`DbCondition.UNKNOWN`) identically to Corruption classification, automatically attempting backup restore on `rag`/`session`. INV-17 has been addressed by adding an explicit UNKNOWN branch that preserves the target database and requires operator intervention.
  - **Type**: Resolved
  - **Summary**: Unknown classification handling now separated from Corruption classification
  - **Impact**: Previously classified as Implementation Gap; now resolved
  - **Resolution**: Implemented in `implementations/20260902-105941_01_scripts_db_recovery_py.md`; verified via unit and integration tests
```

### Details

- **Line 435**: Replace the existing `- **Known Issue**:` bullet with `- **Resolved Issue**:`.
- **Type field**: Change from `Implementation Gap` to `Resolved`.
- **Summary field**: Update to describe the current state (gap resolved).
- **Impact field**: Note the previous classification and its resolution.
- **Resolution field**: Reference the related implementation procedure document.
- **No changes to**: Any other ADR sections, Known Deviations entries, or Review Triggers.

## Compatibility considerations

N/A — documentation-only change.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

If the UNKNOWN branch fix is reverted, this ADR entry should also be reverted to its prior state. Coordinate rollback of both artifacts together.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `docs/adr/ADR-008-sqlite-4db-separation.md` | Manual review of Known Deviations entry | Read the updated entry | Entry accurately reflects the resolved state |

## Completion criteria

- [ ] Known Deviations entry updated to reflect INV-17 gap is resolved
- [ ] Type field changed from "Implementation Gap" to "Resolved"
- [ ] Resolution field references the related implementation procedure
- [ ] No unintended changes to other ADR sections

## Out of scope

- Updating any other ADRs or documentation
- Modifying source code
- Adding new architectural decisions
- Modifying any file outside `docs/adr/ADR-008-sqlite-4db-separation.md`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A: documentation only | — | — | |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260831-181721_adr008_01_recover_corruption_unknown_classification_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-064946_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-105941
- **Related target files**: docs/adr/ADR-008-sqlite-4db-separation.md
