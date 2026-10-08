## Goal
Add an end-to-end reconnect test that uses the real resume helper through the subscribe endpoint for in-order and out-of-order acknowledgements (REQ-001, REQ-003 of the Plan).

## Scope
- Add tests to the restart-resume module without changing existing tests.

## Assumptions
- The module's client fixture builds the production app; the database helpers used by its existing tests are available.

## Design decisions
- Existing tests assert only the helper's return value; the new tests replay through the route so the integration is covered.

## Alternatives considered
- Putting these in the subscribe test module: rejected; the restart module already owns offset-resume scenarios.

## Implementation
### Target file
tests/eventbus/test_eventbus_restart_resume.py

### Procedure
1. Read the existing resume tests and fixture.
2. Add a test for in-order acknowledgements up to N: reconnecting with the consumer id replays N+1 first and continues in order.
3. Add a test for an out-of-order acknowledgement: reconnecting replays the lowest unacked event first (included) and the following events in order.
4. Confirm the tests fail before the route fix and pass after.

### Method
Insert events and acknowledge them with the database helpers on the app state, then open the subscribe stream with the consumer id and read the ordered ids.

### Details
Use exact expected lists of seq values; keep the SSE idle timeout short through the fixture.

## Compatibility considerations
- Tests only.

## Security considerations
- Fake tokens only.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run ruff format` and `ruff check` on the file; `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -q --timeout=60`.

## Completion criteria
- Both reconnect tests exist, fail before the fix for the stated reason, and pass after it (REQ-001, REQ-003).

## Out of scope
- Changes to existing tests; other modules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add in-order and out-of-order reconnect tests through the route | Completed | 20261008-122614 | 20261008-122614 |  |
| 2 | Confirm failures before the route fix and passes after | Completed | 20261008-122614 | 20261008-122614 |  |

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
- **Requirement ID**: REQ-001 (resume through the route), REQ-003 (tests)
- **Source issue**: issues/20261007-164638_ebresume01_fix-off-by-one-in-eventbus-subscribe-resume-position.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-120658_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-121500
- **Related target files**: tests/eventbus/test_eventbus_restart_resume.py