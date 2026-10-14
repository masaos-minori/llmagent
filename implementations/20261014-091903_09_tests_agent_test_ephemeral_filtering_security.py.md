## Goal

Remove skill cases from the ephemeral filtering security tests (REQ-003: update tests).

## Scope

- Delete skill-only tests and update the trusted-source assertions. Skill cases only; keep memory_injection, cmd_handler, and loop_guard coverage.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Delete whole tests: `test_untrusted_source_with_skill_ephemeral_key_rejected` (line 37), `test_cmd_handler_cannot_use_skill_ephemeral` (261), `test_memory_injection_cannot_use_skill_ephemeral` (300), the three `test_skill_mixin_*` tests (313, 326, 339), and `test_multiple_ephemeral_keys_from_trusted_source_partial_failure` (352, which uses `skill_mixin`).
- Edit, do not delete: remove the `skill_mixin` line from `test_is_trusted_source_returns_true_for_known_sources` (about 370), the `skill_mixin` assert in `test_get_allowed_ephemeral_keys_returns_correct_set` (382), and the `skill_mixin` set member and assertion in `test_trusted_sources_dict_has_expected_entries` (388-398).

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/agent/test_ephemeral_filtering_security.py`

### Procedure

Apply the deletions and edits listed in Design decisions.

### Method

Edit by test name from the bottom of the file upward so line numbers stay valid; compare `pytest --collect-only -q` counts before and after.

### Details

A message with `_skill_ephemeral` is now rejected as an unknown key, with a different reason string than "Unauthorized ephemeral keys", so the rejection tests for that key are deleted, not rewritten.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/agent/test_ephemeral_filtering_security.py -q` passes.
- `rg -n 'skill' tests/agent/test_ephemeral_filtering_security.py` has no match.

## Completion criteria

- No skill reference remains.
- Coverage of the three remaining trusted sources is intact.

## Out of scope

- Non-skill security tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove skill cases and edit assertions | Pending | — | — | |
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
- **Related target files**: tests/agent/test_ephemeral_filtering_security.py
