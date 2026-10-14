## Goal

Remove `_skill_ephemeral` from the core types lifecycle list (REQ-004: update documentation).

## Scope

- Edit one phrase on line 51. The lifecycle list on line 51 only.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Result: `_ephemeral`/`_memory_injected` (lifecycle).

## Alternatives considered

N/A: the docs follow the code removal

## Implementation

### Target file

`docs/40_shared/shared_02_01_types_and_protocols-core-types.md`

### Procedure

Delete `/`_skill_ephemeral`` from the lifecycle list in the `LLMMessage` description.

### Method

Edit with the Edit tool.

### Details

Keep the trailing `(Explicit in code)` marker.

## Compatibility considerations

Docs-only change.

## Security considerations

N/A: docs-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `check_docs_quality.py` and `check_docs_consistency.py --domain agent` pass.
- `rg -n 'skill' <this file>` has no match.

## Completion criteria

- The phrase no longer names `_skill_ephemeral`.

## Out of scope

- Other type descriptions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the phrase | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: docs/40_shared/shared_02_01_types_and_protocols-core-types.md
