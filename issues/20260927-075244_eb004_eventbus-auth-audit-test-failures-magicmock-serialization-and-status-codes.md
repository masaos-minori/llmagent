# EventBus auth audit test failures MagicMock serialization and status codes

## Priority
High

## Summary
`tests/eventbus/test_eventbus_auth.py` has 5 failures: one genuine production bug (`TypeError: Type is not JSON serializable: MagicMock` inside `scripts/eventbus/audit.py:126`) and four status-code mismatches (403 vs 200, 500 vs 200) in auth/audit-record tests.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
- `TypeError: Type is not JSON serializable: MagicMock` raised from `scripts/eventbus/audit.py:126` — the audit-logging code attempts to JSON-serialize a value that is (or resolves to, via a test double) a `MagicMock`, in a consumer-identity/topic-authorization audit-record test.
- `TestRequireConsumerIdentityTopicSemantics::test_non_empty_topic_restriction_is_enforced_and_returned`: `assert 200 == 403`
- `TestAuditRecordValidation::test_topic_authorization_rejection_produces_structured_audit_record`: `assert 200 == 403`
- `TestReplayAuth::test_replay_with_valid_operator_token`: `assert 500 == 200`
- `TestDlqListAuth::test_dlq_list_with_valid_operator_token`: `assert 500 == 200`

The MagicMock-serialization failure and the two 403-vs-200 failures may share a cause (both relate to consumer-identity/topic authorization rejection producing an audit record); the two 500-vs-200 failures (valid operator token unexpectedly causing a server error) look like a separate cause.

## Reason for Change
A 500 on a *valid* operator token request is a genuine reliability bug (a previously-working authenticated request now errors). The MagicMock-serialization `TypeError` indicates the audit-logging code path can crash on certain inputs in production, not just in tests, if a non-JSON-serializable value reaches it.

## Implementation Intent
Investigate the two clusters separately: (1) why valid-operator-token requests to replay/dlq-list now 500 instead of 200 — likely an unhandled exception in the request path since a valid, this-should-succeed case fails; (2) why topic-authorization-rejection audit-record construction can receive/serialize a `MagicMock` and why the resulting response status is 200 instead of the expected 403.

## Target Files or Areas
- `scripts/eventbus/audit.py` (confirmed: line 126, JSON-serialization of audit record)
- EventBus auth/consumer-identity route handlers (confirm exact path)
- `tests/eventbus/test_eventbus_auth.py`

## Required Changes
- Capture the full traceback (not just final assertion) for the two 500-vs-200 failures to find the actual unhandled exception.
- Fix `audit.py`'s serialization to either avoid receiving non-serializable values, or serialize defensively (e.g. `default=str`), after confirming why a `MagicMock` reaches it (test double leakage vs. genuine production input).
- Fix the topic-authorization-rejection status-code handling so a rejection returns 403 as expected.

## Constraints
Do not broadly catch-and-suppress exceptions in the auth path merely to avoid the 500 — find and fix the actual unhandled exception.

## Acceptance Criteria
- All 5 listed tests pass.
- The audit-logging path no longer crashes with `TypeError` on the previously-failing scenario.

## Testing Expectations
Run `tests/eventbus/test_eventbus_auth.py`; run full suite once after the fix.

## Documentation Impact
N/A: unless the auth/audit-record contract changes, in which case update relevant eventbus auth documentation (Needs confirmation on exact doc path).

## Out of Scope
Other unrelated eventbus failing tests (tracked as separate issues).

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: the full traceback behind the two 500-vs-200 failures (only the final assertion was captured in this investigation, not the underlying exception).

## AI Implementation Instruction
Reproduce each of the 5 failures with full tracebacks (`--tb=long`) before fixing — the 500-vs-200 cases in particular need the actual server-side exception, not just the status code, to diagnose correctly.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/eventbus/test_eventbus_auth.py, scripts/eventbus/audit.py
