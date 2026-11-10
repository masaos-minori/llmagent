## Goal

Reword the `MdqMCPServer` docstring that cites the deleted `list_tools_with_server_key()` (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

Docstring edit in `scripts/mcp_servers/mdq/mdq_server.py` only.

## Assumptions

- Phase 2 of the Plan; independent of the `server.py` edit, but meaningful only once the helper is gone.

## Design decisions

- Replace `(used by list_tools_with_server_key() and routing)` with a statement that `server_key` is used for routing; no code change.

## Alternatives considered

N/A: one-line docstring change.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure
1. In the `MdqMCPServer` class docstring (line 461) change the `server_key` bullet to `used for routing`.

### Method
- Confirm with `rg -n "list_tools_with_server_key" scripts` that no mention remains after this and the `server.py` row.

### Details
- Keep the other docstring bullets as is.

## Compatibility considerations

N/A: docstring only.

## Security considerations

N/A: docstring only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run ruff format scripts/mcp_servers/mdq/mdq_server.py` and `uv run ruff check` on it; `uv run pytest tests/mcp_servers/mdq/test_mdq_routing.py -v`.

## Completion criteria

- No mention of `list_tools_with_server_key` in the file.

## Out of Scope

- Behavior of `MdqMCPServer` and `test_mdq_routing.py` (own row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the docstring | Done | 20261110-172551 | 20261110-172551 | REQ-006 |
| 2 | Run ruff and the mdq routing tests | In Progress | 20261110-172551 | — | ruff clean; rg confirms no `list_tools_with_server_key` mention in scripts/. test_mdq_routing.py has 3 red conformance tests until row 35 lands (allowed red, batch end gate) |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/mcp_servers/mdq/mdq_server.py`
