# mcpcompat001-import-mcpserverhealthregistry-from-mcp-health-in-context

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Move the module-level `McpServerHealthRegistry` import in the agent context to the
canonical `shared.mcp_health` module (REQ-001; AC-1).

## Scope

- `scripts/agent/context.py`: the single-line import at current L31.
- No other line of the file changes.

## Assumptions

- Verified against the current source: L31 reads
  `from shared.mcp_config import McpServerHealthRegistry`.
- Overlap recorded by the Plan (Assumptions): the Frozen plans `20261027-070403_turn001`
  and `20261027-072306_memory001` also target this file (ConvState methods, field
  comments); they are disjoint from this one-line import change — rebase whichever lands
  second.

## Design decisions

- One-line module-name swap; import ordering in the existing `shared.*` block stays
  alphabetical (`mcp_health` sorts after `mcp_config`, so the line moves one position
  down within the block per isort).

## Alternatives considered

- None significant for a one-line import move.

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

1. Replace current L31:
   > from shared.mcp_config import McpServerHealthRegistry

   with:
   > from shared.mcp_health import McpServerHealthRegistry

   and re-run `uv run ruff check` so the import block keeps its isort order.

### Method

One-line replacement plus formatter ordering.

### Details

- `context.py` keeps importing `shared.config_loader`, `shared.runtime_paths`,
  `shared.runtime_tool_registry`, `shared.types` as written.

## Compatibility considerations

- Must land before procedure 01 (the re-export deletion).
- `context.py` is high-churn (8 commits/30d per the Plan); keep the edit to the import
  block and re-check after any sync.

## Security considerations

- None.

## Rollback considerations

- Revert the single line.

## Validation plan

- `uv run pytest tests/agent/test_context.py -v`.
- `uv run mypy --no-namespace-packages scripts/` and `uv run ruff check` on the file.

## Completion criteria

- The file imports `McpServerHealthRegistry` from `shared.mcp_health` (AC-1).

## Out of Scope

- The re-export deletion — procedure 01.
- The turn001/memory001 edits — their own plans.

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
- **Related target files**: scripts/agent/context.py
