# mcpcompat001-import-mcpserverhealthstate-from-mcp-health-in-startup-reporter

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Move the deferred `McpServerHealthState` import in the startup reporter to the
canonical `shared.mcp_health` module (REQ-001; AC-1).

## Scope

- `scripts/agent/startup_reporter.py`: the deferred (function-local) import at current
  L84 inside `report_readiness()`.
- No other line of the file changes.

## Assumptions

- Verified against the current source: L84 reads
  `from shared.mcp_config import McpServerHealthState` inside `report_readiness`.
- The deferral itself (a function-local import) is intentional in this file and is
  kept; only the module name changes.

## Design decisions

- Keep the import deferred at the same location; changing it to a module-level import is
  out of scope (behavior-neutral import cost change is not what the Plan asks for).

## Alternatives considered

- Promoting the import to module level while moving it: rejected — unrelated behavior
  change.

## Implementation

### Target file

`scripts/agent/startup_reporter.py`

### Procedure

1. Replace current L84:
   > from shared.mcp_config import McpServerHealthState

   with:
   > from shared.mcp_health import McpServerHealthState

### Method

One-line replacement inside the existing function body.

### Details

- The file has no other `shared.mcp_config` Health usage.

## Compatibility considerations

- Must land before procedure 01 (the re-export deletion).

## Security considerations

- None.

## Rollback considerations

- Revert the single line.

## Validation plan

- `uv run pytest tests/agent/test_startup_reporter.py -v`.
- `uv run mypy --no-namespace-packages scripts/` and `uv run ruff check` on the file.

## Completion criteria

- The deferred import references `shared.mcp_health` (AC-1).

## Out of Scope

- The re-export deletion — procedure 01.

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
- **Related target files**: scripts/agent/startup_reporter.py
