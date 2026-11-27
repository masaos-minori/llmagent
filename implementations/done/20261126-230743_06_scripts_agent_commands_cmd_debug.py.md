## Goal

Make `/debug` raise `UnknownSubcommandError` instead of writing the message directly, so it follows the
same error contract as the other command modules (REQ-004 — one common error contract).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: lines 55-58 write "Unknown subcommand" directly, while `cmd_memory.py:131`,
  `cmd_mcp.py:420`, and `cmd_session.py:470` raise `UnknownSubcommandError`.
- The rendering change is in `scripts/agent/commands/registry.py` (document 05); this document only
  changes the raise.
- `scripts/agent/commands/exceptions.py` is a reference file.

## Design decisions

- Raise rather than write (Plan D4); the no-argument toggle path is unchanged.
- Step 3b correction (2026-11-27): `UnknownSubcommandError.__init__` takes `(sub, valid)`, so the call is
  `UnknownSubcommandError(sub, ("verbose", "normal"))`; the raised message carries the valid subcommands,
  which is the usage hint the boundary renders.

## Alternatives considered

- Keeping the direct write and special-casing the rendering — rejected by Plan D4.

## Implementation
### Target file
`scripts/agent/commands/cmd_debug.py`
### Procedure
- Replace the direct write in the unknown-subcommand branch with `raise UnknownSubcommandError(sub)`.

### Method
- Add the import of `UnknownSubcommandError` from `agent.commands.exceptions` and raise it; the usage
  hint stays in the raised message so the boundary renders it as usage.

### Details
- The `verbose`/`normal` subcommands and the no-argument toggle keep their current behavior.

### Companion test files
- `tests/agent/commands/test_cmd_debug.py`
  - Procedure: update the assertions at lines 34-43 to expect the raised error rather than written
    text.
  - Validation: `uv run pytest tests/agent/commands/test_cmd_debug.py`.

## Compatibility considerations

- Pinned direct-write assertions change under D4; the companion document covers them.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_cmd_debug.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- An unknown `/debug` subcommand raises `UnknownSubcommandError` and renders as a usage error through
  the boundary.

## Out of Scope

- The boundary classification (document 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | done |
| 2 | Add or update tests per Validation plan | Completed | — | — | companion `tests/agent/commands/test_cmd_debug.py` done |
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
- **Requirement ID**: `REQ-004` (one common error contract)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `scripts/agent/commands/cmd_debug.py`, `tests/agent/commands/test_cmd_debug.py`