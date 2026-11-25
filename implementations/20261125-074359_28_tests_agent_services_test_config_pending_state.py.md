## Goal

Prove the pending contract: MCP add, change, and remove records and startup-only fields survive across
commands, never appear as applied, are cleared by a restart, and a `/reload` after `degraded` is refused
(REQ-003, startup-only fields stay pending; REQ-008, restart-only MCP; REQ-009, pending display;
REQ-012, degraded guard).

## Scope
**Release unit**: R5-pending-restart

## Assumptions
- `PendingConfigState` is created by row 8; this file is written before it, per the Plan's Phase 5 order
  (tests first).
- The tests run with a live lifecycle and assert no observable change, which is the check for UNK-03
  (whether any state is rebuilt lazily from `ctx.cfg.mcp`).

## Design decisions
- Pending records are asserted as structured records, not as printed strings, so the display layer and
  the storage layer are validated against the same shape.
- Cross-command survival is asserted by calling the pending state from two separate command invocations,
  not by holding a single object.

## Alternatives considered
- Asserting the CLI output only — rejected: it would pass even if the record were wrong and the display
  happened to print it.

## Implementation
### Target file
`tests/agent/services/test_config_pending_state.py` (new)

### Procedure

### Method
- Cases for an added, changed, and removed MCP definition; each asserts nothing was applied and no
  lifecycle method was called.
- Cases for pending startup-only fields, asserted against `startup_only_for(section)` from row 4.
- A case asserting the records survive across commands and are cleared by a restart.
- A case asserting `allow_reload` refuses a later `/reload` after `degraded`.

### Details
- The tests assert `ctx.cfg.mcp` and `RuntimeToolRegistry` are unchanged after a pending MCP change.

## Compatibility considerations
- New file; no pending-state coverage exists today.

## Security considerations
- A case asserts a pending record does not carry a value, only the field path.

## Rollback considerations
- Revert the Phase 5 commit.

## Validation plan
- `uv run pytest tests/agent/services/test_config_pending_state.py -q`

## Completion criteria
- Every pending kind has a test showing it is recorded, survives across commands, is never reported as
  applied, and is cleared by a restart; the degraded guard has a refusal test.

## Out of Scope
- The display rendering (rows 20, 21).
- The container wiring (rows 23, 24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | tests written before row 8 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `tests/agent/services/test_config_pending_state.py`
