## Goal

Render pending MCP definition changes in `/mcp status` through an extracted helper, so the pending view
is shown without pushing `_cmd_mcp_status` above the complexity gate (REQ-008, restart-only MCP;
REQ-009, pending display).

## Scope
**Release unit**: R5-pending-restart

## Assumptions
- Verified against current source: `_cmd_mcp_status` (`cmd_mcp.py:123`) has radon complexity E(39), so
  adding the pending display inline is not allowed; the file already has extracted formatters
  (`_format_health_interpretation` at `cmd_mcp.py:33`, `_format_availability_display` at `cmd_mcp.py:69`).
- The pending rows come from `PendingConfigState` (row 8) through `AppServices` (row 23); the rendering
  input model is exposed by row 22.
- Live probe rows come from `McpStatusService.probe_all` and must stay separate from pending rows.

## Design decisions
- The pending rendering is a module-level helper, consistent with the existing formatters, so the
  complexity of `_cmd_mcp_status` drops below the radon C gate.
- Pending rows are printed after the live rows under a distinct heading, because a pending definition has
  no live process to probe.

## Alternatives considered
- Raising the complexity gate for this file — rejected: the gate is a repository rule
  (`rules/30_module-architecture.md`), and the extraction is the intended fix.

## Implementation
### Target file
`scripts/agent/commands/cmd_mcp.py`

### Procedure
Extract the pending-row rendering into a helper and display the pending section, bringing
`_cmd_mcp_status` below the radon C gate.

### Method
- The helper takes the pending records from row 8 and writes the heading and the rows.
- `_cmd_mcp_status` keeps its live-probe behavior unchanged and calls the helper once.

### Details
- The helper prints the server key, the change kind, and the field paths that changed; no raw value.

## Compatibility considerations
- Blast radius: `tests/agent/commands/test_cmd_mcp.py` reaches the deleted private method
  `_classify_mcp_server_changes` and must be retargeted by its own document (row 37) before this change
  lands; live probe-row assertions stay unchanged.

## Security considerations
- No configuration value is printed; `auth_token` changes are named by field path only.

## Rollback considerations
- Revert the Phase 5 commit; the command holds no state.

## Validation plan
- `uv run pytest tests/agent/commands/test_cmd_mcp.py -q` (row 37)
- `uv run radon cc scripts/agent/commands/cmd_mcp.py` — `_cmd_mcp_status` below the C gate
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- An added, changed, or removed MCP definition appears as a pending row, live probe rows are unchanged,
  and `_cmd_mcp_status` is below the radon C gate.

## Out of Scope
- The pending-state storage (row 8).
- The pending-row model (row 22).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 37 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | radon gate included |

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
- **Requirement ID**: REQ-008 (restart-only MCP), REQ-009 (pending display); AC-4, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/commands/cmd_mcp.py`
