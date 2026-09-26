# EventBus subscribe reconnect delivers duplicate events

## Priority
High

## Summary
`tests/eventbus/test_eventbus_subscribe_transition.py::TestReconnectResumeSemantics::test_since_seq_precedence_over_consumer_offset` fails because events 4 and 5 are delivered to both the original and a reconnected subscription, violating the expected "no duplicate events between subscriptions" invariant for `since_seq`-based reconnect.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
`AssertionError: No duplicate events between subscriptions` — `{1,2,3,4,5}.isdisjoint({4,5})` is `False`, i.e. events 4 and 5 appear in both the first subscription's received set and the reconnected subscription's received set. The test asserts `since_seq` should take precedence over the consumer's stored offset on reconnect (T-7 semantics per the test's docstring), but the resume logic appears to replay events already delivered before the reconnect.

## Reason for Change
Duplicate delivery on reconnect is a correctness bug for exactly-once/at-least-once consumer semantics — a consumer using `since_seq` to resume could reprocess events it already handled, which is the class of bug the DLQ/idempotency mechanisms elsewhere in eventbus are meant to guard against.

## Implementation Intent
Read the subscribe/reconnect resume logic (offset vs. `since_seq` precedence) to determine why events already delivered before a reconnect are replayed when `since_seq` is supplied. Confirm whether this is a genuine precedence-ordering bug (offset checked before/after `since_seq` incorrectly) or a test-setup issue (e.g. the test's `since_seq` value is set too low, unintentionally requesting replay of already-seen events).

## Target Files or Areas
- EventBus subscribe/SSE reconnect-resume logic (confirm exact path, likely `scripts/eventbus/` subscribe route or offset-resolution helper)
- `tests/eventbus/test_eventbus_subscribe_transition.py`

## Required Changes
- Trace the exact `since_seq` value the test passes and the offset the consumer would otherwise have stored, to confirm whether the test itself requests overlap or the resume logic ignores `since_seq` precedence.
- Fix the resume logic (or the test, if it is the one at fault) so the documented T-7 precedence holds.

## Constraints
Preserve existing offset-based resume behavior for the case where `since_seq` is not supplied — this fix must not change default (non-`since_seq`) reconnect behavior.

## Acceptance Criteria
- The listed test passes.
- No duplicate delivery occurs for the `since_seq`-precedence scenario specifically.

## Testing Expectations
Run `tests/eventbus/test_eventbus_subscribe_transition.py`; run full suite once after the fix.

## Documentation Impact
If resume/precedence semantics change, update the eventbus subscribe/reconnect documentation describing `since_seq` vs. consumer-offset precedence (confirm exact doc path, e.g. `docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md`'s "since_seq Precedence" section).

## Out of Scope
Other unrelated eventbus failing tests (tracked as separate issues).

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: whether the test's own `since_seq` value is set correctly to test only the intended precedence scenario, or whether it inadvertently requests replay of already-delivered events.

## AI Implementation Instruction
Read the exact `since_seq` value asserted in the test and the resume-resolution code path before concluding this is a production bug — confirm the test itself is requesting a genuinely-non-overlapping replay window.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/eventbus/test_eventbus_subscribe_transition.py
