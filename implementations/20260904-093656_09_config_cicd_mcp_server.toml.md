## Goal
Migrate `auth_token` from an empty literal to an environment-variable
reference, matching `config/agent.toml`'s `[mcp_servers.cicd]` entry.

## Scope
- **In-Scope**: `auth_token = ""` (verified 2026-09-04, line 23) and its
  preceding comment (lines 21-22).
- **Out-of-Scope**: `repo_allowlist`, `workflow_allowlist`,
  `max_log_size_kb`, and `github_token` (a separate, unrelated credential
  with its own existing `GITHUB_TOKEN` environment-variable fallback
  convention, confirmed by direct read to already exist independent of this
  Plan) — confirmed to be unrelated to `auth_token`.

## Assumptions
- This file's `auth_token` must resolve to the *same* secret value as
  `config/agent.toml`'s `[mcp_servers.cicd].auth_token` (row 7) — same
  client/server credential-matching reasoning as row 8
  (`config/git_mcp_server.toml`).
- `cicd_models.py:39`'s `auth_token=get_str(d, "auth_token")` call
  (confirmed by direct read) transparently resolves `${ENV:...}` once row
  2's `get_str()` change lands — no code change needed in `cicd_models.py`
  itself.
- This file already documents a precedent for an environment-variable
  fallback convention (`github_token`'s comment: "fallback when
  GITHUB_TOKEN env var is unset") — this row's `${ENV:MCP_CICD_AUTH_TOKEN}`
  syntax is a distinct, explicit-reference mechanism (row 2), not the same
  implicit-fallback mechanism `github_token` uses; do not conflate the two
  or attempt to unify them, since `github_token`'s own convention is out of
  this Plan's scope.

## Design decisions
- Use `${ENV:MCP_CICD_AUTH_TOKEN}`, matching row 7's naming for
  `[mcp_servers.cicd]`.

## Alternatives considered
- Reusing `github_token`'s existing implicit `GITHUB_TOKEN`-fallback
  pattern for `auth_token` too: rejected — `github_token` and `auth_token`
  are different credentials for different purposes (GitHub API access vs.
  this MCP server's own Bearer-token authentication); reusing one
  credential's fallback mechanism for an unrelated field would be
  confusing and is not required by REQ-002.

## Implementation
### Target file
`config/cicd_mcp_server.toml`

### Procedure
Replace `auth_token = ""` (line 23) with
`auth_token = "${ENV:MCP_CICD_AUTH_TOKEN}"`.

### Method
Direct `Edit`.

### Details
Current (verified 2026-09-04, lines 21-23):
```toml
# auth_token: Bearer token for MCP server call authentication
# Empty string = auth disabled (loopback-only default)
auth_token = ""
```
After:
```toml
# auth_token: Bearer token for MCP server call authentication, resolved
# from the MCP_CICD_AUTH_TOKEN environment variable. Must match
# config/agent.toml's [mcp_servers.cicd].auth_token value.
auth_token = "${ENV:MCP_CICD_AUTH_TOKEN}"
```

## Compatibility considerations
This is the live deployed configuration for the cicd MCP server subprocess —
a deploy step (Plan Implementation steps Phase 3) is mandatory after this
edit, sequenced together with row 7's `agent.toml` change (both must use
the same `MCP_CICD_AUTH_TOKEN` value).

## Security considerations
This row's edit is part of REQ-002/AC-5's environment-variable-based secret
loading for the cicd MCP server.

## Rollback considerations
Single-line config edit under version control; revert via `git revert` if
needed, together with row 7.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `config/cicd_mcp_server.toml` | Deployment | `skills/deploy/workflow.md`'s deploy sequence, with `MCP_CICD_AUTH_TOKEN` set beforehand | CICD MCP server starts and validates incoming Bearer tokens against the resolved value |

## Completion criteria
`auth_token` references `${ENV:MCP_CICD_AUTH_TOKEN}`; no literal
empty-string value remains.

## Out of scope
`repo_allowlist`, `workflow_allowlist`, `max_log_size_kb`, `github_token`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Must use the same `MCP_CICD_AUTH_TOKEN` value as row 7's `agent.toml` entry; do not touch unrelated `github_token` |
| 2 | Add or update tests per Validation plan | N/A | — | — | Configuration file, no dedicated test — validated via deploy step |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Includes the mandatory deploy step |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Plan's Documentation Impact: Yes — deployment secret instructions, sequenced after this Plan lands |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: config/cicd_mcp_server.toml
