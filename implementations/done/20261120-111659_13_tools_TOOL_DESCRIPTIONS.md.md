## Goal

- State the new `check_adr_invariant_matrix.py` rules in the two rows of `tools/TOOL_DESCRIPTIONS.md` (`REQ-010`, documentation sync).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `check_adr_invariant_matrix.py` rows of the tool list and of the detailed table (Plan step 8). Fallout required by `AGENTS.md` Global Rule 9, outside the Issue's Target Files.
- Execute after the checker rules of Plan steps 5 to 7 landed; add the gated rules (grammar, Not verified plus Blocking) when Plan steps 9 and 12 land.

## Assumptions

- Only the rules that landed are described; a gated rule is added in the commit that lands it.

## Design decisions

- Extend the existing sentences of both rows instead of adding a row.

## Alternatives considered

N/A: a two-row text update.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
1. In both rows, state that an `### Automated Tests` table without a `Verifies` or `Implementation` column is an error, that Index test files with no ADR body evidence are an error, and that the Manual and Partial `Cadence:` and `Expected evidence:` fields are required as an error.
2. Remove any wording that says the body table is skipped when a column is missing.
### Method
- Direct text edit of two rows.
### Details
- Keep the row structure and the `--format json` remark.

## Compatibility considerations

N/A: documentation row.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py`, `uv run python tools/check_docs_quality.py`.

## Completion criteria

- Both rows describe the landed rules and the sync checker passes (AC-6).

## Out of Scope

- Other tools' rows and any new tool row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two check_adr_invariant_matrix.py rows (Plan step 8) | Completed | — | 2026-11-20 | Both rows updated; also documented tools/_adr_matrix_core.py (split fallout of the checker size gate) as a new shared-base row pair; registry/manifests/invariant_coverage.yaml regenerated for the new Index rows |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | — | 2026-11-20 | check_tool_descriptions_sync.py exit 0; no 'column skipped' wording remained |

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
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`