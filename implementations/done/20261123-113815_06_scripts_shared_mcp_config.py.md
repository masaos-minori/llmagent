## Goal

Give the Agent a per-server control credential: add `control_auth_token` (new) to `McpServerConfig` and resolve it tolerantly when the config is built.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the dataclass field and `_build_single_server`. `auth_token` handling and validation are unchanged.

## Assumptions

- Verified: `_build_single_server` resolves `auth_token` with `resolve_env_ref` (strict: unset raises) and registers it with `register_secret`.
- The control token is optional by design, so an unset `${ENV:...}` must not stop the Agent; `resolve_control_token` maps it to an empty string (control closed).

## Design decisions

- Field: `control_auth_token: str = ""` placed after `auth_token`; build with `resolve_control_token(v.get("control_auth_token", ""))` and `register_secret` when non-empty.
- Match the existing `auth_token` treatment of repr/logging; if `auth_token` is excluded from repr, exclude this field the same way.

## Alternatives considered

Rejected: reusing `resolve_env_ref` for the control token (an unset variable would stop every Agent start until all ten variables are exported).

## Implementation
### Target file
`scripts/shared/mcp_config.py`

### Procedure
1. Import `resolve_control_token` from the contract module.
2. Add the field and the resolved value in the `McpServerConfig(...)` construction.
3. Register the resolved token as a secret for log redaction.

### Method
Two small edits in `scripts/shared/mcp_config.py`; no change to validation functions.

### Details
- Existing tests for `McpServerConfig` construction rely on defaults, so no other call site changes.

## Compatibility considerations

Additive field with a default; configs without the key behave as before.

## Security considerations

The token is registered with `register_secret` so it is redacted from logs; an empty token keeps control closed.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_config.py tests/agent/test_config_builders.py`
- Row 30 covers the field through the recovery service tests

## Completion criteria

- `McpServerConfig.control_auth_token` exists, resolves `${ENV:...}` tolerantly, defaults to empty, and is registered as a secret.

## Out of Scope

Server-side `[control]` loading (row 10) and `config/agent.toml` entries (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-140902 | 20261123-140902 | field added after auth_token; resolved with resolve_control_token and registered when non-empty |
| 2 | Add or update tests per Validation plan | Completed | 20261123-140902 | 20261123-140902 | test added for tolerant resolution (the procedure expected no test change); 96 tests green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-140902 | 20261123-140902 | ruff, mypy, lint-imports, bandit pass |

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
- **Related target files**: `scripts/shared/mcp_config.py`
