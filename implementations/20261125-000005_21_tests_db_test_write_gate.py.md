## Goal

Create the test file that pins the write gate: its three states, the refusal of every db write entry point, the authorized-operation context, and the refused-write counter (REQ-004: writes stop when shutdown starts; REQ-005: the refusal is enforced in the db layer; AC-2).

## Scope
**Release unit**: R2-write-gate (Phase 2)

- In scope: `tests/db/test_write_gate.py` and the expectations it locks.
- Out of scope: the gate implementation (row 2), the write-path checks (row 3), and the exports (row 4), which this file asserts against but does not define.

## Assumptions

- The file does not exist yet, so it is written against the contract rows 2, 3 and 4 declare, and it runs before those rows land only as a failing specification.
- The write entry points the refusal must cover are the ones in `scripts/db/helper.py:350-543`; the test drives them through the public surface rather than through private helpers.

## Design decisions

- Test the gate directly and the write paths through the gate: one set of cases for state transitions and authorization, one set per write entry point for the refusal, so a regression names which half broke.
- Assert the counter as behavior, not as a log line: a caller that swallows the exception must still be visible in the count (REQ-012).
- Keep the tests deterministic: no wall-clock sleeps and no real subprocess, so the suite stays order-independent.

## Alternatives considered

- fold these cases into `tests/db/test_sqlite_helper.py` — rejected: the gate is a new public API with its own contract, and the helper file already covers connection and statement behavior.

## Implementation
### Target file
`tests/db/test_write_gate.py` (new)

### Procedure
1. Cover the state machine: open allows a write, closing refuses an unauthorized write, closed refuses every write.
2. Cover the authorized-operation context: a write inside it succeeds in `closing`, and the authorization does not outlive the block.
3. Cover each write entry point in `scripts/db/helper.py:350-543` and assert `WriteGateClosed` (new) is raised in `closing` and `closed`.
4. Cover the read paths: reads succeed in every state (REQ-006, REQ-008).
5. Cover the refused-write counter: each refusal increments it once, including a swallowed exception.

### Method

- One fixture that builds a gate in a chosen state, so each case states the state it tests rather than arranging it inline.

### Details

- The exception assertions check the type only, never a message that embeds a path (REQ-013).

## Compatibility considerations

- New file: no existing test is changed, and the public-API expectations live in row 24.

## Security considerations

- N/A: no path or credential is asserted.

## Rollback considerations

- N/A: revert the Phase 2 commit; rows 2, 3, 4 and 25 are the same unit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/db/test_write_gate.py` | Unit | `uv run pytest tests/db/test_write_gate.py -q` | states, refusal, authorization, counter pass |
| `tests/db/test_write_gate.py` | Unit | `uv run pytest tests/db/test_sqlite_helper.py tests/db/test_helper_thread_safety.py tests/db/test_db_public_api.py -q` | the guarded paths and exports agree with the gate contract |

## Completion criteria

- Every write entry point has a refusal case, every state has a case, and the counter is asserted for each refusal.

## Out of Scope

- The gate implementation, the exports, and the shutdown sequence that closes the gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | this row is the test row |
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
- **Requirement ID**: REQ-004 (writes stop at shutdown), REQ-005 (enforced in the db layer)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `tests/db/test_write_gate.py`, `scripts/db/write_gate.py`, `scripts/db/helper.py`
