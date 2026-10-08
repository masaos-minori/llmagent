# Fix timeouts in the EventBus subscribe-transition tests

## Priority
Medium

## Summary
Four tests in the EventBus subscribe-transition test module time out (more than 40 seconds each), so the EventBus suite cannot pass or finish quickly; find the cause and make them deterministic.

## Background
Found while running the EventBus suite for the health and publish route fix. The same tests also time out with that change reverted, so they are a pre-existing problem and were excluded from the full-suite run recorded for that work (the rest of the repository passed).

## Problem
- `test_keyset_pagination_no_duplicate_at_boundary`, `test_live_path_catches_events_after_replay`, `test_reconnect_with_consumer_offset_resumes_correctly`, and `test_since_seq_precedence_over_consumer_offset` fail with a pytest-timeout after 40 to 60 seconds.
- The EventBus suite takes about seven minutes in total, which slows every EventBus change and hides real regressions behind known failures.
- The cause is unknown: possibilities include an SSE stream that never ends in the test client, a missing idle-timeout setting for these tests, or a stale test scenario.

## Reason for Change
A suite that always contains known failures cannot gate changes, and the long runtime discourages running it. The tests were last edited in a stale-scenario cleanup commit, which suggests the scenarios may not match current behavior.

## Implementation Intent
- First reproduce one failing test in isolation and find where it blocks (for example by dumping stacks on timeout).
- Fix the test setup (idle timeout, bounded streams, or the client lifecycle) or the stale scenario; change production code only if the investigation shows an actual defect in the subscribe path.

## Target Files or Areas
- `tests/eventbus/test_eventbus_subscribe_transition.py`
- Possibly `tests/eventbus/eventbus_helpers.py` and `scripts/eventbus/subscribe_route.py` if the cause lies there

## Required Changes
- Identify why each of the four tests blocks.
- Make each test finish quickly and deterministically, without arbitrary sleeps.
- Remove any deselection or skip added elsewhere for these tests once they pass.

## Constraints
- Do not weaken assertions to make a test pass; verify against the subscribe contract first.
- Do not use arbitrary `sleep` calls to fix timing, per the test skill rules.

## Acceptance Criteria
- The four tests pass in a normal run, each well under the timeout.
- The whole EventBus suite passes without deselection.
- The cause is recorded in the issue or the commit message.

## Testing Expectations
Run the module repeatedly to confirm determinism, then the whole EventBus suite and the full suite once.

## Documentation Impact
Not expected, unless the investigation finds the documented subscribe behavior differs from the code; record such a mismatch as a Known Issue.

## Out of Scope
- Redesigning SSE delivery or the subscribe route.
- Other EventBus test modules.

## Dependencies
- N/A: none. Independent of the EventBus authentication work.

## Unresolved Questions
- Whether the tests ever passed in the current environment (unknown; check the commit that last edited the module).
- Whether the cause is the test client's handling of an unbounded stream (unknown).

## AI Implementation Instruction
Reproduce first; do not edit assertions before you know why a test blocks. Keep changes within the transition test module and the shared EventBus test helper unless a production defect is demonstrated, and stop to report if so.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261008-111323_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-115806
- **Related target files**: `tests/eventbus/test_eventbus_subscribe_transition.py`
