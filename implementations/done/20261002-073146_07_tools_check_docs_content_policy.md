# Implementation Procedure: Fix stale governance path in tools/check_docs_content_policy.py

## Goal

Replace the stale governance document path references (`docs/00_governance_04_documentation-checks.md`, `docs/00_governance_02_documentation-metadata.md`) with the actual existing paths (`docs/00_governance/governance_04_documentation-checks.md`, `docs/00_governance/governance_02_documentation-metadata.md`) in `tools/check_docs_content_policy.py`.

## Scope

- Modify only `tools/check_docs_content_policy.py`.
- In-Scope: Replace the stale path strings on lines 9 and 319.
- Out-of-Scope: Changing any other content in `tools/check_docs_content_policy.py`.

## Assumptions

- The correct paths are `docs/00_governance/governance_04_documentation-checks.md` and `docs/00_governance/governance_02_documentation-metadata.md` (confirmed by filesystem inspection).
- No other references to `docs/00_governance_0N_*` exist in this file.

## Design decisions

- **Approach**: Direct string replacement — replace `docs/00_governance_04_documentation-checks.md` with `docs/00_governance/governance_04_documentation-checks.md` on line 9, and `docs/00_governance_02_documentation-metadata.md` with `docs/00_governance/governance_02_documentation-metadata.md` on line 319.
- **Alternatives considered**: None — this is a straightforward path correction.

## Alternatives considered

None — direct replacement is the only sensible approach for stale path strings.

## Implementation

### Target file

`tools/check_docs_content_policy.py`

### Procedure

Replace the stale path strings on lines 9 and 319 with the correct paths.

### Method

Edit `tools/check_docs_content_policy.py`:
- Line 9: change `docs/00_governance_04_documentation-checks.md` → `docs/00_governance/governance_04_documentation-checks.md`
- Line 319: change `docs/00_governance_02_documentation-metadata.md` → `docs/00_governance/governance_02_documentation-metadata.md`

### Details

Line 9 currently reads:
```
docs/00_governance_04_documentation-checks.md's Governance Verification
```

Change to:
```
docs/00_governance/governance_04_documentation-checks.md's Governance Verification
```

Line 319 currently reads:
```
not a mechanical restatement — see docs/00_governance_02_documentation-metadata.md's
```

Change to:
```
not a mechanical restatement — see docs/00_governance/governance_02_documentation-metadata.md's
```

Only the path strings change; surrounding text is preserved.

## Compatibility considerations

- The corrected paths resolve to existing files (`docs/00_governance/governance_04_documentation-checks.md`, `docs/00_governance/governance_02_documentation-metadata.md`).
- No other tool or document depends on the old prefixed forms.

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path strings if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_docs_content_policy.py` | Path resolution | `grep -rnE "docs/00_governance_0[0-4]_" tools/check_docs_content_policy.py` | No matches |
| `tools/check_docs_content_policy.py` | Format + lint | `uv run ruff format tools/check_docs_content_policy.py` then `uv run ruff check tools/check_docs_content_policy.py` | Clean |
| `tools/check_docs_content_policy.py` | Type check | `uv run mypy tools/check_docs_content_policy.py` | Pass |

## Completion criteria

- All `docs/00_governance_0N_*` references replaced with `docs/00_governance/governance_0N_*` in `tools/check_docs_content_policy.py`.
- Corrected paths resolve to existing files.

## Out of scope

- Other stale paths in `tools/check_docs_content_policy.py` (if any).
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
- **Related target files**: tools/check_docs_content_policy.py
