## Goal

Expose the pending-row model and its rendering input in the MCP status service, so the command layer can
display pending definitions without reading live lifecycle state (REQ-008, restart-only MCP; REQ-009,
pending display).

## Scope
**Release unit**: R5-pending-restart

## Assumptions
- Verified against current source: `McpStatusService.probe_all` (`mcp_status.py:60`) and the module-level
  `_resolve_health_state` (`mcp_status.py:45`) own the display state; `McpProbeResult` is defined in
  `scripts/agent/services/models.py:50` and imported here (`mcp_status.py:20`).
- The pending records themselves are stored by `PendingConfigState` (row 8); this module exposes the row
  shape the command layer renders, it does not store the records.
- No lazy rebuild from `ctx.cfg.mcp` was found (UNK-03), so a pending row cannot become observable
  before restart through this service.

## Design decisions
- Live probe rows and pending rows are distinct types, so the command layer cannot render a pending
  definition as if it were a live server.
- The pending row carries the server key, the change kind, and the field paths, matching the record shape
  row 8 stores.

## Alternatives considered
- Rendering pending rows from the live probe result — rejected: a pending definition has no probe state.

## Implementation
### Target file
`scripts/agent/services/mcp_status.py`

### Procedure
Expose the pending-row model and its rendering input so the command layer displays pending definitions
without reading live lifecycle state.

### Method
- `McpPendingRow` (new) is the rendering input row 21 consumes.
- `pending_rows()` (new) returns the rows derived from the pending records passed in; the service does
  not read lifecycle state.

### Details
- `probe_all` and `_resolve_health_state` are unchanged.

## Compatibility considerations
- Blast radius: the status service is the only owner of MCP display state; the command layer (row 21) is
  its consumer.

## Security considerations
- The row carries field paths, not values, so tokens cannot reach the display.

## Rollback considerations
- Revert the Phase 5 commit; the service holds no new state.

## Validation plan
- `uv run pytest tests/agent/services/test_agent_mcp_status.py -q`
- `uv run pytest tests/agent/commands/test_cmd_mcp.py -q` (row 37)
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- Pending rows and live probe rows are separate types, and the status service reads no lifecycle state to
  produce a pending row.

## Out of Scope
- The pending-record storage (row 8).
- The command-layer rendering (row 21).

### Companion test files
- `tests/agent/services/test_agent_mcp_status.py`
  - Procedure: assert pending MCP rows are kept separate from live probe rows and that the service does
    not read live lifecycle state to build a pending row.
  - Validation: `uv run pytest tests/agent/services/test_agent_mcp_status.py -q`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-194300 | 20261125-204907 | McpPendingRow and the static McpStatusService.pending_rows added, deliberately distinct from McpProbeResult |
| 2 | Add or update tests per Validation plan | Completed | 20261125-194300 | 20261125-204907 | companion test file companion cases in tests/agent/services/test_agent_mcp_status.py TestPendingRows: 5 green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-194300 | 20261125-204907 | R5 unit gate as row 8 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `pending_rows` is a static method that reads no ctx, probe, or registry state, and `McpPendingRow` is a distinct frozen dataclass from `McpProbeResult`: a pending definition has no probe state to render, so the command layer cannot show one as a running server (REQ-008, AC-4) | Yes | 2026-11-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008 (restart-only MCP), REQ-009 (pending display); AC-4, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/mcp_status.py`, `tests/agent/services/test_agent_mcp_status.py`