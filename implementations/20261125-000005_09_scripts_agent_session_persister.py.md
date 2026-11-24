## Goal

Persist from the one snapshot the step captured, and bound the reads the persister performs, so a shutdown snapshot is atomic and cannot run past the deadline (REQ-007: bounded single-snapshot persistence; AC-3).

## Scope
**Release unit**: R4-sequence-and-snapshot (Phase 4)

- In scope: `capture_snapshot()`, `persist_session_memories()`, `persist_session_diagnostics()`, and the reads they perform.
- Out of scope: registering the step (row 7) and the step record and reporting (row 5).

## Assumptions

- `persist_session_diagnostics()` already accepts a snapshot (`scripts/agent/session_persister.py:211-214`) and captures one itself when none is given (`scripts/agent/session_persister.py:221`), so the parameter must stay optional: existing callers pass no snapshot (`tests/agent/workflow/test_session_diagnostics_wiring.py:113`, `tests/agent/test_repl_error_handling.py:73`).
- The gap this row closes is that a snapshot can be captured inside the persist call, and that the reads carry no deadline; it is not that two snapshot generations are taken by the REPL path (`scripts/agent/repl.py:94-102` already feeds one snapshot to both persist calls).
- Reads must keep working after the write gate closes (row 3): the snapshot step reads while writes are refused (REQ-006, REQ-008).

## Design decisions

- The step owns the snapshot: when a snapshot is supplied, the persister never captures another one, so the values the step records and the values written to the store come from one read (REQ-007).
- The optional parameter is kept rather than made required: making it required would break the callers listed above for no behavioral gain.
- Reads are bounded by the remaining deadline passed by the step, and a read that cannot finish is reported as a partial snapshot rather than retried past the deadline.
- Compatibility impact: no signature changes; behavior changes only when a snapshot is supplied and when the deadline is short.

## Alternatives considered

- capture the snapshot inside each persist call — rejected: two reads of a live session can disagree, which is the non-atomicity the Plan's Problem section names.

## Implementation
### Target file
`scripts/agent/session_persister.py`

### Procedure
1. Keep `capture_snapshot()` (`scripts/agent/session_persister.py:118-138`) as the single capture point and record on the returned snapshot that it is the step's snapshot.
2. In `persist_session_diagnostics()` (`scripts/agent/session_persister.py:211-214`), use the supplied snapshot and skip the implicit capture at `scripts/agent/session_persister.py:221` whenever one is given.
3. Apply the same rule to `persist_session_memories()` so both persist calls read from the same snapshot object.
4. Add the remaining-deadline parameter to the read paths (`scripts/agent/session_persister.py:153-191`, `scripts/agent/session_persister.py:193-209`) and stop reading when it is spent, recording which parts were captured.
5. Keep the constructor (`scripts/agent/session_persister.py:107-116`) unchanged so the existing wiring in `scripts/agent/repl.py:86-88` keeps working.

### Method
- The snapshot is a value object produced once: the persist calls consume it and never re-read the session, so atomicity comes from data ownership rather than from locking.
- Deadline handling is a check before each read group, not a timeout inside a single query, so a partial snapshot is well defined.

### Details
- A partial snapshot records the sections it holds, which is what the step's `timed_out` (row 1) outcome reports (REQ-012).

### Companion test files
- `tests/agent/test_session_persister.py`
  - Procedure: assert one captured snapshot is passed to both persist methods, and that a supplied snapshot is used instead of a fresh read.
  - Validation: `uv run pytest tests/agent/test_session_persister.py -q` (REQ-007; AC-3).

## Compatibility considerations

- The snapshot parameter stays optional, so every existing caller keeps compiling and behaving as today.
- Callers that pass no snapshot keep today's implicit capture, which is the path the tests listed above exercise.

## Security considerations

- Snapshot contents stay inside the diagnostic store; nothing new is written to the log (REQ-013).

## Rollback considerations

- Revert this row's commit with row 30: the single-snapshot expectations are asserted there.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/session_persister.py` | Unit | `uv run pytest tests/agent/test_session_persister.py -q` | one capture per shutdown step, bounded reads, partial-snapshot reporting pass |
| `scripts/agent/session_persister.py` | Unit | `uv run pytest tests/agent/workflow/test_session_diagnostics_wiring.py tests/agent/test_repl_error_handling.py -q` | callers that pass no snapshot keep working |

## Completion criteria

- A shutdown step produces exactly one snapshot and both persist calls consume that object.
- A read that cannot finish inside the deadline yields a reported partial snapshot rather than an unbounded wait.

## Out of Scope

- Step registration, step records, and the write gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion row 30 |
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
- **Requirement ID**: REQ-007 (bounded single-snapshot persistence)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/session_persister.py`, `tests/agent/test_session_persister.py`
