## Goal

- Update section 12 of `governance_04` so it describes the rules that landed in `check_adr_invariant_matrix.py` (`REQ-010`, documentation sync).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the paragraph of `### 12. ADR Invariant Matrix Checks` (Plan step 8). Fallout, outside the Issue's Target Files.
- Execute after the checker rules of Plan steps 5 to 7 landed; add the gated rules when Plan steps 9 and 12 land.

## Assumptions

- The paragraph currently states the empty-cell rule and the containment rule only; the new rules are added beside them.

## Design decisions

- Keep the single paragraph and extend its sentence about `check_adr_invariant_matrix.py`; do not add a table.

## Alternatives considered

N/A: a one-paragraph text update.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`
### Procedure
1. In section 12, after the empty-cell and containment sentence, state that a missing `Verifies` or `Implementation` column of an ADR body `### Automated Tests` table, Index test files with no ADR body evidence, and a Manual or Partial row without `Cadence:` or `Expected evidence:` each fail the check.
### Method
- Direct text edit.
### Details
- Describe behavior only; do not copy code or finding message text.

## Compatibility considerations

N/A: documentation row.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_docs_consistency.py --domain deployment`.

## Completion criteria

- Section 12 describes the landed rules and the documentation checkers pass (AC-6).

## Out of Scope

- Other sections, the Governance Verification Matrix rows, and the Accepted Limits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update section 12 (Plan step 8) | Completed | — | 2026-11-20 | Section 12 now states the missing-column, Index-only-evidence, Not verified plus Blocking, and Manual/Partial Cadence rules |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | — | 2026-11-20 | check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_japanese, check_docs_consistency --domain deployment all exit 0 |

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
- **Requirement ID**: `REQ-010` (documentation sync)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`