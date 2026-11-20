## Goal

- Record ADR-016 verification as an `### Automated Tests` table with an `Implementation` column, so the checker can read it and the Index can mirror it (`REQ-002`, table form; `REQ-003`, Index row source).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `## Verification` section (Plan step 2). Decision text and Implementation Notes are out of scope.
- The pending adrchk015 procedure for this file edits Decision, Summary and Implementation Notes, and pins line numbers; this edit is below the Decision text, so the overlap is compatible (Plan Assumption A1), and that procedure revalidates its own lines.

## Assumptions

- The three bullets map to rows: `check_adr_authority.py` (INV-01, INV-02, INV-05), `generate_adr_authority.py --check` (INV-03), `check_adr_reference.py` (INV-04); the Coverage note stays as prose.
- Test nodes come from `tests/tools/test_adr_authority.py`, `tests/tools/test_generate_adr_authority.py` and `tests/tools/test_check_adr_reference.py`; each node is verified with `rg` before it is cited, and a row with no suitable node cites the tool command only.

## Design decisions

- Keep `Verifies`, `Type` (`Static Check`) and `Blocking` (`Yes`) as the bullets state them.

## Alternatives considered

N/A: a format conversion; the Plan fixes the shape.

## Implementation
### Target file
`docs/10_adr/adr_02_07_016_adr-authority-model.md`
### Procedure
1. Replace the three `**Test**:` bullets with `### Automated Tests` and a table `Test | Verifies | Type | Blocking | Implementation`, one row per bullet, the `Test` cell carrying the bullet's description.
2. Put the tool command and the test nodes in `Implementation`, for example `tests/tools/test_adr_authority.py::test_dup_primary_fails`, `tests/tools/test_adr_authority.py::test_typed_cycle_fails`, `tests/tools/test_adr_authority.py::test_assumption_drift_against_live_config_shape`, `tests/tools/test_generate_adr_authority.py::test_live_docs_and_model_have_no_drift`.
3. Keep the `- **Coverage**:` note after the table.
### Method
- Direct text edit; verify each node with `rg`.
### Details
- Citations use the full repository path so rule 3 of the checker resolves them.

## Compatibility considerations

N/A: documentation row; no decision text changes, and `tools/check_adr_preservation.py` confirms it.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- `## Verification` holds an `### Automated Tests` table with the five columns and rows for INV-01 to INV-05 coverage as the bullets stated (AC-1).
- `uv run python tools/check_adr_invariant_matrix.py` exits 0; `check_adr_preservation.py` reports no changed invariant.

## Out of Scope

- Decision, Summary and Implementation Notes text (adrchk015), and the Index rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Convert the Verification bullets to an Automated Tests table (Plan step 2) | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (table form), `REQ-003` (Index row source)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/10_adr/adr_02_07_016_adr-authority-model.md`
