# Implementation Procedure: Fix stale governance path in tools/check_known_deviation_sync.py

## Goal

Replace the stale governance document path references (`docs/00_governance_03_issue-and-uncertainty-management.md`) with the actual existing path (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`) in `tools/check_known_deviation_sync.py`.

## Scope

- Modify only `tools/check_known_deviation_sync.py`.
- In-Scope: Replace the stale path strings on lines 54, 68, and 137.
- Out-of-Scope: Changing any other content in `tools/check_known_deviation_sync.py`.

## Assumptions

- The correct path is `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (confirmed by filesystem inspection).
- No other references to `docs/00_governance_0N_*` exist in this file.

## Design decisions

- **Approach**: Direct string replacement — replace `docs/00_governance_03_issue-and-uncertainty-management.md` with `docs/00_governance/governance_03_issue-and-uncertainty-management.md` on lines 54, 68, and 137.
- **Alternatives considered**: None — this is a straightforward path correction.

## Alternatives considered

None — direct replacement is the only sensible approach for stale path strings.

## Implementation

### Target file

`tools/check_known_deviation_sync.py`

### Procedure

Replace the stale path strings on lines 54, 68, and 137 with the correct path.

### Method

Edit `tools/check_known_deviation_sync.py`:
- Line 54: change `docs/00_governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- Line 68: change `docs/00_governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- Line 137: change `docs/00_governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Details

Lines 54, 68, and 137 currently read:
```
# `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 and
# same line) -- see docs/00_governance_03_issue-and-uncertainty-management.md
consolidated `docs/00_governance_03_issue-and-uncertainty-management.md`
```

Change to:
```
# `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 and
# same line) -- see docs/00_governance/governance_03_issue-and-uncertainty-management.md
consolidated `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
```

Only the path strings change; surrounding text is preserved.

## Compatibility considerations

- The corrected path resolves to an existing file (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`).
- No other tool or document depends on the old prefixed form.

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path strings if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_known_deviation_sync.py` | Path resolution | `grep -rnE "docs/00_governance_0[0-4]_" tools/check_known_deviation_sync.py` | No matches |
| `tools/check_known_deviation_sync.py` | Format + lint | `uv run ruff format tools/check_known_deviation_sync.py` then `uv run ruff check tools/check_known_deviation_sync.py` | Clean |
| `tools/check_known_deviation_sync.py` | Type check | `uv run mypy tools/check_known_deviation_sync.py` | Pass |

## Completion criteria

- All `docs/00_governance_0N_*` references replaced with `docs/00_governance/governance_0N_*` in `tools/check_known_deviation_sync.py`.
- Corrected paths resolve to existing files.

## Out of scope

- Other stale paths in `tools/check_known_deviation_sync.py` (if any).
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
- **Related target files**: tools/check_known_deviation_sync.py
