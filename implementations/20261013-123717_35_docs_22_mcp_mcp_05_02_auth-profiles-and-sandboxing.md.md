## Goal
- State in the access-control chapter that each server except mdq-mcp verifies the token from its own server-side `auth_token`, and that the shell, github, and file servers refuse to start without a non-empty value (REQ-007).

## Scope
- In: the `Applies to:` paragraph of the Authentication section (line 39).
- Out: the Agent-side description and everything else.

## Assumptions
- Apply after Steps 3-7. The Authentication section (lines 24-51) currently describes only the Agent-side check.

## Design decisions
- Extend the existing sentence rather than adding a section; no configuration values (documentation policy).

## Alternatives considered
N/A: a one-sentence addition.

## Implementation
### Target file
`docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`

### Procedure
1. Append the new sentences to the `Applies to:` paragraph.

### Method
- Keep the existing mdq-mcp sentence intact; add the new text before the final sentence about the agent-side entry or after it, as the paragraph reads best.

### Details
Line 39 (Before/After):

```markdown
# Before:
Applies to: All servers except mdq-mcp (configured per server via `McpServerConfig.auth_token`). mdq-mcp attaches the auth middleware with an empty token, so it does not verify Bearer tokens at the HTTP layer (see `mcp_05_05_mdq-enforcement-and-lockdown.md`); the agent-side `auth_token` entry is still required to be non-empty.
# After:
Applies to: All servers except mdq-mcp (configured per server via `McpServerConfig.auth_token`). mdq-mcp attaches the auth middleware with an empty token, so it does not verify Bearer tokens at the HTTP layer (see `mcp_05_05_mdq-enforcement-and-lockdown.md`); the agent-side `auth_token` entry is still required to be non-empty. Each of these servers verifies the token from its own server-side `auth_token`, resolved from the same environment variable the agent configuration uses; the shell, github, and file servers additionally refuse to start when that value is empty, so an empty or missing token cannot leave them unauthenticated.
```

## Compatibility considerations
- Documentation only.

## Security considerations
N/A: documentation of the control.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`.

## Completion criteria
- The paragraph states the server-side token, its source variable, and the refusal; the checkers pass.

## Out of scope
- The mdq-mcp description and the Agent-side validation text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the `Applies to:` paragraph | Pending | — | — | Plan Step 8; after Steps 3-7 |
| 2 | Run the documentation checkers | Pending | — | — |  |

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
- **Requirement ID**: `REQ-007` (the per-server authentication description states the server-side token and the startup refusal)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md
