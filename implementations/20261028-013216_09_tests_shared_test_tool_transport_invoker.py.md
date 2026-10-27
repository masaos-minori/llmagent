# mcpcompat001-import-mcpserverhealthregistry-from-mcp-health-in-transport-invoker-tests

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Move the `McpServerHealthRegistry` import in the transport-invoker test module to the
canonical `shared.mcp_health` import it already has (REQ-001; AC-1).

## Scope

- `tests/shared/test_tool_transport_invoker.py`: the multi-line `shared.mcp_config`
  import at current L14-L19 (`McpServerConfig`, `McpServerHealthRegistry`,
  `StartupMode`, `TransportType`) and the existing `shared.mcp_health` line at current
  L20 (`McpServerHealthState`).
- Import block only; no test body change.

## Assumptions

- Verified against the current source: this file already imports
  `McpServerHealthState` from `shared.mcp_health` (L20) while importing the Registry
  from `shared.mcp_config` (L14-L19) — the Plan's target-row evidence names this exact
  mixed state.
- Shared-file overlap: the mcpinv004 procedure `20261028-004831_03` adds three new
  tests and an `_inflight_fake` (new) helper to the same file. Disjoint regions
  (imports vs. test bodies); rebase whichever lands second.

## Design decisions

- Merge into one canonical line instead of adding a second `shared.mcp_health` import.

## Alternatives considered

- Keeping two `shared.mcp_health` import statements: rejected — ruff isort merges
  same-module imports.

## Implementation

### Target file

`tests/shared/test_tool_transport_invoker.py`

### Procedure

1. Replace current L14-L20:
   > from shared.mcp_config import (
   >     McpServerConfig,
   >     McpServerHealthRegistry,
   >     StartupMode,
   >     TransportType,
   > )
   > from shared.mcp_health import McpServerHealthState

   with:
   > from shared.mcp_config import McpServerConfig, StartupMode, TransportType
   > from shared.mcp_health import McpServerHealthRegistry, McpServerHealthState

### Method

Import-block replacement; isort order preserved.

### Details

- Names and test bodies unchanged.

## Compatibility considerations

- Must land before procedure 01 (the re-export deletion).
- Rebase point for `20261028-004831_03`.

## Security considerations

- None.

## Rollback considerations

- Revert the import block.

## Validation plan

- `uv run pytest tests/shared/test_tool_transport_invoker.py -v`.
- `uv run ruff check tests/shared/test_tool_transport_invoker.py`.

## Completion criteria

- `McpServerHealthRegistry` imported from `shared.mcp_health`; no Health type imported
  from `shared.mcp_config` in this file (AC-1).

## Out of Scope

- The re-export deletion — procedure 01.
- The mcpinv004 default-cap tests — `20261028-004831_03`.

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
- **Related target files**: tests/shared/test_tool_transport_invoker.py
