## Goal

Remove the `skill_mixin` trusted source (REQ-002: remove skill plumbing).

## Scope

- Delete one `TRUSTED_SOURCES` entry and update the docstring. Line 21 entry and the line 4 docstring only.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- After removal a message carrying `_skill_ephemeral` is an unknown extra key and is rejected by the existing whitelist check; no new validation code is needed.
- `_ALL_EPHEMERAL_KEYS` is derived from `TRUSTED_SOURCES`, so it shrinks automatically.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`scripts/agent/message_schema.py`

### Procedure

Delete `"skill_mixin": {"_skill_ephemeral"},` and change the module docstring to mention only `_ephemeral` and `_memory_injected`.

### Method

Edit by symbol; keep the remaining three sources (`cmd_handler`, `memory_injection`, `loop_guard`) in their order.

### Details

Docstring target text: keys like ``_ephemeral`` or ``_memory_injected``.

## Compatibility considerations

Any caller still passing `source="skill_mixin"` would have its `_skill_ephemeral` key stripped; the only caller is deleted in procedure 01.

## Security considerations

Narrows the trusted-source table; no widening.

## Rollback considerations

N/A: revert the commit; apply procedures 01-06 and 07-11 as one commit unit

## Validation plan

- `uv run pytest tests/agent/test_message_schema.py tests/agent/test_ephemeral_filtering_security.py -q` passes after procedures 08-09.
- `rg -n 'skill' scripts/agent/message_schema.py` has no match.

## Completion criteria

- `TRUSTED_SOURCES` keys equal `cmd_handler`, `memory_injection`, `loop_guard`.
- Docstring no longer names `_skill_ephemeral`.

## Out of scope

- `ROLE_KEY_WHITELIST`, validation logic, other sources.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the entry and docstring mention | Completed | 20261014-094631 | 20261014-094631 |  |
| 2 | Run the tests that cover this file (updated by procedures 07-11) | Completed | 20261014-094631 | 20261014-094631 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-094631 | 20261014-094631 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: scripts/agent/message_schema.py