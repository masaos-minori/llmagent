## Goal

Add the `mcp_servers.*.control_auth_token` row to the per-key reference this document owns.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: one table row in `### MCP server definitions`, placed after `mcp_servers.*.auth_token`; the reload-class note near the top that mentions `auth_token` restarts.

## Assumptions

- Verified: the per-key table lists `mcp_servers.*.auth_token | McpServerConfig | string | n/a | '' | [RESTART]`, and the document states that changes to `auth_token` require a restart.

## Design decisions

- Row: `mcp_servers.*.control_auth_token | McpServerConfig | string | n/a | '' | [RESTART]`; mention it in the restart sentence.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/23_agent/agent_08_01_configuration-loading-agent-config.md`

### Procedure
1. Insert the row and update the restart sentence.

### Method
Two prose edits.

### Details
- The per-key reference restates neither code defaults nor deployed values beyond the existing table convention; follow the neighbouring row exactly.

## Compatibility considerations

N/A: no behavior change in this row.

## Security considerations

N/A: documentation only; no secret value, approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/run_validation_gates.py`
- `uv run pytest tests/tools/test_generate_reference_table.py`

## Completion criteria

- The row exists with the same columns as its neighbour; the gates pass.

## Out of Scope

Other config keys.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-155132 | 20261123-155132 | row added after mcp_servers.*.auth_token and the restart sentence names it. Verified against code: control_auth_token is a McpServerConfig field, and classify_mcp_server_changes treats every field difference as restart-required, so [RESTART] is correct; the section row count marker went 76 to 77 |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-155132 | 20261123-155132 | check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_consistency --domain agent pass; the single warning is a pre-existing line in the generated agent_14 document |

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
- **Related target files**: `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`
