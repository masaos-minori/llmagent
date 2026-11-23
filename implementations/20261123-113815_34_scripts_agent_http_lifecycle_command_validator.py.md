## Goal

Let a subprocess MCP server inherit its own control token by adding the `MCP_*_CONTROL_TOKEN` pattern to the default child-environment allowlist.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `_DEFAULT_ALLOWED_ENV_VARS` and the comment above it. The denylist and protected-variable sets are unchanged.

## Assumptions

- Verified: the allowlist is default-deny and contains `MCP_*_AUTH_TOKEN`; each server resolves its `${ENV:...}` references from the inherited environment, so a control token variable would be dropped without this pattern.
- Verified: the env-allowlist integration test checks that variables referenced by shipped configs reach their child.

## Design decisions

- Add the single pattern `MCP_*_CONTROL_TOKEN` (fnmatch form, like the existing pattern).

## Alternatives considered

Rejected: passing the variables through each server's `env` table (ten duplicated entries and tokens in config).

## Implementation
### Target file
`scripts/agent/http_lifecycle_command_validator.py`

### Procedure
1. Add the pattern to the frozenset and extend the comment to name the control token.
2. Update the documented inherited list in row 36 accordingly.

### Method
One-line set edit plus comment.

### Details
- The pattern does not match `MCP_*_AUTH_TOKEN` or unrelated variables.

## Compatibility considerations

Subprocess servers receive one more family of variables; none are secrets beyond their own token.

## Security considerations

Narrow pattern; a server receives all `MCP_*_CONTROL_TOKEN` variables of the Agent environment, the same exposure shape as `MCP_*_AUTH_TOKEN` today; tokens are never logged.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py tests/agent/test_http_lifecycle_env_allowlist_integration.py`

## Completion criteria

- `filter_env` keeps `MCP_<NAME>_CONTROL_TOKEN` and still drops unrelated variables.

## Out of Scope

Documentation of the list (row 36) and tests (row 35).

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
- **Related target files**: `scripts/agent/http_lifecycle_command_validator.py`
