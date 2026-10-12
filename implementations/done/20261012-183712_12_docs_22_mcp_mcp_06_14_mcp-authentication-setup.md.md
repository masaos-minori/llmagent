## Goal
- Replace the two-token description added by mcp004 with the shared-token model (`REQ-005`)

## Scope
- The web-search bullet under Setup Requirements and the web-search troubleshooting entry in `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`.

## Assumptions
- Lightweight fill: English documentation.
- The mcp004 text said web-search needs a second secret and that the health check was fixed by a loopback admission; the model has since changed to one shared secret.

## Design decisions
- Keep the loopback health note brief and factual; do not claim tool calls depend on it.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`

### Procedure
1. Replace the web-search bullet with: web-search uses the single environment variable for its authentication token, on both the agent side and the server configuration (like git and cicd); no second secret is needed. Cite the server configuration file and the server module as evidence.
2. Replace the troubleshooting entry about the startup health check with an entry for web-search answering 401 on every request: Symptom (the server is up but tool calls and probes are rejected), Cause (the agent and the server resolved different values, for example a stale configuration from before the shared token), Solution (set the one environment variable, deploy the configuration and scripts together, restart the agent). Keep its position before the entry about reload versus restart.

### Method
- Match heading levels, bold labels, and bullet style; wrap identifiers in backticks.

### Details
- Mention that the server's health endpoint is also admitted from a loopback client without a token, as an aside only.

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
- The bullet and the entry describe the shared model and the checkers pass.

## Out of scope
- Other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the web-search bullet and the troubleshooting entry | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: docs/22_mcp/mcp_06_14_mcp-authentication-setup.md (bullet and troubleshooting entry replaced) |
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
- **Related target files**: docs/22_mcp/mcp_06_14_mcp-authentication-setup.md