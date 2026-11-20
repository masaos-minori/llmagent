## Goal

- Name INV-06 in the ADR-007 body row that cites `test_stdio_transport_rejected`, so the evidence the Index cites for ADR-007 INV-06 exists in the body (`REQ-003`, body matches the Index).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one `Verifies` cell in the `### Automated Tests` table (Plan step 3). A fallout of the reverse rule (`REQ-005`), outside the Issue's Target Files and recorded in the Plan's table.
- The pending adrchk015 procedure for this file edits other regions; the overlap is compatible (Plan Assumption A1).

## Assumptions

- The body rows for INV-03 and INV-04 already cite `tests/shared/test_mcp_config.py::TestMcpServerConfigValidation::test_stdio_transport_rejected`; INV-06 states that stdio is not a valid transport value in the configuration schema, which that test verifies.

## Design decisions

- Add INV-06 to the `Verifies` cell of the INV-04 row (`INV-04, INV-06`) rather than adding a duplicate row.

## Alternatives considered

N/A: a one-cell edit.

## Implementation
### Target file
`docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`
### Procedure
1. Confirm with `rg -n "test_stdio_transport_rejected" docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` that the INV-04 row cites the test; change its `Verifies` cell to `INV-04, INV-06`.
### Method
- Direct one-cell edit.
### Details
- No other cell, status or Blocking value changes.

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

- The row names INV-06 and the body cites a test file for it; `uv run python tools/check_adr_invariant_matrix.py` exits 0 (AC-3).

## Out of Scope

- The adrchk015 edits, the Index row, and any Blocking value.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Name INV-06 in the INV-04 row (Plan step 3) | Completed | 20261120 | 20261120 | INV-04 row Verifies cell set to 'INV-04, INV-06'; no other cell changed |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | — | 20261120 | 6 of 7 doc checkers exit 0; check_adr_preservation clean for ADR-007; matrix now has body evidence for the Index ADR-007 INV-06 row |

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
- **Requirement ID**: `REQ-003` (body matches the Index)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`