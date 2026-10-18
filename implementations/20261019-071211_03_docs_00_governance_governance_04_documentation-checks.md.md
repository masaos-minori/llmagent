## Goal

Update the GV-014 row in the documentation-checks matrix
(`docs/00_governance/governance_04_documentation-checks.md`) to reflect that the
auto-check implementation audit is now automated via the new checker, moving its status from
`Partial` to `Existing` and clearing the follow-up note.

## Scope

- **In-Scope**: edit the single GV-014 matrix row — status cell `Partial` → `Existing`, clear the
  trailing follow-up note (`REQ-005`).
- **Out-of-Scope**: any other matrix row, the automation/tool columns, or any other governance
  rule.

## Assumptions

- The corresponding tool change (creating `check_auto_check_inventory.py`) has been implemented and
  tested first (the preceding documents in this Plan).
- The matrix column holding `Partial`/`Existing` is the automation-completeness status (8th
  column); the trailing column is the follow-up note (9th column).

## Design decisions

- Only the GV-014 status + note cells are touched; the row's other columns are left intact. Clear
  the note to `None` to match other fully-automated rows (e.g. GV-001).

## Alternatives considered

N/A: a one-row matrix edit is the minimal, reviewable change.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Locate the `GV-014` row in the matrix.
2. Change its status cell (8th column) from `Partial` to `Existing`.
3. Clear the trailing follow-up note ("Automate auto-check implementation audit (currently
   manual)") — replace with `None`, consistent with other fully-automated rows.

### Method

- Edit the row in place; do not reflow or reorder the table. Verify the row is the only one
  containing `GV-014` before editing.
- Leave the rest of the row's columns unchanged (rule description, `Chk` category, `Manual`
  automation, `Human review` tool, `Periodic` trigger, `Warning` severity).

### Details

- `REQ-005`: after the tool change, the auto-check implementation audit is automated, so
  `Partial` → `Existing` and the follow-up note no longer applies.

> **Plan Gap (scope decision for the Plan, not applied here):** the GV-014 row's automation
> column still reads `Manual` and its tool column `Human review`. Marking the row
> `Existing` while leaving those two columns as `Manual`/`Human review` is internally
> inconsistent with fully-automated rows (which read `Auto` + a tool name). Deciding whether
> to also set automation=`Auto` and tool=`check_auto_check_inventory.py` is a Plan scope
> decision outside `REQ-005`; this procedure implements `REQ-005` as written only.

## Compatibility considerations

N/A: documentation matrix only; no code impact.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Docs validation | `rules/toolchain.md` docs checker (e.g. `check_docs_quality.py` / `check_docs_structure.py`) | Matrix row well-formed; GV-014 = `Existing` |

## Completion criteria

- The GV-014 row reports `Existing` with the follow-up note cleared.

## Out of scope

Any other matrix row, the automation/tool columns, or any other governance rule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-005 |
| 2 | Add or update tests per Validation plan | Pending | — | — | REQ-005 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | all REQs |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | REQ-005 |

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
- **Requirement ID**: `REQ-005` (mark GV-014 fully automated in the matrix)
- **Source issue**: `issues/done/20261018-173319_gov014_automate-audit-of-auto-checks-documented-as-implemented.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-181700_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-071211
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
