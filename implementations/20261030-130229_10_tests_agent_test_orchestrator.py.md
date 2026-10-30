## Goal

Pin the turn-level failure contract in `tests/agent/test_orchestrator.py`: halted and timed-out turns carry a stable `error_kind` in the returned result and the turn-end audit with and without `on_error`, task status and audit agree, and no turn ends empty without an error (`REQ-004`, typed failure result; `REQ-005`, LLM-failure results; `REQ-008`, invariant; `REQ-009`, tests).

## Scope

- Modify only `tests/agent/test_orchestrator.py`.

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 4 tests, written with the adapter row (row 05) and after the wfrecovery001 Plan's orchestrator test edits in other regions of this file. Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `test_orchestrator.py` is also a target of `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (status-write and resume tests, `:2095-2118`, `:2627-2765`) and `plans/20261030-001153_turnadr001_align-adr014-loop-ownership.md` (a guard test near `:2933`): compatible, different regions.
- Existing tests in scope: `TestHandleTurnInvokesWorkflowEngine` (`:265`, returns normally on workflow timeout), `TestEntryWorkFailureIsNotRetried` (`:673`, asserts task `halted` and `on_error` called once), and `TestTurnEndBracket::test_halt_emits_single_turn_end_and_invokes_on_error` (`:1357`).
- Production supplies `on_error` (`startup_component_init.py:77-81`); the tests build the orchestrator with and without the callback.

## Design decisions

- Extend the existing halt and timeout tests with assertions on the returned `error_kind` and on the emitted `turn_end` event's `error_kind`; add a callback-absent variant rather than a new harness.

## Alternatives considered

- N/A: test row; cases come from the Plan's Tests section.

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. In the halt and timeout tests, assert workflow_halted / workflow_timeout in the turn-end audit event and the adapter's returned tuple, and keep the existing `on_error` and task-status assertions.
2. Add the same scenarios with `on_error=None`, asserting the same outcome and no exception.
3. Add an LLM-level failure scenario: the task ends `failed` with exactly one status write (no `completed` write), and the turn-end `error_kind` equals the result's kind.
4. Add an invariant test over halt, timeout, LLM failure, and cancellation: never (empty answer, `error_kind` `None`, status `halted` or `failed`).
5. Add a side-effect scenario: a failure after a non-READ tool call executes is not retried.

### Method

- Use the harness patterns already in `TestEntryWorkFailureIsNotRetried` (a temp workflow database and a recording `StateStore` subclass) to record status writes.
- Read the emitted audit event from the audit logger test double the existing `TestTurnEndBracket` tests use.

### Details

- Write the new tests first and confirm they fail before the adapter row.
- Keep each scenario independent so a failure points to one outcome.

## Compatibility considerations

- N/A: tests only; existing assertions on `on_error` and status remain.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py -v`
- `uv run ruff format tests/agent/test_orchestrator.py`, `uv run ruff check tests/agent/test_orchestrator.py`

## Completion criteria

- Halt, timeout, LLM failure, and cancellation each have an assertion on returned kind, audit kind, and status; the invariant test passes; the callback-absent variants pass.

## Out of Scope

- Engine-level cases (row 08), tool runner flag (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend and add the orchestrator tests | Pending | — | — | Plan Phase 4 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-005, REQ-008, REQ-009 (turn-level failure tests)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: tests/agent/test_orchestrator.py
