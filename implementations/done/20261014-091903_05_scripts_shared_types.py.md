## Goal

Remove the `_skill_ephemeral` field from `LLMMessage` (REQ-002: remove skill plumbing).

## Scope

- Delete one TypedDict field. Line 31 only.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- The field has no reader outside the removed command, the ephemeral key set, and tests (`rg` verified).
- Do not touch the neighboring `_ephemeral` and `_memory_injected` fields.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`scripts/shared/types.py`

### Procedure

Delete the `_skill_ephemeral: bool` line and its trailing comment.

### Method

Locate with `rg -n '_skill_ephemeral' scripts/shared/types.py`.

### Details

`shared.types` is widely imported, but only a TypedDict key is removed, so no importer changes.

## Compatibility considerations

TypedDict key removal; code that never set the key is unaffected.

## Security considerations

N/A: removal only; no new input path

## Rollback considerations

N/A: revert the commit; apply procedures 01-06 and 07-11 as one commit unit

## Validation plan

- `uv run mypy --no-namespace-packages scripts/` shows no new error.
- `rg -n '_skill_ephemeral' scripts` has no match.

## Completion criteria

- `LLMMessage` has no `_skill_ephemeral` field.
- mypy reports no new error.

## Out of scope

- Other `LLMMessage` fields and `shared/types.py` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the field | Completed | 20261014-094631 | 20261014-094631 |  |
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
- **Related target files**: scripts/shared/types.py