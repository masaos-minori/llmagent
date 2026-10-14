## Goal

Remove the MDQ mixin from the command registry composition (REQ-001: remove the command).

## Scope

- Delete the docstring line, the import, and the base class entry. Only the three `_MdqMixin` mentions (lines 21, 38, 63).

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Remove the mixin from the base-class list and its import; do not reorder the remaining mixins.
- Update the docstring's mixin list at line 21.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

Remove the `cmd_mdq.py — _MdqMixin: /mdq commands` docstring line, `from agent.commands.cmd_mdq import _MdqMixin`, and the `_MdqMixin,` base class entry.

### Method

Locate with `rg -n 'Mdq|cmd_mdq' scripts/agent/commands/registry.py`; edit by symbol, then run `uv run ruff format` on the file.

### Details

The remaining mixin order is unchanged, so method resolution for other commands is unchanged. The mixin counts drop to 12 total and 10 direct (procedure 07).

## Compatibility considerations

No public API change: `CommandRegistry` loses only `_cmd_mdq` and `_cmd_mdq_*`.

## Security considerations

N/A: removal only; no new input path

## Rollback considerations

N/A: removal only, applied as one commit unit with procedures 01-15 (revert the commit)

## Validation plan

- `uv run pytest tests/agent/commands/test_command_registry_consistency.py -q` passes after procedure 07.
- `uv run mypy --no-namespace-packages scripts/` shows no new error.

## Completion criteria

- `registry.py` contains no `Mdq` mention.
- Registry consistency test passes.

## Out of scope

- Other mixins and the `_COMMANDS` ownership text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the three mixin mentions | Completed | 20261014-110318 | 20261014-110318 |  |
| 2 | Run the tests that cover this file | Completed | 20261014-110318 | 20261014-110318 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-110318 | 20261014-110318 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: scripts/agent/commands/registry.py