# mcpcompat001-import-mcpserverhealthstate-from-mcp-health-in-mcp-status

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Move the `McpServerHealthState` import in the MCP status service to the canonical
`shared.mcp_health` module (REQ-001; AC-1).

## Scope

- `scripts/agent/services/mcp_status.py`: the multi-line import at current L16-L20.
- No other line of the file changes.

## Assumptions

- Verified against the current source: the file imports
  `McpServerHealthState, TransportType, get_effective_health_timeout` from
  `shared.mcp_config` and has no `shared.mcp_health` import yet.
- `shared.mcp_health` imports only the standard library (Plan Design), so the new import
  cannot create a cycle; the six import-layer contracts in `.importlinter` already allow
  `agent -> shared.mcp_health` (existing production importers `cmd_mcp.py`, `factory.py`).

## Design decisions

- Split the import: non-Health names stay on `shared.mcp_config`; only the Health name
  moves, keeping each imported name exactly once.

## Alternatives considered

- Importing the module (`from shared import mcp_health`): rejected — the repository
  style imports names directly.

## Implementation

### Target file

`scripts/agent/services/mcp_status.py`

### Procedure

1. Replace current L16-L20:
   > from shared.mcp_config import (
   >     McpServerHealthState,
   >     TransportType,
   >     get_effective_health_timeout,
   > )

   with:
   > from shared.mcp_config import TransportType, get_effective_health_timeout
   > from shared.mcp_health import McpServerHealthState

### Method

Import-block replacement; isort order preserved (`mcp_config` before `mcp_health`).

### Details

- The rest of the file (usage of `McpServerHealthState` in status mapping) is untouched.

## Compatibility considerations

- Must land before procedure 01 (the re-export deletion); landing after it breaks this
  module at import time.
- No patch target or module-attribute access uses the old path (Plan Background).

## Security considerations

- None.

## Rollback considerations

- Revert the two import lines; independent of every other procedure in the batch.

## Validation plan

- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` and the status
  service tests under `tests/agent` (existing coverage of `mcp_status.py`).
- `uv run mypy --no-namespace-packages scripts/` and `uv run ruff check` on the file.
- `PYTHONPATH=scripts uv run lint-imports` (six contracts kept).

## Completion criteria

- The file imports `McpServerHealthState` from `shared.mcp_health` and no Health type
  from `shared.mcp_config` (AC-1).

## Out of Scope

- The re-export deletion — procedure 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Before procedure 01 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | Import-only change; no new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | pytest, mypy, ruff, lint-imports |
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
- **Related target files**: scripts/agent/services/mcp_status.py
