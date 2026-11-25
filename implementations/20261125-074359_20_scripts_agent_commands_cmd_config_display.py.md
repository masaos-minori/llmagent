## Goal

Add a pending-restart section to `/config show`, separated from live values, so a startup-only change is
visible as pending rather than as applied (REQ-009, pending display).

## Scope
**Release unit**: R5-pending-restart

## Assumptions
- Verified against current source: `_ConfigDisplayMixin` (`cmd_config_display.py:29`) renders live values
  read from `ctx.cfg.tool.masked_fields`, `ctx.cfg.approval.allowed_root`, `ctx.cfg.tool.allowed_tools`,
  and `ctx.cfg.tool.plan_blocked_tools`; there is no pending section today.
- The pending records are read from `PendingConfigState` (row 8) through `AppServices` (row 23); this
  document does not store them.
- The display assembly point is the command mixin layer (`scripts/agent/commands/mixin_base.py`), which
  composes the config and MCP command handlers.

## Design decisions
- Live values and pending values are printed under separate headings, because a startup-only field that
  is not applied must not appear in the live section.
- The pending section prints field paths and change kinds only, since the pending record does not carry
  the raw value (row 8).

## Alternatives considered
- Marking pending fields inline in the live section — rejected: the reader could not tell which values
  are actually in effect.

## Implementation
### Target file
`scripts/agent/commands/cmd_config_display.py`

### Procedure
Add the pending-restart section to `/config show`, separated from live values.

### Method
- Read the pending startup-only fields from `PendingConfigState.allow_reload`-adjacent record accessors
  defined by row 8.
- Keep the existing live-section rendering unchanged.

### Details
- The section prints nothing when there are no pending records, so the current output shape is unchanged
  for a config with no pending change.

## Compatibility considerations
- Blast radius: the display mixin is shared by the config command; `tests/agent/commands/test_agent_cmd_config.py`
  asserts the CLI output and is retargeted by its own document (row 38).

## Security considerations
- No configuration value is printed, only the field path and the pending reason.

## Rollback considerations
- Revert the Phase 5 commit; the display is stateless.

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_config.py -q` (row 38)
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- A startup-only change appears under the pending heading and not under the live heading, and the live
  section output is unchanged when nothing is pending.

## Out of Scope
- The pending-state storage (row 8).
- The MCP pending display (row 21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 38 |
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
- **Requirement ID**: REQ-009 (pending display); AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/commands/cmd_config_display.py`
