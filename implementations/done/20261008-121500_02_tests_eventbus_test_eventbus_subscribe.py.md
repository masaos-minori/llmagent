## Goal
Add failing end-to-end tests for the three resume sources and multi-batch replay, correct the stale Last-Event-ID expectation, and replace the two placeholder tests (REQ-001, REQ-002, REQ-003 of the Plan).

## Scope
- Edit the subscribe test module only; reuse its existing fixtures and helpers (client with consumer token, publisher client helper, event builder, SSE id extractor).

## Assumptions
- The helper that reads at most N frame ids closes the response; the fixture sets a short SSE idle timeout so streams end.
- The user confirmed the old Last-Event-ID expectation (first seq 3 for header value 1) is not intentional: the correct first seq is 2.

## Design decisions
- Tests assert exact ordered seq lists, not just the first element, so skips and duplicates both fail.
- For multi-batch tests, set a small replay batch size on the running app's configuration object inside the test.
- Offset-based tests acknowledge events through the database helper used by the restart tests, then reconnect through the endpoint with a consumer id.

## Alternatives considered
- Use real SSE streaming through the endpoint rather than calling the helper: required, since the defect is in the route.

## Implementation
### Target file
tests/eventbus/test_eventbus_subscribe.py

### Procedure
1. Read the helpers and the existing resume tests.
2. Correct the Last-Event-ID fallback test to expect the next seq after the header value (seq 2 for header 1).
3. Implement the two placeholder tests: reconnect with a stored consumer offset resumes at the next seq; since_seq takes precedence over the consumer offset.
4. Add tests: out-of-order acknowledgement resumes at the lowest unacked event (included); Last-Event-ID equal to the max seq yields no events and above max returns 412; a backlog larger than the batch size (small batch) is replayed completely, once, in order, for since_seq zero, since_seq positive, and Last-Event-ID; the replay-to-live boundary emits no duplicate.
5. Run the new tests and confirm the ones covering the defect fail before the route fix.

### Method
Publish events with the publisher client; acknowledge with the database helper through the app state; read frame ids with the existing extractor using a larger read count than the number of events so truncation is visible; compare with exact expected lists.

### Details
- Tests only; no production change in this document.

## Compatibility considerations
- Fake tokens only.

## Security considerations
- Revert the commit.

## Rollback considerations
- `uv run ruff format` and `ruff check` on the file; `uv run pytest tests/eventbus/test_eventbus_subscribe.py -q --timeout=60` (new tests fail before the fix and pass after).

## Validation plan
- The corrected expectation, two real tests, and the added tests exist; they fail for the stated reasons before the fix and pass after it (REQ-003).

## Completion criteria
- Other test modules, including the timing-out transition module.

## Out of scope
REQ-001 (resume sources), REQ-002 (multi-batch), REQ-003 (tests)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|


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
- **Requirement ID**: tests/eventbus/test_eventbus_subscribe.py
- **Source issue**: issues/20261007-164638_ebresume01_fix-off-by-one-in-eventbus-subscribe-resume-position.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-120658_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-121500
- **Related target files**: | 1 | Correct the Last-Event-ID expectation and implement the two placeholder tests | Pending | — | — | |
| 2 | Add out-of-order, boundary, multi-batch, and handoff tests | Pending | — | — | |
| 3 | Confirm failures before the route fix and passes after | Pending | — | — | |
