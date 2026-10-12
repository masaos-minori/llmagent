## Goal
- Describe the shared auth_token in the web-search configuration table instead of the browser-only token (`REQ-005`)

## Scope
- The configuration key table in `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`.

## Assumptions
- Lightweight fill: one table row in English.
- The web-search server now authenticates every protected route with the shared token.

## Design decisions
- State what the key is and that it is shared with the agent's web-search entry; do not repeat the setup steps.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`

### Procedure
1. Replace the row for the browser token with a row for the key auth_token: Bearer token required on every request to the server (not only the browser tool), supplied by the same environment variable as the agent's web-search entry.

### Method
- Keep the table's style; wrap identifiers in backticks.

### Details
- Do not add the environment variable's value.

## Compatibility considerations
Documentation only.

## Security considerations
N/A: documentation only; no token values are written.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- The documentation checkers named in `routing.md` Tools "When to run which tool" for an edited docs file (quality, structure, content policy, the consistency check for the mcp or deployment domain, and the English-only check).
- Execution order for the whole plan: tests first (procedures 05, 06, 07, 08, 09, 04), then the code (01, 02, 03), then the documentation (10 to 15); the new tests must be seen failing before the code is edited.

## Completion criteria
- The row describes the shared token and the checkers pass.

## Out of scope
- The other documents (procedures 11 to 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the configuration table row | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: docs/22_mcp/mcp_04_01_web-search-file-read-github.md |
| 2 | Run the documentation checkers | Completed | 20261012-184531 | 20261012-184531 | documentation checkers pass |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/done/20261012-182600_mcp005_web-search-tool-calls-return-401-when-browser_auth_token-differs-from-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183712
- **Related target files**: docs/22_mcp/mcp_04_01_web-search-file-read-github.md