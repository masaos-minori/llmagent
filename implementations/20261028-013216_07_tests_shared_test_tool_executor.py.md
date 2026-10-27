# mcpcompat001-import-health-types-from-mcp-health-in-tool-executor-tests

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Move both Health-type imports in the tool-executor test module to the canonical
`shared.mcp_health` module (REQ-001; AC-1).

## Scope

- `tests/shared/test_tool_executor.py`: the multi-line `shared.mcp_config` import at
  current L15-L21 (`McpServerConfig`, `McpServerHealthRegistry`, `McpServerHealthState`,
  `StartupMode`, `TransportType`).
- Import block only; no test body change.

## Assumptions

- Verified against the current source: the file imports all five names from
  `shared.mcp_config` and has no `shared.mcp_health` import.

## Design decisions

- Split the import: `McpServerConfig`, `StartupMode`, `TransportType` stay on
  `shared.mcp_config`; the two Health names move to a new `shared.mcp_health` line.

## Alternatives considered

- None significant for an import move.

## Implementation

### Target file

`tests/shared/test_tool_executor.py`

### Procedure

1. Replace current L15-L21:
   > from shared.mcp_config import (
   >     McpServerConfig,
   >     McpServerHealthRegistry,
   >     McpServerHealthState,
   >     StartupMode,
   >     TransportType,
   > )

   with:
   > from shared.mcp_config import McpServerConfig, StartupMode, TransportType
   > from shared.mcp_health import McpServerHealthRegistry, McpServerHealthState

### Method

Import-block replacement; isort order preserved.

### Details

- Test bodies patch and construct Health objects by name; the names are unchanged, only
  their import source moves. No patch target string references the old module path
  (Plan Background).

## Compatibility considerations

- Must land before procedure 01 (the re-export deletion).

## Security considerations

- None.

## Rollback considerations

- Revert the import block.

## Validation plan

- `uv run pytest tests/shared/test_tool_executor.py -v`.
- `uv run ruff check tests/shared/test_tool_executor.py`.

## Completion criteria

- Neither Health type is imported from `shared.mcp_config` in this file (AC-1).

## Out of Scope

- The re-export deletion — procedure 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Before procedure 01 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | Import-only change; no new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | pytest, ruff |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | N/A |

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
- **Related target files**: tests/shared/test_tool_executor.py
