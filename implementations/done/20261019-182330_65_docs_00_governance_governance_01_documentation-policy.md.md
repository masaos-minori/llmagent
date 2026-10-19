## Goal
- Update `docs/00_governance/governance_01_documentation-policy.md` for the grouped ADR file names (`REQ-002` (replace old ADR file names), `REQ-005` (state the naming rule and registry)).

## Scope
- In scope: `docs/00_governance/governance_01_documentation-policy.md` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- Names only; no prose rewording beyond the listed changes.

## Alternatives considered
- N/A: the Plan fixes the approach.

## Implementation
### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure
1. Update the patterns `adr_02_{NNN}_*.md`, `adr_02_NNN_*.md`, and the `adr_02_007_*.md`, `adr_02_012_*.md`, `adr_02_013_*.md` glob forms (lines about 70, 74, 124, 125, 134, and 302) to the grouped shape, for example `adr_02_??_{NNN}_*.md`.
### Method
- Only pattern or table text changes; no full ADR file name appears.
### Details
- 0 full name reference(s) plus the pattern text `adr_02_{NNN}_*.md` and `adr_02_NNN_*.md` (Resolution Matrix, claim types, heading rule).

## Compatibility considerations
- Documentation only; files reach the deployed docs directory with the next deploy.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py`, `check_docs_quality.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, and (for ADR-related content) `check_adr_reference.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`.

## Completion criteria
- No old ADR file name or glob/placeholder form remains in the file.
- The document checkers pass.

## Out of Scope
- Modifying any file other than the target file; ADR decisions, IDs, status, and invariants; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the references and patterns | Completed | 20261019-204703 | 20261019-204703 |  |
| 2 | Run the documentation checkers | Completed | 20261019-204703 | 20261019-204703 | Stale clean; 6 pattern lines updated to adr_02_??_{NNN}_*.md; quality, content_policy --strict, japanese, structure pass. |

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
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: issues/done/20261019-170548_adrname001_group-adr-file-names-by-theme.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-173513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-182330
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md