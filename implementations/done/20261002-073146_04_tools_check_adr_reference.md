# Implementation Procedure: Fix stale governance path in tools/check_adr_reference.py

## Goal

Replace the stale governance document path reference (`docs/00_governance_04_documentation-checks.md`) with the actual existing path (`docs/00_governance/governance_04_documentation-checks.md`) in `tools/check_adr_reference.py`.

## Scope

- Modify only `tools/check_adr_reference.py`.
- In-Scope: Replace the stale path string on line 12.
- Out-of-Scope: Changing any other content in `tools/check_adr_reference.py`.

## Assumptions

- The correct path is `docs/00_governance/governance_04_documentation-checks.md` (confirmed by filesystem inspection).
- No other references to `docs/00_governance_0N_*` exist in this file.

## Design decisions

- **Approach**: Direct string replacement — replace `docs/00_governance_04_documentation-checks.md` with `docs/00_governance/governance_04_documentation-checks.md` on line 12.
- **Alternatives considered**: None — this is a straightforward path correction.

## Alternatives considered

None — direct replacement is the only sensible approach for a stale path string.

## Implementation

### Target file

`tools/check_adr_reference.py`

### Procedure

Replace the stale path string on line 12 with the correct path.

### Method

Edit `tools/check_adr_reference.py` line 12: change `docs/00_governance_04_documentation-checks.md` → `docs/00_governance/governance_04_documentation-checks.md`.

### Details

Line 12 currently reads:
```
mandate (per docs/00_governance_04_documentation-checks.md GV-014
```

Change to:
```
mandate (per docs/00_governance/governance_04_documentation-checks.md GV-014
```

Only the path string changes; surrounding text is preserved.

## Compatibility considerations

- The corrected path resolves to an existing file (`docs/00_governance/governance_04_documentation-checks.md`).
- No other tool or document depends on the old prefixed form.

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path string if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_adr_reference.py` | Path resolution | `grep -rnE "docs/00_governance_0[0-4]_" tools/check_adr_reference.py` | No matches |
| `tools/check_adr_reference.py` | Format + lint | `uv run ruff format tools/check_adr_reference.py` then `uv run ruff check tools/check_adr_reference.py` | Clean |
| `tools/check_adr_reference.py` | Type check | `uv run mypy tools/check_adr_reference.py` | Pass |

## Completion criteria

- The path on line 12 of `tools/check_adr_reference.py` resolves to an existing file.
- No remaining `docs/00_governance_0N_*` patterns in this file.

## Out of scope

- Other stale paths in `tools/check_adr_reference.py` (if any).
- Changes to other files.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | REQ-002 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test needed for path string fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | REQ-002 |
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
- **Requirement ID**: REQ-002 — Replace stale `docs/00_governance_0N_*` references
- **Source issue**: issues/20261001-103636_govpath001_correct-stale-governance-document-path-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-072411_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261002-073146
- **Related target files**: tools/check_adr_reference.py
