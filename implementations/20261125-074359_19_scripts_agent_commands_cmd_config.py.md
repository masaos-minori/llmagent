## Goal

Make the `/reload` command catch the structured config errors and print the transaction stage, the
applied list, and the pending list, so the CLI outcome matches live state (REQ-005, stage reporting;
REQ-009, pending display; REQ-011, structured config error).

## Scope
**Release unit**: R5-pending-restart

## Assumptions
- Verified against current source: `_cmd_reload` (`cmd_config.py:43`) catches only `OSError` and
  `ValueError` (`cmd_config.py:78-83`), so a `TypeError` from a validator escapes; `source_files` is
  assigned at `cmd_config.py:61` and read by no code.
- The error types are created by row 12; `ConfigReloadValidationError` stays a `ValueError` subclass,
  so the existing catch keeps working during the transition.
- The stage and pending fields come from the outcome produced by row 6; this document does not add them.

## Design decisions
- The command prints the stage first, then the applied list, then the pending list, so a startup-only
  change is visibly pending rather than reported as applied.
- The printed error is built from the error's field path and rule name, never from the raw value.

## Alternatives considered
- Catching `TypeError` in the command layer — rejected (row 12): it would print the value and keep two
  error vocabularies.

## Implementation
### Target file
`scripts/agent/commands/cmd_config.py`

### Procedure
Catch `ConfigReloadError` and `ConfigReloadValidationError` instead of only `OSError` and `ValueError`;
print the stage, the applied list, and the pending list; keep raw values out of the printed error.

### Method
- The pending list is read from `PendingConfigState` (row 8) through the context, not re-derived here.
- `source_files` assignment stays as-is because OD-07 keeps the existing outcome fields for cliplc013.

### Details
- The stage strings printed are the four `ReloadStage` values from row 7; no new wording is invented in
  the command layer.

## Compatibility considerations
- Blast radius: the command is the only user-visible surface of the reload outcome;
  `tests/agent/commands/test_agent_cmd_config.py` asserts the CLI outcome and is retargeted by its own
  document (row 38).

## Security considerations
- No configuration value is printed; paths and tokens in `approval_protected_paths` and `memory_embed_url`
  must not reach the output.

## Rollback considerations
- Revert the Phase 5 commit; the command holds no state.

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_config.py -q` (row 38)
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- A wrong-typed value produces a printed field-level error with no uncaught `TypeError`, and the printed
  stage, applied list, and pending list match the live state after the reload.

## Out of Scope
- The pending-restart section of `/config show` (row 20).
- The error class definitions (row 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | catch lands with Phase 3, printing with Phase 5 |
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
- **Requirement ID**: REQ-002 (reload candidate through the startup parser), REQ-005 (reload transaction and stage), REQ-009 (pending display), REQ-011 (structured config error); AC-1, AC-5, AC-6
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/commands/cmd_config.py`
