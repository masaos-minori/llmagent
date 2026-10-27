# mcpcompat001-import-mcpserverhealthregistry-from-mcp-health-in-agent-mcp-integration-tests

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Move the `McpServerHealthRegistry` import in the agent-MCP integration test module to
the canonical `shared.mcp_health` module (REQ-001; AC-1).

## Scope

- `tests/integration/test_agent_mcp_integration.py`: the single-line `shared.mcp_config`
  import at current L18 (`McpServerConfig`, `McpServerHealthRegistry`, `TransportType`).
- Import block only; no test body change.

## Assumptions

- Verified against the current source: L18 reads
  `from shared.mcp_config import McpServerConfig, McpServerHealthRegistry, TransportType`;
  the file has no `shared.mcp_health` import.

## Design decisions

- Split the import: `McpServerConfig` and `TransportType` stay on `shared.mcp_config`;
  the Registry moves to a new `shared.mcp_health` line.

## Alternatives considered

- None significant for an import move.

## Implementation

### Target file

`tests/integration/test_agent_mcp_integration.py`

### Procedure

1. Replace current L18:
   > from shared.mcp_config import McpServerConfig, McpServerHealthRegistry, TransportType

   with:
   > from shared.mcp_config import McpServerConfig, TransportType
   > from shared.mcp_health import McpServerHealthRegistry

### Method

One-line replacement plus one added line; isort order preserved.

### Details

- Names and test bodies unchanged.

## Compatibility considerations

- Must land before procedure 01 (the re-export deletion).

## Security considerations

- None.

## Rollback considerations

- Revert the two import lines.

## Validation plan

- `uv run pytest tests/integration/test_agent_mcp_integration.py -v`.
- `uv run ruff check tests/integration/test_agent_mcp_integration.py`.

## Completion criteria

- `McpServerHealthRegistry` imported from `shared.mcp_health` (AC-1).

## Out of Scope

- The re-export deletion — procedure 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Before procedure 01 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | Import-only change; no new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | pytest, ruff |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | N/A for this row |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261027-104222_mcpcompat001_remove-mcp-compat-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-013216
- **Related target files**: tests/integration/test_agent_mcp_integration.py
