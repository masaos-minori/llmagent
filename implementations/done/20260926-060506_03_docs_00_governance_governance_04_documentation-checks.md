## Goal

Update GV-007 status from "Missing" to "Existing" in the Governance Verification Matrix table in `docs/00_governance/governance_04_documentation-checks.md`.

## Scope

- Update GV-007 row at line 298: change "Missing" to "Existing" and "Implement" to "None"

## Assumptions

- The GV-007 row structure remains unchanged except for the Status and Follow-up columns
- No other rows need updating in this procedure

## Design decisions

- Only update the two cells in the GV-007 row: Status column ("Missing" → "Existing") and Follow-up column ("Implement" → "None")
- Preserve all other columns in the row exactly as-is

## Alternatives considered

- Updating multiple governance rows simultaneously: unnecessary since only GV-007 is in scope for this plan
- Adding a new governance check entry: out of scope for this fix

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

Replace the GV-007 row's Status and Follow-up columns.

### Method

Use Edit tool to replace the single row.

### Details

**Line 298**: Replace:
```
| GV-007 | Duplicate Related Link prohibition | Meta | Auto | `check_docs_structure.py` | PR | Warning | Missing | Implement |
```
with:
```
| GV-007 | Duplicate Related Link prohibition | Meta | Auto | `check_docs_structure.py` | PR | Warning | Existing | None |
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

- GV-007 row shows "Existing" in the Status column
- GV-007 row shows "None" in the Follow-up column
- All other columns in the row remain unchanged

## Out of scope

- Modifying any other governance rows
- Changing the governance policy itself
- Modifying any files outside `Implementation Target Files` (additional target file discovery must be reported separately)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260926-114432 | 20260926-114432 | Stale detector clean. GV-007 Status Missing->Existing, Follow-up Implement->None at line 298. |
| 2 | Add or update tests per Validation plan | Completed | 20260926-114432 | 20260926-114432 | N/A: validation plan defines no tests. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260926-114432 | 20260926-114432 | No Python code changed; toolchain n/a. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260926-114432 | 20260926-114432 | Edited docs/*.md. check_docs_quality.py exit0, check_docs_content_policy.py exit0, check_docs_structure.py: my file clean (other failures pre-existing, out of scope). |

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
- **Requirement ID**: REQ-009 — GV-007 status updated to "Existing" in the Governance Verification Matrix
- **Source issue**: issues/20260925-220411_gv007_duplicate_related_link_prohibition_check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-052849_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260926-060506
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md