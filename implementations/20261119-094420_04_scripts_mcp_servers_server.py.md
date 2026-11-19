## Goal
- Keep the MCP middleware docstring accurate after the EventBus rename (REQ-003: update every cross-reference).

## Scope
**Release unit**: eventbus-api-surface

- In scope: one sentence of the `attach_auth_middleware` docstring in `scripts/mcp_servers/server.py`. This file is not in the issue's Target Files; it is fallout of the rename and is a row of the Plan's frozen table.
- The MCP function `attach_auth_middleware` itself and every MCP caller stay unchanged.

## Assumptions
- The docstring sentence names `eventbus.auth.attach_auth_middleware` and says it injects only X-Request-Id and performs no authentication (verified in Step 3a).

## Design decisions
- Change only the cited EventBus name; keep the meaning of the contrast sentence.

## Alternatives considered
N/A: a one-sentence docstring fix.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. In the docstring of `attach_auth_middleware`, replace `eventbus.auth.attach_auth_middleware` with `eventbus.auth.attach_request_id_middleware` (new).
2. Re-wrap the sentence so each line stays within 88 characters; the longer name pushes the first line past the limit.

### Method
- Keep the sentence structure: it contrasts the EventBus function (injects only X-Request-Id, no authentication) with this function (authenticates a Bearer token and fails closed on an empty token).

### Details
- Do not touch the function body, its signature, or any other docstring text.

## Compatibility considerations
N/A: docstring only.

## Security considerations
N/A: no behavior change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run ruff format --check scripts/mcp_servers/server.py` and `uv run ruff check scripts/mcp_servers/server.py`.
- `uv run pytest tests/mcp_servers/test_mcp_server_base.py -q`.
- `rg "eventbus.auth.attach_auth_middleware" scripts` finds nothing.

## Completion criteria
- The docstring names the renamed EventBus function and no source file cites the old EventBus name.

## Out of Scope
- Any change to MCP authentication behavior or to other docstrings in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update and re-wrap the docstring sentence | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (rename the request-ID middleware and update cross-references)
- **Source issue**: issues/20261117-123002_adrchk002_eventbus-authz-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-092411_adrchk002_eventbus-authz-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-094420
- **Related target files**: `scripts/mcp_servers/server.py`
