## Goal

Remove `_skill_ephemeral` cases from the orchestrator clearing tests (REQ-003: update tests).

## Scope

- Edit one test, delete one test, change one fixture key. `TestClearPreviousTurnEphemeralMessages` only (lines 1567-1630).

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Keep `test_removes_ephemeral_memory_injected_and_skill_ephemeral_messages` but drop its `_skill_ephemeral` history entry (line 1575) and rename it to `test_removes_ephemeral_and_memory_injected_messages` (new).
- Delete `test_skill_ephemeral_only_message_removed_without_other_ephemeral_keys` (1581). In the mixed-role test, change the assistant message key at line 1624 from `_skill_ephemeral` to `_memory_injected` so the assistant-role coverage stays.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

Apply the three edits in Design decisions.

### Method

Edit by test name; the expected remaining history in each test is unchanged because the removed entries were cleared in the original expectation.

### Details

The deleted test's docstring references a past requirement fix that no longer applies once the key is gone.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py -q` passes.
- `rg -n 'skill' tests/agent/test_orchestrator.py` has no match.

## Completion criteria

- No skill reference remains.
- The class still covers `_ephemeral`, `_memory_injected`, role mix, and empty history.

## Out of scope

- Other orchestrator tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit and delete the skill cases | Pending | — | — | |
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
- **Related target files**: tests/agent/test_orchestrator.py
