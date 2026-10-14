## Goal

Add the `/mdq` unregistered regression test (REQ-003: guard reintroduction).

## Scope

- Add one test class. Append one class after the existing `/skill` and `/note` classes; do not change existing classes.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Mirror the existing classes: assert `"/mdq"` is not among `{cmd.name for cmd in _COMMANDS}`.
- Keep the strings `cmd_mdq` and `_MdqMixin` out of the new text, because AC-002 greps `tests` for them; `/mdq` itself is allowed here (the file is on the compat allowlist).

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/agent/commands/test_removed_commands.py`

### Procedure

Add `TestRemovedMdqCommand` (new) with `test_mdq_not_in_registry` (new), importing `_COMMANDS` from `agent.commands.registry` inside the test like the existing classes.

### Method

Follow the surrounding style: class and test docstrings, `-> None`, assertion message `"/mdq should not be a registered command"`. Run `ruff format` and `ruff check` on the file.

### Details

Place after the last existing class.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/agent/commands/test_removed_commands.py -q` passes after procedures 01-03 and fails if `/mdq` is re-added.

## Completion criteria

- The new test exists and passes.

## Out of scope

- Existing removed-command tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test class | Completed | 20261014-110318 | 20261014-110318 |  |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: tests/agent/commands/test_removed_commands.py