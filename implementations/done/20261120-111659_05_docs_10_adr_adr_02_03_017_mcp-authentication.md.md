## Goal

- Add an `Implementation` column to the ADR-017 `### Automated Tests` table and move the test citations out of the `Test` cell, so the checker reads ADR-017 and the Index can mirror it (`REQ-001`, evidence column; `REQ-003`, Index row source).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `### Automated Tests` table (Plan step 1). Invariants, Failure Policy and Approval are out of scope.
- Execute before the Index procedure.

## Assumptions

- The table keeps one row per current row; only the column and the cell contents change.
- Bare test names in the `Test` cell (for example `test_disabled_server_without_token_passes_mcp_auth`) become full node paths in the new column, verified with `rg` before writing.

## Design decisions

- `Test` becomes a short description of what the test proves; `Implementation` holds the `tests/path.py::Class::test` citations.

## Alternatives considered

N/A: a column addition; the Plan fixes the shape.

## Implementation
### Target file
`docs/10_adr/adr_02_03_017_mcp-authentication.md`
### Procedure
1. Add the header cell `Implementation` and a matching cell to each row.
2. For each row, replace the `Test` cell with a one-clause description and move the cited nodes to `Implementation` with full repository paths: `tests/agent/test_startup_validation.py::TestMcpAuthDisabledServers::...`, `tests/mcp_servers/test_require_auth_token.py::...`, `tests/mcp_servers/test_mcp_server_base.py::TestAttachAuthMiddleware::...`.
3. Keep every `Verifies`, `Type` and `Blocking` value (INV-01 `Unit` `Yes`, and so on).
### Method
- Direct table edit.
### Details
- A row that cites several test functions lists each as its own full node, comma-separated.

## Compatibility considerations

N/A: documentation row.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- The table has the five columns and every row cites full node paths that resolve (AC-1).
- `uv run python tools/check_adr_invariant_matrix.py` exits 0.

## Out of Scope

- Invariant text, Failure Policy, and any change of a Blocking value.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Implementation column and move the citations (Plan step 1) | Completed | 20261120 | 20261120 | Implementation column added; Test cells rewritten as descriptions; 11 full node citations, all verified present in test sources |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | — | 20261120 | 6 of 7 doc checkers exit 0; pytest on the 3 cited files: 96 passed; check_adr_preservation reports 6 'test citation added' ERRORs, all procedure-authorized full-path expansions of bare names (precedent: done/20261118-212828_03 Final Report) |

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
- **Requirement ID**: `REQ-001` (evidence column), `REQ-003` (Index row source)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/10_adr/adr_02_03_017_mcp-authentication.md`