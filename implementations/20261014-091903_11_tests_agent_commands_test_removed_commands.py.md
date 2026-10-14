## Goal

Add the `/skill` unregistered regression test (REQ-003: update tests).

## Scope

- Add one test class. Append one class to this file; do not change existing classes.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Mirror `TestRemovedNoteCommand`: assert `"/skill"` is not among `{cmd.name for cmd in _COMMANDS}`.
- This test is the effective guard against reintroduction, because `_REMOVED_NAME_PATTERNS` scans `*.md` only and is opt-in.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/agent/commands/test_removed_commands.py`

### Procedure

Add `TestRemovedSkillCommand` (new) with `test_skill_not_in_registry` (new), importing `_COMMANDS` from `agent.commands.registry` inside the test like the existing classes.

### Method

Follow the surrounding style: docstring on class and test, `-> None` annotation, assertion message `"/skill should not be a registered command"`.

### Details

Place after `TestRemovedNoteCommand`. Run `ruff format` and `ruff check` on the file.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/agent/commands/test_removed_commands.py -q` passes after procedures 01-03; it fails if `/skill` is re-added.

## Completion criteria

- The new test exists and passes.

## Out of scope

- Existing removed-command tests; `_REMOVED_NAME_PATTERNS`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test class | Pending | — | — | |
| 2 | Run the affected tests | Pending | — | — | |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: tests/agent/commands/test_removed_commands.py
