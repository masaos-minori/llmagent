## Goal

Document the `control_auth_token` field and the `MCP_*_CONTROL_TOKEN` inherited-environment pattern on the McpServerConfig fields page.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the field list or table for `McpServerConfig` fields and the inherited-variable bullets in the `env` note. No other text changes.

## Assumptions

- Verified: the page lists the inherited variables including `MCP_*_AUTH_TOKEN` and explains why the token pattern must stay inherited.

## Design decisions

- Describe `control_auth_token` as optional, defaulting to empty, resolved from `${ENV:...}` without failing when unset.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`

### Procedure
1. Add `MCP_*_CONTROL_TOKEN` to the inherited variable list (matching row 34).
2. Add one bullet: the control token is resolved inside the child and an unset variable only closes the control paths.
3. Add `control_auth_token` to the field listing with its meaning.

### Method
Prose and list edits only.

### Details
- Keep the existing statement about `auth_token` and add the control token alongside it.

## Compatibility considerations

N/A: no behavior change in this row.

## Security considerations

N/A: documentation only; no secret value, approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The page names the field and the inherited pattern consistently with the code; the gates pass.

## Out of Scope

The per-key reference in the agent config document (row 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-154345 | 20261123-154345 | inherited-variable list now names MCP_*_CONTROL_TOKEN; a bullet states the pattern is resolved inside the child from each server [control] table and that an unset control token closes only that server control paths; control_auth_token added to the fields-with-design-meaning list as optional, default empty, tolerant resolution, registered as a secret and never logged |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-154345 | 20261123-154345 | check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_consistency --domain mcp pass |

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
- **Requirement ID**: `REQ-002` (separate control Bearer authorization), `REQ-007` (documentation of the control contract)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`
