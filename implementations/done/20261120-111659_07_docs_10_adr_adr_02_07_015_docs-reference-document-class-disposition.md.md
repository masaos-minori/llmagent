## Goal

- Record ADR-015 verification as an `### Automated Tests` table so the reverse rule (`REQ-005`) finds the evidence the Index cites for ADR-015 INV-01 (`REQ-002`, table form).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `## Verification` section (Plan step 2). Fallout of `REQ-005`: the Index cites `tests/tools/test_generate_reference_table.py::TestCheckDrift::test_live_docs_have_no_drift` for ADR-015 INV-01 while the body holds a bullet only.

## Assumptions

- One row: INV-01, `Static Check`, `Blocking` `Yes`, as the bullet states; the description and the CI `lint` job statement move into the `Test` cell.

## Design decisions

- Cite `uv run python tools/generate_reference_table.py --check` and the full test node in `Implementation`.

## Alternatives considered

N/A: a format conversion; the Plan fixes the shape.

## Implementation
### Target file
`docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`
### Procedure
1. Replace the single `**Test**:` bullet with `### Automated Tests` and a one-row table `Test | Verifies | Type | Blocking | Implementation`.
2. `Implementation` cites `tools/generate_reference_table.py --check` and `tests/tools/test_generate_reference_table.py::TestCheckDrift::test_live_docs_have_no_drift`.
### Method
- Direct text edit.
### Details
- Keep the sentence that the check runs in the CI `lint` job in the `Test` cell.

## Compatibility considerations

N/A: documentation row; no decision text changes.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- The table exists with one INV-01 row citing the test node, and `uv run python tools/check_adr_invariant_matrix.py` exits 0 (AC-3).

## Out of Scope

- Invariant text, the Index row, and any pending amendment bullet.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Convert the Verification bullet to an Automated Tests table (Plan step 2) | Completed | 20261120 | 20261120 | Bullet converted to one-row Automated Tests table; tool command token kept |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | — | 20261120 | 6 of 7 doc checkers exit 0; pytest 27 passed; check_adr_preservation: 1 citation token swapped (TestCheckDrift -> full node), procedure-authorized expansion, no changed invariant |

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
- **Requirement ID**: `REQ-002` (table form)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`