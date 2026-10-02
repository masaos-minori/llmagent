# Implementation Procedure: Fix stale governance paths in docs/10_adr/ADR-002-config-isolation.md

## Goal

Replace stale `docs/governance_0N_*` path references in `docs/10_adr/ADR-002-config-isolation.md` with actual existing paths under `docs/00_governance/governance_0N_*`.

## Scope

- Modify only `docs/10_adr/ADR-002-config-isolation.md`.
- In-Scope: Replace stale path on line 414.
- Out-of-Scope: Changing any other content in the file.

## Assumptions

- The correct path is `docs/00_governance/governance_01_documentation-policy.md` (confirmed by filesystem inspection).

## Design decisions

- **Approach**: Direct string replacement — replace `docs/governance_01_documentation-policy.md` with `docs/00_governance/governance_01_documentation-policy.md` on line 414.

## Alternatives considered

None — direct replacement is the only sensible approach for stale paths.

## Implementation

### Target file

`docs/10_adr/ADR-002-config-isolation.md`

### Procedure

Replace the stale path string on line 414 with the correct path.

### Method

Edit `docs/10_adr/ADR-002-config-isolation.md` line 414: change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`.

### Details

Line 414 currently reads:
```
- **Approval Reference**: `docs/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
```

Change to:
```
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
```

Only the path string changes; surrounding text is preserved.

## Compatibility considerations

- The corrected path resolves to an existing file (`docs/00_governance/governance_01_documentation-policy.md`).

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path string if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-002-config-isolation.md` | Path resolution | `grep -rnE "docs/governance_0[0-4]_" docs/10_adr/ADR-002-config-isolation.md` | No matches |
| `docs/10_adr/ADR-002-config-isolation.md` | File existence | `test -f docs/00_governance/governance_01_documentation-policy.md` | File exists |

## Completion criteria

- The path on line 414 of `ADR-002-config-isolation.md` resolves to an existing file.
- No remaining `docs/governance_0N_*` patterns in `ADR-002-config-isolation.md`.

## Out of scope

- Other stale paths in `ADR-002-config-isolation.md` (if any).
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
