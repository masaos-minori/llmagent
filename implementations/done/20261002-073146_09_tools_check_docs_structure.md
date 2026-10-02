# Implementation Procedure: Fix stale governance path in tools/check_docs_structure.py

## Goal

Replace the stale governance document path reference (`docs/00_governance_03_issue-and-uncertainty-management.md`) with the actual existing path (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`) in `tools/check_docs_structure.py`.

## Scope

- Modify only `tools/check_docs_structure.py`.
- In-Scope: Replace the stale path string on line 33.
- Out-of-Scope: Changing any other content in `tools/check_docs_structure.py`.

## Assumptions

- The correct path is `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (confirmed by filesystem inspection).
- No other references to `docs/00_governance_0N_*` exist in this file.

## Design decisions

- **Approach**: Direct string replacement — replace `docs/00_governance_03_issue-and-uncertainty-management.md` with `docs/00_governance/governance_03_issue-and-uncertainty-management.md` on line 33.
- **Alternatives considered**: None — this is a straightforward path correction.

## Alternatives considered

None — direct replacement is the only sensible approach for a stale path string.

## Implementation

### Target file

`tools/check_docs_structure.py`

### Procedure

Replace the stale path string on line 33 with the correct path.

### Method

Edit `tools/check_docs_structure.py` line 33: change `docs/00_governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.

### Details

Line 33 currently reads:
```
# docs/00_governance_03_issue-and-uncertainty-management.md at ~46KB remains
```

Change to:
```
# docs/00_governance/governance_03_issue-and-uncertainty-management.md at ~46KB remains
```

Only the path string changes; surrounding text is preserved.

## Compatibility considerations

- The corrected path resolves to an existing file (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`).
- No other tool or document depends on the old prefixed form.

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path string if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_docs_structure.py` | Path resolution | `grep -rnE "docs/00_governance_0[0-4]_" tools/check_docs_structure.py` | No matches |
| `tools/check_docs_structure.py` | Format + lint | `uv run ruff format tools/check_docs_structure.py` then `uv run ruff check tools/check_docs_structure.py` | Clean |
| `tools/check_docs_structure.py` | Type check | `uv run mypy tools/check_docs_structure.py` | Pass |

## Completion criteria

- The path on line 33 of `tools/check_docs_structure.py` resolves to an existing file.
- No remaining `docs/00_governance_0N_*` patterns in this file.

## Out of scope

- Other stale paths in `tools/check_docs_structure.py` (if any).
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
- **Related target files**: tools/check_docs_structure.py
