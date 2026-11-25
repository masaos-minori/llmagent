## Goal

Create the pending-state service that records MCP definition changes and startup-only fields until a
restart, and refuses a later `/reload` after a `degraded` stage (REQ-003, startup-only fields stay
pending; REQ-008, restart-only MCP; REQ-009, pending display; REQ-012, degraded guard).

## Scope
**Release unit**: R5-pending-restart

## Assumptions
- Nothing records pending configuration state across CLI calls today; `config_outcome_classification.py`
  returns display strings and runs after the mutation.
- The pending record is derived from the same parsed candidate the restart path reads, so a pending row
  and the parsed definition cannot disagree (Plan `Risks`).
- The service lives on `AppServices` (row 23) and is constructed in `factory.py` (row 24), the
  placement pattern cliplc003 landed for `MaintenanceJobRegistry`.
- A restart clears the pending records; no lazy rebuild from `ctx.cfg.mcp` was found (UNK-03).

## Design decisions
- Pending records are structured (added, changed, removed) rather than display strings, so the display
  layer and the tests read the same shape (OD-03).
- The degraded guard lives with the pending state because the guard must survive across commands.

## Alternatives considered
- Keeping the live cleanup call for removed servers — rejected (OD-03).
- Making the pending state a second source of truth for MCP configuration — rejected: it stores only
  the record of a change, not a definition.

## Implementation
### Target file
`scripts/agent/services/config_pending_state.py` (new)

### Procedure
Define `PendingConfigState` (new) with the pending MCP records, the pending startup-only fields, and
the reload generation guard.

### Method
- `PendingMcpRecord` (new) carries the server key, the change kind, and the field paths that changed;
  it is the rendering input row 21 and row 22 display.
- `record_startup_only` (new) takes the fields `startup_only_for(section)` returned.
- `allow_reload` (new) returns false once a `degraded` stage is recorded.

### Details
- No configuration value is stored beyond the field path and the change kind; the raw value is not
  kept, so the display layer cannot print it.
- The module is read by `cmd_config_display.py` (row 20) and `cmd_mcp.py` (row 21) only.

## Compatibility considerations
- New module; no existing caller. `tests/agent/services/test_config_pending_state.py` (row 28) is its
  coverage.

## Security considerations
- Pending records must not carry tokens such as `auth_token`; the record names the field, not the value.

## Rollback considerations
- Revert the Phase 5 commit; the state is in-memory only and nothing is persisted.

## Validation plan
- `uv run pytest tests/agent/services/test_config_pending_state.py tests/agent/commands/test_cmd_mcp.py tests/agent/commands/test_agent_cmd_config.py -q`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- A pending MCP add, change, or remove and a pending startup-only field survive across commands, never
  appear as applied, and are cleared by a restart; a `/reload` after `degraded` is refused.

## Out of Scope
- The display rendering (rows 20, 21) and the container wiring (rows 23, 24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 28 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (startup-only fields stay pending), REQ-008 (restart-only MCP), REQ-009 (pending display), REQ-012 (degraded guard); AC-2, AC-4, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/config_pending_state.py`
