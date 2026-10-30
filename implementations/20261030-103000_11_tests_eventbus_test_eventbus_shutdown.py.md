# Implementation Procedure: test_eventbus_shutdown.py in-flight outbox join

## Goal

Extend `tests/eventbus/test_eventbus_shutdown.py` so shutdown with an in-flight outbox
generation joins before the shared connection closes and never uses a closed connection
(REQ-008; plan AC-6).

## Scope

**In scope:**
- One new shutdown test (new) in the existing ebshutdown002 suite.

**Out of scope:**
- Shutdown sequence changes (row 06 changes none), outbox internals (row 03).

## Assumptions
- Verified at HEAD `124e340b4`: 300-line module covering the ebshutdown002 sequence (cancel
  `dlq_task`, join, lock-guarded close, `app.py:95-136`).
- Outbox work rides `app.state.dlq_task` (row 06), so the existing join already covers it —
  this test proves it rather than re-implementing the guarantee.

## Design decisions
- Test shape: with a pending `dlq_outbox` (new) row and a slow file write (monkeypatched
  `_atomic_write` that sleeps briefly or blocks on an `asyncio.Event`), stop the app lifespan
  mid-cycle and assert: (a) the lifespan exit completes without error, (b) no
  `sqlite3.ProgrammingError`/closed-connection traceback appears in logs, (c) the in-flight
  cycle finished its locked completion write (row is `done` or has a persisted failed attempt
  — either terminal state, never a half-committed one), (d) pending-but-not-yet-started rows
  remain `pending` for the next process (no corruption).
- The existing shutdown tests (characterization locks) stay byte-identical.

## Alternatives considered
- Testing `process_outbox` (new) cancellation directly without the lifespan: rejected — AC-6 is
  about the lifespan join ordering, which only the TestClient lifespan exercises.

## Implementation
### Target file
`tests/eventbus/test_eventbus_shutdown.py`

### Procedure
1. Add the new test following the module's existing lifespan-fixture style.

### Method
Monkeypatch `eventbus.dlq._atomic_write` for controlled slowness; assertions via direct DB
reads after lifespan exit (the file's existing post-shutdown read pattern).

### Details
- Bound the test deterministically (event-flag handshake, no wall-clock sleeps), matching the
  suite's determinism policy.

## Compatibility considerations
- None for production code.

## Security considerations
- N/A.

## Rollback considerations
- Revert with row 06.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_shutdown.py` (all tests, incl. unchanged
  ebshutdown002 cases); determinism re-run 3x.

## Completion criteria
- AC-6 holds with a generation in flight: join-before-close ordering proven for outbox work.

## Out of Scope
- Outbox lifecycle cases (row 10), promotion contracts (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add in-flight-join test | Pending | — | — | Plan Phase 4 |
| 2 | Run shutdown suite green incl. unchanged cases | Pending | — | — | |

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
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `tests/eventbus/test_eventbus_shutdown.py`
