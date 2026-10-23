## Goal
Update the module docstring so it covers all ten servers' tokens (`REQ-005`).

## Scope
- Docstring only (lines 1-12); the constants stay.

## Assumptions
- The docstring currently names five variables and the shell, github and file servers only.

## Design decisions
- Describe the rule generally (the value `tests/conftest.py` assigns to every `MCP_*_AUTH_TOKEN`).

## Alternatives considered
- N/A: docstring-only change.

## Implementation
### Target file
`tests/mcp_servers/_auth_headers.py`

### Procedure
1. Reword the docstring to say the header is valid for every Bearer-authenticated MCP server application and that `tests/conftest.py` assigns the same value to all of the MCP token variables.

### Method
- Keep `MCP_TEST_TOKEN` and `MCP_TEST_AUTH_HEADERS` unchanged.

### Details
- Keep the first-line module docstring format unchanged.

## Compatibility considerations
- N/A: docstring-only.

## Security considerations
- N/A: dummy token only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run ruff check tests/mcp_servers`, `uv run mypy`, `uv run pytest tests/mcp_servers -q`.

## Completion criteria
- Docstring is accurate; constants unchanged.

## Out of Scope
- Changing the token value

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the docstring edit per Implementation > Procedure | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (shared header documentation)
- **Source issue**: issues/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115211_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123707
- **Related target files**: tests/mcp_servers/_auth_headers.py
