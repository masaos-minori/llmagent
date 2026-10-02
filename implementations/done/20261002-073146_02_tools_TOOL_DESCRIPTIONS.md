# Implementation Procedure: Fix stale governance path in tools/TOOL_DESCRIPTIONS.md

## Goal

Replace stale governance document path references (`docs/00_governance_0N_*`) with actual existing paths (`docs/00_governance/governance_0N_*`) in `tools/TOOL_DESCRIPTIONS.md`.

## Scope

- Modify only `tools/TOOL_DESCRIPTIONS.md`.
- In-Scope: Replace stale paths on lines 60, 63, 64.
- Out-of-Scope: Changing any other content in `tools/TOOL_DESCRIPTIONS.md`.

## Assumptions

- The correct paths are `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (confirmed by filesystem inspection).
- No other references to `docs/00_governance_0N_*` exist in `tools/TOOL_DESCRIPTIONS.md`.

## Design decisions

- **Approach**: Direct string replacement — replace `docs/00_governance_03_issue-and-uncertainty-management.md` with `docs/00_governance/governance_03_issue-and-uncertainty-management.md` on lines 60, 63, 64.
- **Alternatives considered**: None — this is a straightforward path correction.

## Alternatives considered

None — direct replacement is the only sensible approach for stale path strings.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

Replace the stale path strings on lines 60, 63, 64 with the correct paths.

### Method

Edit `tools/TOOL_DESCRIPTIONS.md`:
- Line 60: change `docs/00_governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- Line 63: change `docs/00_governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- Line 64: change `docs/00_governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

Only the path strings change; surrounding text is preserved.

### Details

The three occurrences are in tool description entries for `check_needs_confirmation_inventory.py`, `check_known_deviation_sync.py`, and `check_issue_inventory_conformance.py`. Each mentions the old prefixed form `docs/00_governance_03_issue-and-uncertainty-management.md` which does not exist as a file path.

## Compatibility considerations

- The corrected paths resolve to existing files (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`).
- No other tool or document depends on the old prefixed form.

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path strings if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Path resolution | `grep -rnE "docs/00_governance_0[0-4]_" tools/TOOL_DESCRIPTIONS.md` | No matches |
| `tools/TOOL_DESCRIPTIONS.md` | File existence | `test -f docs/00_governance/governance_03_issue-and-uncertainty-management.md` | File exists |

## Completion criteria

- All `docs/00_governance_0N_*` references replaced with `docs/00_governance/governance_0N_*` in `tools/TOOL_DESCRIPTIONS.md`.
- Corrected paths resolve to existing files.

## Out of scope

- Other stale paths in `tools/TOOL_DESCRIPTIONS.md` (if any).
- Changes to other files.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261002-120249 | 20261002-120249 | REQ-002 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test needed for path string fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261002-120249 | 20261002-120249 | REQ-002 |
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
- **Related target files**: tools/TOOL_DESCRIPTIONS.md