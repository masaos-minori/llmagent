## Goal

Update GV-009 status from "Missing" to "Existing" in the Governance Verification Matrix table in `docs/00_governance/governance_04_documentation-checks.md`, completing REQ-008.

## Scope

- Update GV-009 row: change Status column from "Missing" to "Existing" and Follow-up column from "Implement" to "None"

## Assumptions

- The GV-009 row structure remains unchanged except for the Status and Follow-up columns
- No other rows need updating in this procedure
- The GV-009 rule description ("Needs Confirmation owner and deadline") correctly reflects the scope of this plan

## Design decisions

- Only update the two cells in the GV-009 row: Status column ("Missing" → "Existing") and Follow-up column ("Implement" → "None")
- Preserve all other columns in the row exactly as-is

## Alternatives considered

- Updating multiple governance rows simultaneously: unnecessary since only GV-009 is in scope for this plan
- Adding a new governance check entry: out of scope for this fix

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

Replace the GV-009 row's Status and Follow-up columns.

### Method

Use Edit tool to replace the single row.

### Details

**Line 300**: Replace:
```
| GV-009 | Needs Confirmation owner and deadline | Iss | Auto | `check_needs_confirmation_inventory.py` | PR | Warning | Missing | Implement |
```
with:
```
| GV-009 | Needs Confirmation owner and deadline | Iss | Auto | `check_needs_confirmation_inventory.py` | PR | Warning | Existing | None |
```

## Compatibility considerations

No compatibility impact. This change only updates documentation text within the governance matrix. The governance policy itself is unchanged.

## Security considerations

N/A: No security-relevant changes.

## Rollback considerations

Revert the Edit operation to restore the original row. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_04_documentation-checks.md | Manual review of markdown table | Read file content | Status = "Existing", Follow-up = "None" |

## Completion criteria

- GV-009 row shows "Existing" in the Status column
- GV-009 row shows "None" in the Follow-up column
- All other columns in the row remain unchanged

## Out of scope

- Modifying any other governance rows
- Changing the governance policy itself
- Modifying any files outside `Implementation Target Files` (additional target file discovery must be reported separately)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update GV-009 status in governance doc | Pending | — | — | |

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
- **Requirement ID**: REQ-008 — GV-009 status updated to "Existing" in the Governance Verification Matrix
- **Source issue**: issues/20260925-220411_gv009_needs_confirmation_owner_and_deadline_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-053537_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260926-062629
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
