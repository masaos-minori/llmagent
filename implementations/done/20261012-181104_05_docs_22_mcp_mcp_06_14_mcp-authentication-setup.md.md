## Goal
- Record in the MCP authentication setup guide that web-search needs a second credential and that its health check is admitted over loopback (`REQ-001`).

## Scope
- `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`: one bullet under Setup Requirements and one entry under Troubleshooting. Nothing else changes.

## Assumptions
- Lightweight fill: documentation only, written in English per the documentation language rule.
- Verified at generation time: this guide does not mention the browser token today, while the deployment document already records the requirement.
- Documentation sentences about behavior carry an evidence note in the repository's style.

## Design decisions
- Keep the addition short and link to the deployment document's token section instead of repeating it.

## Alternatives considered
N/A: two small insertions.

## Implementation
### Target file
`docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`

### Procedure
1. In Setup Requirements, after the bullet about non-empty secrets for all HTTP MCP servers, add a bullet: web-search additionally requires the environment variable for its browser token, which is a distinct credential from its main authentication token (both must be set); the web-search server validates its endpoints against the browser token, and its health endpoint is admitted without that token only for a loopback client so that the agent's startup health check, which presents the main token, succeeds. Cite the config file and the server module as evidence.
2. In Troubleshooting, add an entry titled for the web-search startup health check failing with 401 when the two tokens differ: Symptom (the agent aborts while waiting for web-search to become ready), Cause (before the loopback admission the health endpoint was validated against the browser token while the poll sends the main token), Solution (use a build that includes the loopback admission and set both tokens; a request from a non-loopback address is still rejected). Place it before the entry about the difference between reload and a full restart.

### Method
- Match the existing heading levels, bold labels, and bullet style; wrap every identifier in backticks.

### Details
- Do not restate the full token table from the deployment document.

## Compatibility considerations
- Documentation only; no behavior change.

## Security considerations
N/A: documentation only; no token values are written.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- The documentation checkers named in `routing.md` Tools "When to run which tool" for an edited docs file (quality, structure, and the English-only check).
- Execution order for the whole plan: procedures 03 and 04 (tests) first, then 01 and 02 (code), then 05 and 06 (documentation); the new tests must be seen failing before the code is edited.

## Completion criteria
- The bullet and the troubleshooting entry exist and the documentation checkers report no issues.

## Out of scope
- The deployment document (procedure 06) and any code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the web-search credential bullet and the troubleshooting entry | Completed | 20261012-182000 | 20261012-182000 | stale_detector clean; changed: docs/22_mcp/mcp_06_14_mcp-authentication-setup.md (Setup Requirements bullet, Troubleshooting entry) |
| 2 | Run the documentation checkers | Completed | 20261012-182000 | 20261012-182000 | check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_consistency --domain mcp, check_docs_japanese pass |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/done/20261012-173750_mcp004_web_search-mcp-server-startup-health-check-fails-due-to-browser_auth_token-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-175600_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-181104
- **Related target files**: docs/22_mcp/mcp_06_14_mcp-authentication-setup.md