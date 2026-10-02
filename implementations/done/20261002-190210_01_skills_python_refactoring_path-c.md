# Implementation Procedure: Fix stale path in skills/python-refactoring/path-c.md

## Goal

Replace the stale path `docs/00_governance_01_documentation-policy.md` in `skills/python-refactoring/path-c.md` with the actual existing path `docs/00_governance/governance_01_documentation-policy.md`.

## Scope

- Modify only `skills/python-refactoring/path-c.md`.
- In-Scope: Replace the stale path string on line 149 with the correct path.
- Out-of-Scope: Changing any other content in `skills/python-refactoring/path-c.md`.

## Assumptions

- The correct path is `docs/00_governance/governance_01_documentation-policy.md` (confirmed by filesystem inspection).
- No other references to `docs/00_governance_0N_*` exist in `skills/python-refactoring/path-c.md`.

## Design decisions

- **Approach**: Direct string replacement — replace `docs/00_governance_01_documentation-policy.md` with `docs/00_governance/governance_01_documentation-policy.md` on line 149.
- **Alternatives considered**: None — this is a straightforward path correction.

## Alternatives considered

None — direct replacement is the only sensible approach for a stale path.

## Implementation

### Target file

`skills/python-refactoring/path-c.md`

### Procedure

Replace the stale path string on line 149 with the correct path.

### Method

Edit `skills/python-refactoring/path-c.md` line 149: change `docs/00_governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`.

### Details

Line 149 currently reads:
```
`docs/00_governance_01_documentation-policy.md` "ADR Section Header Standardization"
```

Change to:
```
`docs/00_governance/governance_01_documentation-policy.md` "ADR Section Header Standardization"
```

Only the path string changes; surrounding text is preserved.

## Compatibility considerations

- The corrected path resolves to an existing file (`docs/00_governance/governance_01_documentation-policy.md`).
- No other tool or document depends on the old stale path.

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path string if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `skills/python-refactoring/path-c.md` | Path resolution | `grep -rnE "docs/00_governance_0[0-4]_" skills/python-refactoring/path-c.md` | No matches |
| `skills/python-refactoring/path-c.md` | File existence | `test -f docs/00_governance/governance_01_documentation-policy.md` | File exists |

## Completion criteria

- The path on line 149 of `skills/python-refactoring/path-c.md` resolves to an existing file.
- No remaining `docs/00_governance_0N_*` patterns in `skills/python-refactoring/path-c.md`.

## Out of scope

- Other stale paths in `skills/python-refactoring/path-c.md` (if any).
- Changes to other files.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-002 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test needed for path string fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-002 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No documentation update needed |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
