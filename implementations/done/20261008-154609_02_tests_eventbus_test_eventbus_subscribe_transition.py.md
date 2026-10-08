## Goal
Make the transition module's client use a 1-second SSE idle timeout, so its tests no longer wait for the 60-second default (REQ-002, REQ-003 of the Plan).

## Scope
- Change the module's client fixture only; do not touch assertions or tests.

## Assumptions
- The shared helper accepts the new optional argument (procedure 01 runs first).
- A 1-second timeout is long enough for the module's assertions (the probe passed all nine tests in about 15 seconds).

## Design decisions
- Pass the value from the fixture, so every test in the module gets it.

## Alternatives considered
- Per-test overrides: rejected; every test in the module reads streams.

## Implementation
### Target file
tests/eventbus/test_eventbus_subscribe_transition.py

### Procedure
1. Change the fixture's helper call to pass the idle timeout of 1.0 second.
2. Run the module three times.
3. Run the EventBus suite and the full suite without deselecting the module.

### Method
A one-argument edit of the helper call in the fixture.

### Details
The fixture keeps using the helper as a context manager so the app lifespan still runs.

## Compatibility considerations
- Test only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -q --timeout=60` three times; `uv run pytest tests/eventbus -q --timeout=60 --durations=20`; the full suite once without deselection.

## Completion criteria
- All nine tests pass each time, the four formerly failing tests take well under 10 seconds, and the EventBus and full suites pass without deselection (REQ-002, REQ-003).

## Out of scope
- Other modules' idle timeouts (tracked separately).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pass the idle timeout in the fixture | Completed | 20261008-155818 | 20261008-155818 |  |
| 2 | Repeat the module and run the suites without deselection | Completed | 20261008-155818 | 20261008-155818 |  |

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
- **Requirement ID**: REQ-002 (fixture uses a short timeout), REQ-003 (tests and suites pass)
- **Source issue**: issues/20261008-115806_ebsubtimeout01_fix-timeouts-in-the-eventbus-subscribe-transition-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-154434_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-154609
- **Related target files**: tests/eventbus/test_eventbus_subscribe_transition.py