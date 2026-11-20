## Goal

- Give the ADR-004 `### Automated Tests` table an `Implementation` column that holds each row's test citations or explicit status, and add the INV-14 row, so the checker can compare the table with the Index (`REQ-001`, evidence column; `REQ-003`, body matches the Index).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `### Automated Tests` table of the ADR body (Plan step 1). Decisions, invariants and the Approval section are out of scope.
- Execute before the Index procedure and before the checker rules of Plan steps 5 and 6.

## Assumptions

- The Index rows ADR-004 INV-07, INV-08, INV-09, INV-10 and INV-14 are the source of the citations; the body cites a subset of each invariant's Index files so the containment rule holds.
- The new INV-14 row takes `Blocking` `Yes`, mirroring the Index Gate `Deployment Blocking`; if the ADR Invariants text says otherwise, report a Plan Gap instead of choosing.
- The reverse rule (Plan step 6) needs a test file in the body for every invariant whose Index row cites one: INV-07, INV-08, INV-09, INV-10 and INV-14.

## Design decisions

- Rename the existing `Status` column to `Implementation` and keep each status word first, followed by the citations, so no status text is lost.
- Cite tests as `tests/path.py::Class::test` (full repository path) so rule 3 of the checker resolves them.

## Alternatives considered

N/A: a column rename and cell edits; the Plan fixes the shape.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
### Procedure
1. In the `### Automated Tests` table of `## Verification`, rename the `Status` header to `Implementation`.
2. Add citations from the Index rows to the Implementation cells: the INV-06 and INV-07 row and the INV-10 row cite `tests/agent/test_production_config_validator.py` and `tests/agent/test_failure_handling_policy_cross_cutting.py`; the INV-08 row cites `tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers`; the INV-09 row cites that node and `tests/shared/test_mcp_config.py::TestMcpServerConfigValidation::test_subprocess_non_required_rejected`; the posture row keeps its two files.
3. Add the INV-14 row (`Unit`, `Yes`) citing the nodes the Index INV-14 row cites (`tests/shared/test_mcp_config.py::TestRequiredDefault`, `tests/shared/test_component_mandatoriness.py::test_unknown_component_raises_typed_error`, `tests/agent/test_startup_validation.py::TestComponentMandatorinessAbort`).
4. Leave the other rows' status text as the Implementation cell, unchanged in meaning (the INV-03, INV-05, INV-11 to INV-12 and INV-15 to INV-16 rows).
### Method
- Direct table edit; verify each cited node exists with `rg` before writing it.
### Details
- Do not change any `Verifies`, `Type` or `Blocking` value of an existing row.

## Compatibility considerations

N/A: documentation row; the checker already accepts an `Implementation` column.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- The table has the columns `Test`, `Verifies`, `Type`, `Blocking`, `Implementation`, and an INV-14 row (AC-1).
- `uv run python tools/check_adr_invariant_matrix.py` exits 0 and the body cites a test file for ADR-004 INV-07, INV-08, INV-09, INV-10 and INV-14.

## Out of Scope

- The Exceptions, Known Deviations and Approval sections, and the adrchk015 front matter edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the column, add the citations and the INV-14 row (Plan step 1) | Completed | 20261120 | 20261120 | Status->Implementation rename; INV-07/08/09/10 citations added; INV-14 row added; size ceiling re-accepted at 36267 in tools/check_docs_structure.py |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | — | 20261120 | 7 doc checkers exit 0 (adr_structure 1 pre-existing ADR-015 warning); check_adr_preservation clean (citations reuse tokens already in HEAD); pytest on cited nodes: 73 passed |

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
- **Requirement ID**: `REQ-001` (evidence column), `REQ-003` (body matches the Index)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`