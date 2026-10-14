## Goal

Remove `_skill_ephemeral` from the ephemeral key set (REQ-002: remove skill plumbing).

## Scope

- Shrink a frozenset literal. Lines 30-32 only.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Result must be `frozenset({"_ephemeral", "_memory_injected"})`; the turn-start clearing order in `workflow_engine_adapter.py` stays unchanged (out of scope).
- Run `ruff format` since the literal may fit on one line.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py`

### Procedure

Edit `_EPHEMERAL_KEYS` to contain only `_ephemeral` and `_memory_injected`.

### Method

Edit by symbol; leave the `EPHEMERAL_KEYS` alias and the class attribute unchanged.

### Details

No `EPHEMERAL_KEYS` assertion exists in tests (`rg` verified), so only the orchestrator tests (procedure 10) touch this behavior.

## Compatibility considerations

Messages tagged only `_skill_ephemeral` would no longer be cleared, but nothing produces them after procedure 01.

## Security considerations

N/A: removal only; no new input path

## Rollback considerations

N/A: revert the commit; apply procedures 01-06 and 07-11 as one commit unit

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py -q` passes after procedure 10.

## Completion criteria

- `_EPHEMERAL_KEYS` equals `{"_ephemeral", "_memory_injected"}`.

## Out of scope

- Clearing logic and call order.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the key set | Pending | — | — | |
| 2 | Run the tests that cover this file (updated by procedures 07-11) | Pending | — | — | |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: scripts/agent/conversation_state_manager.py
