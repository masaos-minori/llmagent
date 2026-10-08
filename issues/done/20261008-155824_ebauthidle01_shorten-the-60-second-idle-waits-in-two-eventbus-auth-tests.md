# Shorten the 60-second idle waits in two EventBus auth tests

## Priority
Low

## Summary
Two tests in the EventBus authentication test module each take about 60 seconds because the subscribe stream is only closed by the server's idle timeout; shorten the idle timeout for them (and check whether other EventBus tests have the same pattern), cutting the EventBus suite by about two minutes.

## Background
Found while fixing the subscribe-transition tests, whose cause was the same default 60-second idle timeout. After that fix, the EventBus suite runs in about 3 minutes (335 tests passed, 1 skipped) instead of about 7 minutes, and a duration report of the slowest tests shows what remains.

## Problem
- `tests/eventbus/test_eventbus_auth.py::TestSubscribeAuth::test_subscribe_with_timeout_disconnect_detection` takes about 60 seconds and `...::test_subscribe_with_valid_consumer_token` takes about 60 seconds; together they are about two thirds of the module-independent slow time.
- Both open a subscribe stream and wait for the server to end it; the class builds its own fixture application and does not shorten the 60-second default idle timeout (the shared client helper now has an optional argument for this, but this class does not use the helper).
- The next slowest tests take about 6 seconds or less, so these two dominate the suite's runtime.
- The first test asserts only that the stream closes within 120 seconds, so the 60-second wait is incidental to what it checks.

## Reason for Change
A shorter suite is run more often and fails faster; the waits add no verification value.

## Implementation Intent
- Set a short idle timeout (1 second) on the configuration used by this class's fixture application, using the attribute-assignment pattern other modules use, and keep the assertions; consider tightening the 120-second bound in the first test accordingly.

## Target Files or Areas
- `tests/eventbus/test_eventbus_auth.py` (the test class's fixture setup and the first test's bound)

## Required Changes
- Apply the short idle timeout to the configuration of this class's fixture application.
- Confirm that both tests pass in a few seconds and that the other tests of the module are unaffected.
- Re-run the duration report for the EventBus suite and record any remaining test above about 5 seconds as a follow-up.

## Constraints
- Do not change what the tests assert about authorization; do not add arbitrary sleeps.
- The configuration validates the idle timeout against the heartbeat interval at construction, so assign the value after construction.

## Acceptance Criteria
- Both tests finish in well under 10 seconds.
- All tests in the module pass; the EventBus suite no longer contains a test slower than about 10 seconds.

## Testing Expectations
Run the module, then the EventBus suite with a duration report, then the full suite once.

## Documentation Impact
Not required.

## Out of Scope
- Production code and other test modules.

## Dependencies
- Related to the earlier fix that gave the shared EventBus test helper an optional idle-timeout argument.

## Unresolved Questions
- Whether the first test's intent (disconnect detection under the test client) needs the real default timeout to be meaningful (unknown; its docstring suggests it only checks that the stream closes).

## AI Implementation Instruction
Change only the fixture setup and, if appropriate, the bound in the first test. Stop and ask if shortening the timeout changes what the test is meant to prove.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261008-154434_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-155824
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`
