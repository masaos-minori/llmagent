## Goal
Migrate `auth_token` from an empty literal to an environment-variable
reference, matching `config/agent.toml`'s `[mcp_servers.git]` entry.

## Scope
- **In-Scope**: `auth_token = ""` (verified 2026-09-04, line 16) and its
  preceding comment (line 15).
- **Out-of-Scope**: `allowed_repo_paths`, `read_only`, `max_log_entries`,
  and the removed-key note about `audit_log_path` — confirmed by direct
  read to be unrelated to authentication.

## Assumptions
- This file's `auth_token` must resolve to the *same* secret value as
  `config/agent.toml`'s `[mcp_servers.git].auth_token` (row 7) — this file
  is the git MCP server's own standalone config (loaded via
  `ConfigLoader.restrict_to(self.own_config_file)` per
  `scripts/mcp_servers/server.py`'s `run_http()`), used server-side to
  validate incoming Bearer tokens, while `agent.toml`'s entry is the Agent's
  client-side credential for calling this server — both must reference the
  identical environment variable (`MCP_GIT_AUTH_TOKEN`).
- `git_models.py:44`'s `get_str(d, "auth_token")` call (confirmed by direct
  read) transparently resolves `${ENV:...}` once row 2's `get_str()` change
  lands — no code change needed in `git_models.py` itself.

## Design decisions
- Use `${ENV:MCP_GIT_AUTH_TOKEN}`, matching row 7's naming for
  `[mcp_servers.git]`.

## Alternatives considered
- A distinct environment variable name from `agent.toml`'s
  `[mcp_servers.git]` entry: rejected — per Assumptions, both sides must
  resolve to the identical secret value for the Bearer-token check to
  succeed; using two different variable names would require an operator to
  manually keep two separately-named secrets in sync, inviting drift.

## Implementation
### Target file
`config/git_mcp_server.toml`

### Procedure
Replace `auth_token = ""` (line 16) with
`auth_token = "${ENV:MCP_GIT_AUTH_TOKEN}"`.

### Method
Direct `Edit`.

### Details
Current (verified 2026-09-04, lines 15-16):
```toml
# auth_token: Bearer token; empty string = auth disabled.
auth_token = ""
```
After:
```toml
# auth_token: Bearer token, resolved from the MCP_GIT_AUTH_TOKEN
# environment variable. Must match config/agent.toml's
# [mcp_servers.git].auth_token value.
auth_token = "${ENV:MCP_GIT_AUTH_TOKEN}"
```

## Compatibility considerations
This is the live deployed configuration for the git MCP server subprocess —
a deploy step (Plan Implementation steps Phase 3) is mandatory after this
edit, sequenced together with row 7's `agent.toml` change (both must use
the same `MCP_GIT_AUTH_TOKEN` value).

## Security considerations
This row's edit is part of REQ-002/AC-5's environment-variable-based secret
loading for the git MCP server.

## Rollback considerations
Single-line config edit under version control; revert via `git revert` if
needed, together with row 7.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `config/git_mcp_server.toml` | Deployment | `skills/deploy/workflow.md`'s deploy sequence, with `MCP_GIT_AUTH_TOKEN` set beforehand | Git MCP server starts and validates incoming Bearer tokens against the resolved value |

## Completion criteria
`auth_token` references `${ENV:MCP_GIT_AUTH_TOKEN}`; no literal empty-string
value remains.

## Out of scope
`allowed_repo_paths`, `read_only`, `max_log_entries`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Must use the same `MCP_GIT_AUTH_TOKEN` value as row 7's `agent.toml` entry |
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
- **Related target files**: config/git_mcp_server.toml
