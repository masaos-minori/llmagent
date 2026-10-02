# Implementation Procedure: Fix stale governance path in docs/00_governance/governance_01_documentation-policy.md

## Goal

Replace the stale governance document path references (`docs/governance_0N_*`) with the actual existing paths (`docs/00_governance/governance_0N_*`) in `docs/00_governance/governance_01_documentation-policy.md`.

## Scope

- Modify only `docs/00_governance/governance_01_documentation-policy.md`.
- In-Scope: Replace the stale paths on lines 131 and 335.
- Out-of-Scope: Changing any other content in `docs/00_governance/governance_01_documentation-policy.md`.

## Assumptions

- The correct paths are `docs/00_governance/governance_02_documentation-metadata.md` and `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (confirmed by filesystem inspection).
- No other references to `docs/governance_0N_*` exist in this file.

## Design decisions

- **Approach**: Direct string replacement — replace `docs/governance_02_documentation-metadata.md` with `docs/00_governance/governance_02_documentation-metadata.md` on line 131, and `docs/governance_03_issue-and-uncertainty-management.md` with `docs/00_governance/governance_03_issue-and-uncertainty-management.md` on line 335.
- **Alternatives considered**: None — this is a straightforward path correction.

## Alternatives considered

None — direct replacement is the only sensible approach for stale path strings.

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

Replace the stale path strings on lines 131 and 335 with the correct paths.

### Method

Edit `docs/00_governance/governance_01_documentation-policy.md`:
- Line 131: change `docs/governance_02_documentation-metadata.md` → `docs/00_governance/governance_02_documentation-metadata.md`
- Line 335: change `docs/governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Details

Line 131 currently reads:
```
| documentation-metadata | Metadata on documentation assets | `docs/governance_02_documentation-metadata.md` | Metadata Validator | Known Issues | |
```

Change to:
```
| documentation-metadata | Metadata on documentation assets | `docs/00_governance/governance_02_documentation-metadata.md` | Metadata Validator | Known Issues | |
```

Line 335 currently reads:
```
- Removed-name reintroduction detected by `check_compat_shims.py --check-removed-names` (`GV-020`), without an approved temporary exception (`docs/governance_03_issue-and-uncertainty-management.md`)
```

Change to:
```
- Removed-name reintroduction detected by `check_compat_shims.py --check-removed-names` (`GV-020`), without an approved temporary exception (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
```

Only the path strings change; surrounding text is preserved.

## Compatibility considerations

- The corrected paths resolve to existing files (`docs/00_governance/governance_02_documentation-metadata.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`).
- No other tool or document depends on the old directory-less forms.

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path strings if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Path resolution | `grep -rnE "docs/governance_0[0-4]_" docs/00_governance/governance_01_documentation-policy.md` | No matches |
| `docs/00_governance/governance_01_documentation-policy.md` | File existence | `test -f docs/00_governance/governance_02_documentation-metadata.md && test -f docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Both files exist |

## Completion criteria

- All `docs/governance_0N_*` references replaced with `docs/00_governance/governance_0N_*` in `docs/00_governance/governance_01_documentation-policy.md`.
- Corrected paths resolve to existing files.

## Out of scope

- Other stale paths in `docs/00_governance/governance_01_documentation-policy.md` (if any).
- Changes to other files.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261002-135534 | 20261002-135534 | REQ-003 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test needed for path string fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261002-135534 | 20261002-135534 | REQ-003 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No documentation update needed |

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
- **Requirement ID**: REQ-003 — Decide on the directory-less `docs/governance_0N_*` form and apply the decision consistently
- **Source issue**: issues/20261001-103636_govpath001_correct-stale-governance-document-path-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-072411_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261002-073146
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md