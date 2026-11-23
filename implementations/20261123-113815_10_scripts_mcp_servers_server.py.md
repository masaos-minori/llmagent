## Goal

Wire the control API into every MCP server from the one shared module: load the server's own `[control]` table in `run_http` and attach the control middleware from `attach_auth_middleware`.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: two small additions in `scripts/mcp_servers/server.py` (about 19 KB of the 24.6 KB gate). Tool-path authentication is unchanged.

## Assumptions

- Verified: `run_http` loads own config with `ConfigLoader` after `restrict_to`, validates `[dedup]` with `load_dedup_section`, and runs before uvicorn imports the app; all ten server modules call `attach_auth_middleware` at import time and `test_require_auth_token.py` already checks that route.
- The `[dedup]` validated config is kept in a local variable so `configure_control` can open its own store handle.

## Design decisions

- In `run_http`, after `configure_dedup(...)`: read `own_data.get('control')` (table or absent), call `resolve_control_token(table.get('auth_token'))`, then `configure_control(token, dedup_cfg, self.server_name)`. A missing own config leaves the token empty and logs the existing warning path.
- At the end of `attach_auth_middleware`, call `attach_control_api(app)` (imported inside the function to avoid an import cycle).

## Alternatives considered

Rejected: attaching in `run_http` by importing `app_module` (breaks the base-class tests' non-importable app strings and double-imports server modules).

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Keep the validated dedup config in a local and call `configure_control` after dedup bootstrap.
2. Add the `attach_control_api(app)` call after the auth middleware registration.
3. Add a startup warning (server name only) when the resolved control token is empty.

### Method
Edit `run_http` and `attach_auth_middleware`; do not change any middleware order inside `attach_auth_middleware` (auth stays registered last before the control middleware, which becomes outermost).

### Details
- Typed config errors from `[dedup]` still propagate before control configuration runs.

## Compatibility considerations

Servers without a `[control]` table start normally with control paths closed.

## Security considerations

An empty or unset control token closes only the control paths; the tool Bearer middleware and its INV-03 fail-closed behavior are untouched.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_mcp_server_base.py tests/mcp_servers/test_call_state_api.py tests/mcp_servers/test_require_auth_token.py tests/mcp_servers/test_config_isolation_import.py`

## Completion criteria

- All ten servers attach the control middleware, `run_http` configures it from `[control]`, and the existing server-base and auth tests pass.

## Out of Scope

Handler logic (row 09) and the per-server TOML rows (15-24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `scripts/mcp_servers/server.py`
