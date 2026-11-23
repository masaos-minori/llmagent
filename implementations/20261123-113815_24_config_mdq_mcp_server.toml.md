## Goal

Give the mdq MCP server its own control credential: add a `[control]` table with `auth_token = "${ENV:MCP_MDQ_CONTROL_TOKEN}"`.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: one new table after `[dedup]`. No existing key changes.

## Assumptions

- Verified: the file carries the `[dedup]` table the `[control]` table mirrors, and `run_http` loads the server's own table after config isolation.
- An unset variable resolves to an empty token (control closed, startup warning), so the server still starts.

## Design decisions

- Table name `[control]`, single key `auth_token`; the value is an env reference only.

## Alternatives considered

N/A: the shape is fixed by the Plan.

## Implementation
### Target file
`config/mdq_mcp_server.toml`

### Procedure
1. Append the `[control]` table after the `[dedup]` table with a comment of at most three lines stating it is the Agent-only control token distinct from the tool `auth_token`.

### Method
One Edit at the end of the file.

### Details
- Variable name is MCP_MDQ_CONTROL_TOKEN, matching the Agent entry in row 14.

## Compatibility considerations

Additive table; servers ignoring unknown tables are unaffected.

## Security considerations

Env reference only; no secret value is stored in the repository.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_call_state_api.py` (config fixture)
- `uv run python tools/check_config_comment_length.py`

## Completion criteria

- The file has a valid `[control]` table and the server config still loads.

## Out of Scope

Server code and the Agent entry (rows 09, 10, 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-145718 | 20261123-145718 | [control] table appended after [dedup] with auth_token = "${ENV:MCP_MDQ_CONTROL_TOKEN}" and a three-line comment (separate credential, empty token closes only control paths) |
| 2 | Run the config loading test and the comment-length checker named in Validation plan | Completed | 20261123-145718 | 20261123-145718 | the file parses as TOML, tests/mcp_servers/ (2807 passed incl. the config fixture and per-server config tests) and check_config_comment_length.py (0 errors) are green |

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
- **Requirement ID**: `REQ-002` (separate control Bearer authorization)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `config/mdq_mcp_server.toml`
