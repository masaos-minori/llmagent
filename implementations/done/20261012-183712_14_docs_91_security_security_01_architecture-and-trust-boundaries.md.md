## Goal
- Update the web-search row's server-side key (`REQ-005`)

## Scope
- The web-search row of the trust boundary table in `docs/91_security/security_01_architecture-and-trust-boundaries.md`.

## Assumptions
- Lightweight fill: change one phrase in English.

## Design decisions
- Only the key name changes; keep the allowlist and browser-fetch protections text.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure
1. In the authentication cell of the web-search row, replace the server-side key browser_auth_token with auth_token.

### Method
- Do not reflow the table.

### Details
- Leave the other columns unchanged.

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
- The row names auth_token and the checkers pass.

## Out of scope
- Other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the web-search row | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: docs/91_security/security_01_architecture-and-trust-boundaries.md |
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
- **Related target files**: docs/91_security/security_01_architecture-and-trust-boundaries.md