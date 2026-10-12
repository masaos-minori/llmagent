## Goal
- Update the paragraph that lists each server's server-side Bearer-token field (`REQ-005`)

## Scope
- The paragraph after the configuration file table in `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`.

## Assumptions
- Lightweight fill: reword one paragraph in English.
- git-mcp, cicd-mcp, and web-search-mcp now all use auth_token as a shared-secret reference.

## Design decisions
- Keep the paragraph's point (server-side token as an environment reference; the same variable name as the agent's counterpart so both sides agree) and extend it to web-search.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`docs/22_mcp/mcp_06_01_configuration-file-inventory.md`

### Procedure
1. Rewrite the first sentence so it says git-mcp, cicd-mcp, and web-search-mcp each carry a server-side Bearer-token field named auth_token, as an environment reference.
2. Rewrite the last sentence so git-mcp, cicd-mcp, and web-search-mcp share the same variable name as their agent configuration counterpart (the git, cicd, and web-search authentication variables).
3. Remove the mention of the browser tool token.

### Method
- Match the paragraph's wrapping and tone.

### Details
- Do not list token values.

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
- The paragraph states the shared model for all three servers and the checkers pass.

## Out of scope
- Other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the Bearer-token field paragraph | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: docs/22_mcp/mcp_06_01_configuration-file-inventory.md (paragraph extended to all three servers) |
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
- **Related target files**: docs/22_mcp/mcp_06_01_configuration-file-inventory.md