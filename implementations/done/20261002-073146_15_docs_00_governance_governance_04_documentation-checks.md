# Implementation Procedure: Fix stale governance path in docs/00_governance/governance_04_documentation-checks.md

## Goal

Replace the stale governance document path reference (`docs/governance_02_documentation-metadata.md`) with the actual existing path (`docs/00_governance/governance_02_documentation-metadata.md`) in `docs/00_governance/governance_04_documentation-checks.md`.

## Scope

- Modify only `docs/00_governance/governance_04_documentation-checks.md`.
- In-Scope: Replace the stale path string on line 215.
- Out-of-Scope: Changing any other content in `docs/00_governance/governance_04_documentation-checks.md`.

## Assumptions

- The correct path is `docs/00_governance/governance_02_documentation-metadata.md` (confirmed by filesystem inspection).
- No other references to `docs/governance_0N_*` exist in this file.

## Design decisions

- **Approach**: Direct string replacement — replace `docs/governance_02_documentation-metadata.md` with `docs/00_governance/governance_02_documentation-metadata.md` on line 215.
- **Alternatives considered**: None — this is a straightforward path correction.

## Alternatives considered

None — direct replacement is the only sensible approach for a stale path string.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

Replace the stale path string on line 215 with the correct path.

### Method

Edit `docs/00_governance/governance_04_documentation-checks.md` line 215: change `docs/governance_02_documentation-metadata.md` → `docs/00_governance/governance_02_documentation-metadata.md`.

### Details

Line 215 currently reads:
```
5. **Deprecated** — Describes an obsolete feature no longer in use. Distinct from `docs/governance_02_documentation-metadata.md`'s Terminology Glossary terms `Obsolete` (a name still present and callable, but no longer the current production path) and `Dead Code` (a name with zero current callers): this evidence label classifies how well a *statement* is grounded, not the compatibility lifecycle of the thing the statement describes.
```

Change to:
```
5. **Deprecated** — Describes an obsolete feature no longer in use. Distinct from `docs/00_governance/governance_02_documentation-metadata.md`'s Terminology Glossary terms `Obsolete` (a name still present and callable, but no longer the current production path) and `Dead Code` (a name with zero current callers): this evidence label classifies how well a *statement* is grounded, not the compatibility lifecycle of the thing the statement describes.
```

Only the path string changes; surrounding text is preserved.

## Compatibility considerations

- The corrected path resolves to an existing file (`docs/00_governance/governance_02_documentation-metadata.md`).
- No other tool or document depends on the old directory-less form.

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path string if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Path resolution | `grep -rnE "docs/governance_0[0-4]_" docs/00_governance/governance_04_documentation-checks.md` | No matches |
| `docs/00_governance/governance_04_documentation-checks.md` | File existence | `test -f docs/00_governance/governance_02_documentation-metadata.md` | File exists |

## Completion criteria

- The path on line 215 of `docs/00_governance/governance_04_documentation-checks.md` resolves to an existing file.
- No remaining `docs/governance_0N_*` patterns in this file.

## Out of scope

- Other stale paths in `docs/00_governance/governance_04_documentation-checks.md` (if any).
- Changes to other files.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261002-135917 | 20261002-135917 | REQ-003 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test needed for path string fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261002-135917 | 20261002-135917 | REQ-003 |
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
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md