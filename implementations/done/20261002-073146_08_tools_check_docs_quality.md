# Implementation Procedure: Fix stale governance path in tools/check_docs_quality.py

## Goal

Replace the stale governance document path references (`docs/00_governance_01_documentation-policy.md`, `docs/00_governance_04_documentation-checks.md`) with the actual existing paths (`docs/00_governance/governance_01_documentation-policy.md`, `docs/00_governance/governance_04_documentation-checks.md`) in `tools/check_docs_quality.py`.

## Scope

- Modify only `tools/check_docs_quality.py`.
- In-Scope: Replace the stale path strings on lines 516 and 517.
- Out-of-Scope: Changing any other content in `tools/check_docs_quality.py`.

## Assumptions

- The correct paths are `docs/00_governance/governance_01_documentation-policy.md` and `docs/00_governance/governance_04_documentation-checks.md` (confirmed by filesystem inspection).
- No other references to `docs/00_governance_0N_*` exist in this file.

## Design decisions

- **Approach**: Direct string replacement — replace `docs/00_governance_01_documentation-policy.md` with `docs/00_governance/governance_01_documentation-policy.md` on line 516, and `docs/00_governance_04_documentation-checks.md` with `docs/00_governance/governance_04_documentation-checks.md` on line 517.
- **Alternatives considered**: None — this is a straightforward path correction.

## Alternatives considered

None — direct replacement is the only sensible approach for stale path strings.

## Implementation

### Target file

`tools/check_docs_quality.py`

### Procedure

Replace the stale path strings on lines 516 and 517 with the correct paths.

### Method

Edit `tools/check_docs_quality.py`:
- Line 516: change `docs/00_governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`
- Line 517: change `docs/00_governance_04_documentation-checks.md` → `docs/00_governance/governance_04_documentation-checks.md`

### Details

Lines 516-517 currently read:
```
    docs/00_governance_01_documentation-policy.md's 'Merge Conditions' vs.
    docs/00_governance_04_documentation-checks.md's 'Merge Condition
```

Change to:
```
    docs/00_governance/governance_01_documentation-policy.md's 'Merge Conditions' vs.
    docs/00_governance/governance_04_documentation-checks.md's 'Merge Condition
```

Only the path strings change; surrounding text is preserved.

## Compatibility considerations

- The corrected paths resolve to existing files (`docs/00_governance/governance_01_documentation-policy.md`, `docs/00_governance/governance_04_documentation-checks.md`).
- No other tool or document depends on the old prefixed forms.

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path strings if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_docs_quality.py` | Path resolution | `grep -rnE "docs/00_governance_0[0-4]_" tools/check_docs_quality.py` | No matches |
| `tools/check_docs_quality.py` | Format + lint | `uv run ruff format tools/check_docs_quality.py` then `uv run ruff check tools/check_docs_quality.py` | Clean |
| `tools/check_docs_quality.py` | Type check | `uv run mypy tools/check_docs_quality.py` | Pass |

## Completion criteria

- All `docs/00_governance_0N_*` references replaced with `docs/00_governance/governance_0N_*` in `tools/check_docs_quality.py`.
- Corrected paths resolve to existing files.

## Out of scope

- Other stale paths in `tools/check_docs_quality.py` (if any).
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
- **Related target files**: tools/check_docs_quality.py
