## Goal

Remove the `_RagExportMixin` wiring and make the command boundary render `UnknownSubcommandError` as a
usage error (REQ-003, REQ-004 — one owner and one error contract).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: the import at line 38 and the class-list entry at line 59 are the wiring;
  `_emit_command_error` (lines 157-170) renders only `CommandValidationError`/`CommandParseError` as
  usage, so `UnknownSubcommandError` (a `CommandDispatchError` subclass) renders as `[error]`.
- `scripts/agent/commands/exceptions.py` is a reference file; the classification change is local to the
  boundary.

## Design decisions

- Classify `CommandDispatchError` as a usage error (Plan D4) rather than special-casing
  `UnknownSubcommandError`, so every dispatch-level usage error renders consistently.

## Alternatives considered

- Special-casing `UnknownSubcommandError` — rejected: it leaves the other `CommandDispatchError`
  subclasses inconsistent.

## Implementation
### Target file
`scripts/agent/commands/registry.py`
### Procedure
- Remove the `_RagExportMixin` import and its entry in the `CommandRegistry` class list.
- Extend the usage branch of `_emit_command_error` to include `CommandDispatchError`.
- Update the module docstring's mixin list: drop the `cmd_rag_export.py — _RagExportMixin: /compact` line
  and add `/compact` to the `_ContextMixin` line.

### Method
- `isinstance(exc, (CommandValidationError, CommandParseError, CommandDispatchError))` renders through
  `write_validation_error`; the `sqlite3.Error` and generic branches stay as they are.

### Details
- The import added for the classification is the only new import in this module.

### Companion test files
- `tests/agent/commands/test_command_registry_consistency.py`
  - Procedure: assert the mixin list no longer contains `_RagExportMixin`, that a raised
    `UnknownSubcommandError` renders as usage, and update the pinned counts at lines 181-197 from 10 MRO
    Mixin classes to 9 and from 8 direct Mixin bases to 7.
  - Validation: `uv run pytest tests/agent/commands/test_command_registry_consistency.py`.

## Compatibility considerations

- Display classification changes for dispatch-level errors; handler behavior is unchanged.
- Step 3b correction (2026-11-27): the pinned test method name `test_direct_base_mixin_count_is_9` did
  not match its assertion (8), so it is renamed to `test_direct_base_mixin_count_is_7` together with the
  count update, and the class docstring's documented total is updated from 10 to 9.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_command_registry_consistency.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- The registry no longer wires the removed mixin and an unknown-subcommand error renders as `[usage]`.

## Out of Scope

- The handler move (document 03) and the module removal (document 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | done |
| 2 | Add or update tests per Validation plan | Completed | — | — | companion `tests/agent/commands/test_command_registry_consistency.py` done |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | done |

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
- **Requirement ID**: `REQ-003` (one implementation owner) and `REQ-004` (one common error contract)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `scripts/agent/commands/registry.py`, `tests/agent/commands/test_command_registry_consistency.py`