## Goal

Remove skill_mixin cases from the message schema tests (REQ-003: update tests).

## Scope

- Delete skill-only tests and single skill assertions. Lines 153-260 region only; keep every non-skill case.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Delete whole tests: `test_trusted_skill_mixin_can_add_skill_ephemeral_key` (line 153) and `test_multiple_ephemeral_keys_from_trusted_source_accepted` (line 176, whose only source is `skill_mixin`).
- Edit, do not delete: in `TestTrustedSourceHelpers`, remove the `skill_mixin` lines at about 241, 251, and 260, and change `assert len(TRUSTED_SOURCES) == 4` (about 262) to `== 3`.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/agent/test_message_schema.py`

### Procedure

Remove the tests and assertion lines that reference `skill_mixin` or `_skill_ephemeral`.

### Method

Edit by test name from the bottom of the file upward; compare `pytest --collect-only -q` counts before and after (only the two deleted tests should disappear).

### Details

`get_allowed_ephemeral_keys("skill_mixin")` now returns an empty set, so rewriting that assertion is unnecessary; delete it.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/agent/test_message_schema.py -q` passes.
- `rg -n 'skill' tests/agent/test_message_schema.py` has no match.

## Completion criteria

- No skill reference remains.
- Non-skill tests are unchanged and passing.

## Out of scope

- Non-skill schema tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove skill cases and assertions | Pending | — | — | |
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
- **Related target files**: tests/agent/test_message_schema.py
