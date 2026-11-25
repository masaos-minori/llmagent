## Goal

Show AC-5 through the CLI outcome: stage reporting, the pending list, and no uncaught `TypeError` for a
wrong-typed value (REQ-005, stage reporting; REQ-009, pending display; REQ-011, structured config error).

## Scope
**Release unit**: R3-shared-candidate

## Assumptions
- The error types are created by row 12 and the stage field by row 6; this file asserts what the command
  prints, not the class hierarchy.
- The command catches `ConfigReloadError` after row 19 changes the catch, so the no-uncaught-`TypeError`
  case is written against the new catch.

## Design decisions
- Cases assert the printed stage, the applied list, and the pending list separately, so a report that
  prints a pending field as applied fails.
- A case asserts the printed error names the field and the rule and contains no raw value.

## Alternatives considered
- Asserting the exception type instead of the printed outcome — rejected: AC-5 is about what the user sees.

## Implementation
### Target file
`tests/agent/commands/test_agent_cmd_config.py`

### Procedure

### Method
- Stage-reporting cases for `prepared`, `committed`, `rolled_back`, and `degraded`.
- A pending-list display case for a startup-only field.
- A wrong-typed-value case asserting the CLI prints a field-level error and does not raise.

### Details
- The `source_files` behavior is not asserted here; OD-07 keeps the existing fields for cliplc013.

## Compatibility considerations
- Blast radius: this file is the CLI-outcome pin for `/reload`; the pending display in `/config show` is
  asserted here through row 20.

## Security considerations
- A case asserts the printed error contains no configuration value.

## Rollback considerations
- Revert the Phase 3 commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_config.py -q`

## Completion criteria
- Every stage has a reporting case, a pending field is asserted as pending, and no wrong-typed input
  produces an uncaught exception.

## Out of Scope
- The error class definitions (row 12).
- The pending display rendering (row 20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-005 (reload transaction and stage), REQ-009 (pending display), REQ-011 (structured config error); AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `tests/agent/commands/test_agent_cmd_config.py`
