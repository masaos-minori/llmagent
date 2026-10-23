## Goal
Replace the statements that treat the accept-all empty-token path as rejected only by Agent validation (`REQ-004`).

## Scope
- Edit line 44 (the `Authorization: Bearer` note) and line 129 (the `attach_auth_middleware` bullet) so both say every MCP server refuses to start without a non-empty token.

## Assumptions
- The document has high churn (16 commits in 30 days); keep the edit to those two statements and rebase before committing.

## Design decisions
- State the rule once as a startup failure for every server; keep the testability note for `attach_auth_middleware`.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_02_01_endpoints-and-transport.md`

### Procedure
1. Rewrite line 129: with an empty token the middleware itself would accept all requests, which only exists for standalone testing; every server refuses to start with an empty token, and Agent startup validation also rejects it.
2. Adjust line 44 so "production: auth_token is mandatory" agrees with the new wording.

### Method
- Edit existing sentences; no new section, table or code block.

### Details
- English only; do not duplicate per-server variable names.

## Compatibility considerations
- N/A: documentation-only.

## Security considerations
- N/A: describes an enforced control.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_docs_japanese.py`.

## Completion criteria
- No sentence says an empty token is accepted by a supported server; checkers pass.

## Out of Scope
- Other MCP security documents
- ADR changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the documentation edit per Implementation > Procedure | Completed | 20261023-130215 | 20261023-130215 | implemented; tests/mcp_servers 2468 passed; one additional test file discovered and added to the Plan (row 25); full suite run at the end of the batch |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261023-130215 | 20261023-130215 |  |

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
- **Requirement ID**: `REQ-004` (document that every server refuses an empty token)
- **Source issue**: issues/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115211_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123707
- **Related target files**: docs/22_mcp/mcp_02_01_endpoints-and-transport.md