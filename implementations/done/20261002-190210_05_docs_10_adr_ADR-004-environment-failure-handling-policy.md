# Implementation Procedure: Fix stale governance paths in docs/10_adr/ADR-004-environment-failure-handling-policy.md

## Goal

Replace stale `docs/governance_0N_*` path references in `docs/10_adr/ADR-004-environment-failure-handling-policy.md` with actual existing paths under `docs/00_governance/governance_0N_*`.

## Scope

- Modify only `docs/10_adr/ADR-004-environment-failure-handling-policy.md`.
- In-Scope: Replace stale paths on lines 581 and 636.
- Out-of-Scope: Changing any other content in the file.

## Assumptions

- The correct path is `docs/00_governance/governance_01_documentation-policy.md` (confirmed by filesystem inspection).

## Design decisions

- **Approach**: Direct string replacement — replace `docs/governance_01_documentation-policy.md` with `docs/00_governance/governance_01_documentation-policy.md` on lines 581 and 636.

## Alternatives considered

None — direct replacement is the only sensible approach for stale paths.

## Implementation

### Target file

`docs/10_adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

Replace the stale path strings on lines 581 and 636 with the correct paths.

### Method

Edit `docs/10_adr/ADR-004-environment-failure-handling-policy.md`:

**Line 581:** Change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`

**Line 636:** Change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`

### Details

Line 581 currently reads:
```
- **Approval Reference**: `docs/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
```

Change to:
```
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
```

Line 636 currently reads:
```
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
```

Change to:
```
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
```

Only the path strings change; surrounding text is preserved.

## Compatibility considerations

- The corrected paths resolve to existing files (`docs/00_governance/governance_01_documentation-policy.md`).

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path strings if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-004-environment-failure-handling-policy.md` | Path resolution | `grep -rnE "docs/governance_0[0-4]_" docs/10_adr/ADR-004-environment-failure-handling-policy.md` | No matches |
| `docs/10_adr/ADR-004-environment-failure-handling-policy.md` | File existence | `test -f docs/00_governance/governance_01_documentation-policy.md` | File exists |

## Completion criteria

- All `docs/governance_0N_*` paths on lines 581 and 636 of `ADR-004-environment-failure-handling-policy.md` resolve to existing files.
- No remaining `docs/governance_0N_*` patterns in `ADR-004-environment-failure-handling-policy.md`.

## Out of scope

- Other stale paths in `ADR-004-environment-failure-handling-policy.md` (if any).
- Changes to other files.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-003 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test needed for path string fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-003 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No documentation update needed |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
