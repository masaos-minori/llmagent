## Goal
- Replace the Known issue note about the web-search startup health check with a resolution note now that the mismatch is fixed in code (`REQ-001`).

## Scope
- The single blockquote that follows the example environment file in section 2.5.1 of `docs/90_deployment/deployment_01_deployment.md`. The sentence above it, which already states that the browser token is required in addition to the main token, stays.

## Assumptions
- Lightweight fill: documentation only, English.
- Verified at generation time: the note links to the mcp004 issue under its former path in `issues/`, which is now archived, so the link target no longer exists at that path.

## Design decisions
- Replace the note instead of deleting it, so a reader of older instructions finds the outcome, and drop the link to the archived issue.

## Alternatives considered
N/A: single-note replacement.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. Replace the Known issue blockquote with a note stating: web-search's startup health check passes when the browser token differs from the main token, because the server admits its health endpoint without the browser token for a loopback client only; both tokens must still be set; every other endpoint, and any non-loopback request, still requires the browser token. Add the evidence note in the repository's style, citing the middleware in `scripts/mcp_servers/server.py` and its opt-in in `scripts/mcp_servers/web_search/web_search_server.py`.
2. Keep the surrounding paragraph and the reference to the authentication setup guide unchanged.

### Method
- Keep the blockquote form and the section's existing wording style; wrap identifiers in backticks.

### Details
- Do not claim that tool calls work with distinct tokens; that is a separate open issue.

## Compatibility considerations
- Documentation only; no behavior change.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- The documentation checkers named in `routing.md` Tools "When to run which tool" for an edited docs file (quality, structure, English-only), including link validation.
- Execution order for the whole plan: procedures 03 and 04 (tests) first, then 01 and 02 (code), then 05 and 06 (documentation); the new tests must be seen failing before the code is edited.

## Completion criteria
- The Known issue note is replaced and the checkers report no issues.

## Out of scope
- The authentication setup guide (procedure 05) and any code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the Known issue note with the resolution note | Completed | 20261012-182000 | 20261012-182000 | stale_detector clean; changed: docs/90_deployment/deployment_01_deployment.md (Known issue note replaced by a Resolved note) |
| 2 | Run the documentation checkers | Completed | 20261012-182000 | 20261012-182000 | same documentation checkers plus check_docs_consistency --domain deployment pass |

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
- **Related target files**: docs/90_deployment/deployment_01_deployment.md