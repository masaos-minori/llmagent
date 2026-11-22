## Goal

Mark the `/memory` command as async so the registry accepts the now-async `_cmd_memory` (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the `/memory` `CommandDef` and the companion test. Added to the Plan as a fallout amendment found while implementing the `cmd_memory.py` row.

## Assumptions

- Verified: `/memory` is declared with `is_async=False` (`scripts/agent/commands/command_defs_list.py:160-163`) and `CommandRegistry.__init__` raises `TypeError` when `CommandDef.is_async` differs from the handler kind (`scripts/agent/commands/registry.py:80-90`); `_invoke_handler` awaits only when `is_async` is true (`scripts/agent/commands/registry.py:130-137`).
- Corrects the Plan's earlier claim that the registry awaits coroutine handlers regardless of the flag.

## Design decisions

- Change only the `is_async` value of the `/memory` entry to True; no other command changes.

## Alternatives considered

Rejected: leaving `_cmd_memory` sync (it cannot await the controller-based confirmation).

## Implementation
### Target file
`scripts/agent/commands/command_defs_list.py`

### Procedure
1. Set `is_async=True` on the `/memory` `CommandDef`.

### Method
One-line edit.

### Details
- Run the command registry consistency and definition-sync tests.

### Companion test files
- `tests/agent/commands/test_command_def_sync.py`
  - Procedure: Make `test_memory_registered_subcommands_equal_the_handler_valid_set` async and await `registry._cmd_memory("no-such-subcommand")` inside `pytest.raises`.
  - Validation: `uv run pytest tests/agent/commands/test_command_def_sync.py tests/agent/commands/test_command_registry_consistency.py -q`

## Compatibility considerations

Slash command behavior is unchanged for operators; dispatch now awaits `/memory`.

## Security considerations

N/A: dispatch flag only.

## Rollback considerations

N/A: revert the commit together with the `cmd_memory.py` change.

## Validation plan

- `uv run pytest tests/agent/commands -q`
- `uv run ruff check scripts/agent/commands/command_defs_list.py && uv run mypy scripts/agent/commands/command_defs_list.py`

## Completion criteria

- `/memory` is async and the registry constructs; command definition tests pass.

## Out of Scope

Other commands, handler bodies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213733 | 20261122-213733 | Changed: scripts/agent/commands/command_defs_list.py (and companions) |
| 2 | Add or update tests per Validation plan (companion test files included) | Completed | 20261122-213733 | 20261122-213733 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-213733 | 20261122-213733 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-004` (async Memory handlers awaited at dispatch; plan amendment 2026-11-22, fallout)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/commands/command_defs_list.py`, `tests/agent/commands/test_command_def_sync.py`
