## Goal

Update the GV-008 row in the documentation-checks matrix
(`docs/00_governance/governance_04_documentation-checks.md`) to reflect that all four
Needs-Confirmation field-groups are now automated, moving its status from `Partial` to
`Existing` and clearing the manual-review follow-up note.

## Scope

- **In-Scope**: edit the single GV-008 matrix row — status `Partial` → `Existing`,
  clear the follow-up note (`REQ-004`).
- **Out-of-Scope**: any other matrix row or governance rule.

## Assumptions

- The corresponding tool change (extend `check_needs_confirmation_inventory.py`) has
  been implemented and tested first (the two preceding documents in this Plan).
- The matrix column holding `Partial`/`Existing` is the automation-completeness status.

## Design decisions

- Only the GV-008 row is touched; the row's other columns (rule text, tool, severity)
  are left intact.

## Alternatives considered

N/A: a one-row matrix edit is the minimal, reviewable change.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Locate the `GV-008` row in the matrix.
2. Change its status cell from `Partial` to `Existing`.
3. Clear the trailing follow-up note ("The tool checks `Assigned To` and
   `Resolution Target`; `Last Reviewed`, `Priority`, and Status/Blocking consistency
   are manual review") — replace with `None` or an equivalent empty marker consistent
   with the other rows.

### Method

- Edit the row in place; do not reflow or reorder the table. Verify the row is the
  only one containing `GV-008` before editing.
- Keep the rest of the row's columns unchanged: rule description, `Auto` automation,
  `check_needs_confirmation_inventory.py` tool, `Warning` severity.

### Details

- `REQ-004`: after the tool change, all four field-groups (`Assigned To`,
  `Resolution Target`, `Last Reviewed`, `Priority`, and Status/Blocking consistency)
  are automated, so `Partial` → `Existing` and the manual-review note no longer
  applies.

## Compatibility considerations

N/A: documentation matrix only; no code impact.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Docs validation | `rules/toolchain.md` docs checker (e.g. `check_docs_quality.py` / `check_docs_structure.py`) | Matrix row well-formed; GV-008 = `Existing` |

## Completion criteria

- The GV-008 row reports `Existing` with the manual-review follow-up note cleared.

## Out of scope

Any other matrix row or governance rule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update GV-008 row status `Partial` → `Existing` and clear follow-up note | Done | — | — | REQ-004 |
| 2 | Run the docs checker and confirm the matrix edit is well-formed | Done | — | — | check_docs_quality.py / check_docs_structure.py pass |

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
- **Requirement ID**: `REQ-004` (mark GV-008 fully automated in the matrix)
- **Source issue**: `issues/20261018-172829_gov008_automate-needs-confirmation-review-metadata-checks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-175819_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-033526
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
