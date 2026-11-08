## Goal
Make ADR-004 reference the ADR-010 decision table instead of restating the fallback condition list (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit
Edits the cross-cutting audit Baseline line of `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`. No invariant or decision text changes.

## Assumptions
- Depends on the ADR-010 table existing (seq 01 of this Plan).
- `check_adr_preservation.py` must report no ERROR for ADR-004.

## Design decisions
- Replace the restated list with a one-sentence reference to the ADR-010 decision table; keep the statement that ADR-010 is the sole Accepted fallback ADR.

## Alternatives considered
N/A: one-line wording change

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Procedure
1. Locate the Baseline bullet of the cross-cutting audit (search for "sole Accepted ADR defining fallback").
2. Replace the enumerated conditions with a reference to the ADR-010 decision table.

### Method
Documentation edit of one bullet.

### Details
- Leave Decision Group 10 items untouched.

## Compatibility considerations
Documentation only.

## Security considerations
N/A: documentation-only change; no secret, permission, or input-handling behavior changes

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`: no ERROR
- `uv run python tools/check_docs_quality.py`, `check_docs_content_policy.py`: no findings

## Completion criteria
- ADR-004 contains no restated list of ADR-010 fallback conditions and points to the ADR-010 table.

## Out of Scope
- Invariant and decision text of ADR-004.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document as described in Implementation > Procedure | Pending | — | — |  |
| 2 | Run the documentation checkers named in the Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-005` (ADR-004 references the ADR-010 table)
- **Source issue**: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-091446_adrrag001_rag-fallback-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111044
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
