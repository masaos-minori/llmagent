## Goal

Pin that `filter_env` passes `MCP_<NAME>_CONTROL_TOKEN` to a child and still drops unrelated variables.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: one new test beside the existing `MCP_SHELL_AUTH_TOKEN` pass-through test.

## Assumptions

- Verified: an existing test builds an environment with `PATH`, `HOME`, and `MCP_SHELL_AUTH_TOKEN` and asserts the token is kept.

## Design decisions

- Parametrize over `MCP_SHELL_CONTROL_TOKEN` and `MCP_MDQ_CONTROL_TOKEN`; include a non-allowlisted variable and assert it is absent.

## Alternatives considered

N/A: minimal test.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_command_validator.py`

### Procedure
1. Add the test next to the auth-token pass-through test, reusing its validator construction.

### Method
Use the same helper and dummy values as the neighbouring test.

### Details
- Assert the control and auth tokens are both kept and an unrelated `SOME_OTHER_TOKEN` is dropped.

## Compatibility considerations

N/A: tests only.

## Security considerations

N/A: dummy values only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py`

## Completion criteria

- The test passes with row 34 and fails without it.

## Out of Scope

Production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-145732 | 20261123-145732 | test added next to the auth-token pass-through test, parametrized over MCP_SHELL_CONTROL_TOKEN and MCP_MDQ_CONTROL_TOKEN, asserting both token families are kept and SOME_OTHER_TOKEN is dropped |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-145732 | 20261123-145732 | ruff format/check pass; 111 unit tests plus the 8 integration-gate tests green |

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
- **Related target files**: `tests/agent/test_http_lifecycle_command_validator.py`
