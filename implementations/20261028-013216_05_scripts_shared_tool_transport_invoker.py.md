# mcpcompat001-import-health-types-from-mcp-health-in-tool-transport-invoker

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Move both Health-type imports in the transport invoker to the canonical
`shared.mcp_health` module (REQ-001; AC-1).

## Scope

- `scripts/shared/tool_transport_invoker.py`: the multi-line import at current
  L16-L21 (`McpServerConfig`, `McpServerHealthRegistry`, `McpServerHealthState`,
  `StartupMode` from `shared.mcp_config`).
- Import block only; no body change.

## Assumptions

- Verified against the current source: L16-L21 import all four names from
  `shared.mcp_config`; the file has no `shared.mcp_health` import yet.
- Shared-file overlap (Plan Dependencies): the mcpinv001 procedures
  (`20261028-004925_01`, pre-send fail-closed gate) and the mcpinv004 procedure
  (`20261028-004831_01`, `DEFAULT_PER_SERVER_CONCURRENCY` (new) cap) edit the body of this
  same file. Those edits are disjoint from the import block; rebase whichever lands
  second. The superseded duplicate plan `20261027-115908` is archived without procedures.

## Design decisions

- Split the import: `McpServerConfig` and `StartupMode` stay on `shared.mcp_config`;
  the two Health names move to a new `shared.mcp_health` line, keeping isort order
  (`mcp_config` then `mcp_health`).

## Alternatives considered

- Importing the health names via `TYPE_CHECKING`: rejected — both names are used at
  runtime (type-annotated constructor parameters plus registry/state instantiation
  paths), and the sibling test files already import them at runtime.

## Implementation

### Target file

`scripts/shared/tool_transport_invoker.py`

### Procedure

1. Replace current L16-L21:
   > from shared.mcp_config import (
   >     McpServerConfig,
   >     McpServerHealthRegistry,
   >     McpServerHealthState,
   >     StartupMode,
   > )

   with:
   > from shared.mcp_config import McpServerConfig, StartupMode
   > from shared.mcp_health import McpServerHealthRegistry, McpServerHealthState

### Method

Import-block replacement; no body edit in this procedure.

### Details

- After the change the module imports neither Health name from `shared.mcp_config`.

## Compatibility considerations

- Must land before procedure 01 (the re-export deletion).
- Rebase point for the mcpinv001 and mcpinv004 procedures listed in Assumptions.

## Security considerations

- None.

## Rollback considerations

- Revert the import block; independent of the body edits by other procedures.

## Validation plan

- `uv run pytest tests/shared/test_tool_transport_invoker.py -v`.
- `uv run mypy --no-namespace-packages scripts/` and `uv run ruff check` on the file.

## Completion criteria

- Both Health names imported from `shared.mcp_health` (AC-1); file body behavior
  unchanged by this procedure.

## Out of Scope

- The re-export deletion — procedure 01.
- Semaphore and pre-send-gate body edits — procedures `20261028-004831_01` and
  `20261028-004925_01`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Before procedure 01 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | Import-only change; no new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | pytest, mypy, ruff |
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
- **Related target files**: scripts/shared/tool_transport_invoker.py
