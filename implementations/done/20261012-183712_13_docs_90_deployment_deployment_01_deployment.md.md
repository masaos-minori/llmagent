## Goal
- Remove the second web-search secret from the deployment instructions (`REQ-005`)

## Scope
- Section 2.5 and 2.5.1 of `docs/90_deployment/deployment_01_deployment.md`: the sentence about the distinct credential, the example environment file entry, the sentence requiring it, and the Resolved note.

## Assumptions
- Lightweight fill: English documentation.
- The pre-flight lists required variables from the configuration references, so no script change is needed.

## Design decisions
- State the new model once and delete what depended on the old one.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. In section 2.5, remove the clause saying the web-search server's browser token is a distinct credential, and say web-search shares its variable with the agent like git and cicd.
2. In the example environment file, remove the line for the browser variable.
3. Remove the paragraph stating that the browser variable is required in addition to the main variable.
4. Replace the Resolved blockquote with a short note: web-search authenticates with the shared token and its health endpoint is admitted from a loopback client; the former separate browser token was retired, and an environment file that still defines it can drop it. Cite the server configuration and the server module.

### Method
- Keep the blockquote form; wrap identifiers in backticks.

### Details
- Do not remove the other servers' variables.

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
- No instruction requires a second web-search secret and the checkers pass.

## Out of scope
- The authentication setup guide.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the second secret from the deployment instructions | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: docs/90_deployment/deployment_01_deployment.md (section 2.5 clause, env example line, required-in-addition paragraph, note) |
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
- **Related target files**: docs/90_deployment/deployment_01_deployment.md