## Goal
State in the shell-mcp section which variables a command receives and that secret-shaped variables are never forwarded (`REQ-004`).

## Scope
- Extend the security-relevant settings bullet that says `env_allowlist` / `env_denylist` filter `req.env` only (line 67).

## Assumptions
- The document has high churn (21 commits in 30 days); keep the edit to one or two sentences and rebase before committing.

## Design decisions
- Describe the contract (boundaries, failure behavior) without listing every key, per `skills/DESIGN.md` Avoid implementation-reference duplication.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`

### Procedure
1. Add a sentence to the `env_allowlist` / `env_denylist` bullet: a command receives only a small fixed base environment plus the filtered `req.env`; credential-shaped variables (`MCP_*`, token, secret, password variables) are never forwarded and are removed even when listed in `req.env`.

### Method
- Edit the existing bullet; no new section, no table, no code block.

### Details
- English only (`skills/DESIGN.md` Output language); do not hardcode doc filenames elsewhere.

## Compatibility considerations
- N/A: documentation-only.

## Security considerations
- N/A: describes an existing control; contains no secret values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_docs_japanese.py`.

## Completion criteria
- The document states the environment contract and the docs checkers pass.

## Out of Scope
- Any other shell documentation or ADR change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the documentation edit per Implementation > Procedure | Completed | 20261023-125405 | 20261023-125405 | implemented and validated per plan batch (targeted shell tests, full suite 9713 passed) |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261023-125405 | 20261023-125405 |  |

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
- **Requirement ID**: `REQ-004` (document the environment contract)
- **Source issue**: issues/20261023-114000_mcpstart001_shell-sandbox-commands-inherit-all-mcp-auth-tokens-and-github_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-122828
- **Related target files**: docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md