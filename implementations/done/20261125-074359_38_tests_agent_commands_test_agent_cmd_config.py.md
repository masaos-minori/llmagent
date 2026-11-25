## Goal

Show AC-5 through the CLI outcome: stage reporting, the pending list, and no uncaught `TypeError` for a
wrong-typed value (REQ-005, stage reporting; REQ-009, pending display; REQ-011, structured config error).

## Scope
**Release unit**: R3-shared-candidate

The Plan maps this procedure to target rows 3 and 5, so its cases are written in two runs: the
wrong-typed-value and no-`TypeError` cases land with R3 (Phase 3 step 1), and the stage-reporting and
pending-list cases land with R5 (Phase 5 step 1), after rows 7 and 19 create the stage and the pending
view. The document is archived only after the R5 run passes.

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
Write the CLI-outcome cases in two runs: the wrong-typed-value case with the R3 candidate work, then the
stage-reporting and pending-list cases with the R5 display work.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-194300 | 20261125-204907 | two runs: wrong-typed case with R3, stage and pending cases with R5 R3 run: wrong-typed-value case added (test_reload_wrong_typed_value_prints_field_error_without_raw_value); stage-reporting and pending-list cases remain with R5 after rows 7 and 19 R5 run: TestCmdReloadStageReporting covers prepared, committed, rolled_back and degraded; TestCmdPendingList and TestCmdReloadPendingList pin the container pending list; TestConfigShowPendingSection pins /config show |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-194300 | 20261125-204907 | 35 passed; completion criteria met only after the R5 run 46 passed in this file; R5 unit gate as row 8 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | The pending-display cases attach a real `PendingConfigState` to `ctx.services.pending_config`: `pending_state_for` returns `None` for a `MagicMock` container, so a mocked ctx cannot pin the pending output | Yes | 2026-11-25 |
| 2 | The pending-only fixture sets `services_required.runtime_tools = None`: `prepare_runtime_tools()` registers a step whenever a registry is wired, which would move the stage from `prepared` to `committed` | Yes | 2026-11-25 |
| 2 | The second `/reload` in `test_the_pending_list_survives_to_the_next_reload_command` patches `ConfigLoader.load_all` with the same payload, so the surviving pending field is not replaced by the repository's real `config/*.toml` values | Yes | 2026-11-25 |

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