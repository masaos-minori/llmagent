## Goal

Clear the optional follow-up note on the GV-012 row in the documentation-checks matrix
(`docs/00_governance/governance_04_documentation-checks.md`). The status remains `Existing`; only
the optional follow-up ("run cited tests in CI, not just verify path existence") is cleared, now
that the CI step implementing it is documented in the preceding procedure in this Plan.

## Scope

- **In-Scope**: edit the single GV-012 matrix row — clear the trailing optional follow-up note
  (`REQ-006`). Status stays `Existing`.
- **Out-of-Scope**: any other matrix row, the automation/tool columns, the status cell, or any
  other governance rule.

## Assumptions

- The corresponding CI change (running cited ADR invariant tests in the `lint` job) has been
  implemented and verified first (the preceding document in this Plan).
- The matrix column holding the optional follow-up is the trailing column (9th column); the
  status cell (8th column) already reads `Existing` and is left unchanged.

## Design decisions

- Only the GV-012 follow-up note cell is touched; the row's other columns (including the
  `Existing` status and `Auto` automation) are left intact. Clear the note to `None`, consistent
  with other rows that have no follow-up.

## Alternatives considered

N/A: a one-cell matrix edit is the minimal, reviewable change.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Locate the `GV-012` row in the matrix.
2. Clear the trailing optional follow-up note ("Optional: run cited tests in CI, not just verify
   path existence") — replace with `None`, consistent with rows that have no follow-up.
3. Leave the status cell as `Existing` (do not change it).

### Method

- Edit the row in place; do not reflow or reorder the table. Verify the row is the only one
  containing `GV-012` before editing.
- Leave the rest of the row's columns unchanged (rule description, `Pol` category, `Auto`
  automation, tool list, `Warning` severity, `Existing` status).

### Details

- `REQ-006`: the optional follow-up is cleared; status remains `Existing`.

## Compatibility considerations

N/A: documentation matrix only; no code impact.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Docs validation | `rules/toolchain.md` docs checker (e.g. `check_docs_quality.py` / `check_docs_structure.py`) | Matrix row well-formed; GV-012 = `Existing`, no follow-up |

## Completion criteria

- The GV-012 row's optional follow-up note is cleared; status remains `Existing`.

## Out of scope

Any other matrix row, the automation/tool columns, the status cell, or any other governance rule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-006 |
| 2 | Add or update tests per Validation plan | Pending | — | — | REQ-006 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | all REQs |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | REQ-006 |

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
- **Requirement ID**: `REQ-006` (clear the GV-012 optional follow-up note; status stays `Existing`)
- **Source issue**: `issues/done/20261018-173230_gov012_run-cited-adr-tests-in-ci-rather-than-only-verifying-cited-paths-exist.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-181334_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-070832
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
