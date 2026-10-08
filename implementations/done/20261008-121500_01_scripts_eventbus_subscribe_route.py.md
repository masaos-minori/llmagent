## Goal
Make the subscribe route replay every event it must deliver on reconnect, for every resume source and for backlogs larger than one batch, with no duplicate inside one connection (REQ-001, REQ-002, REQ-004 of the Plan).

## Scope
- Change only the lower-bound resolution, the replay batch loop, the live-phase duplicate filter, and the comment about the resume position in the subscribe route.

## Assumptions
- The resume helper returns the first seq to deliver (lowest unacked seq, else stored offset + 1); `since_seq=N` means events with seq > N; Last-Event-ID L means events with seq > L (start at L+1).
- The consumer's broker subscription is created before replay, so events published during replay are queued for the live phase.
- The user confirmed the old expectation for Last-Event-ID is not intentional and that no consumer depends on the current behavior.

## Design decisions
- Resolve one exclusive lower bound (events with seq greater than it) for all three sources: since_seq as is; resume position minus one; Last-Event-ID as is.
- Track whether a resume position was used with a flag, so an explicit stored offset of zero does not fall through to Last-Event-ID differently than before.
- Replace the replay ceiling with a cursor holding the highest seq emitted; each batch query is "seq greater than the cursor" ordered by seq with the batch limit, and the loop ends when a batch is shorter than the batch size.
- The live phase discards events whose seq is not greater than the cursor.

## Alternatives considered
- Keep the old inclusive start and subtract one in the SQL: rejected; two meanings of the same variable caused the defect.
- Change the resume helper to return an exclusive value: rejected; its tests and documented contract describe a first-seq-to-deliver value.

## Implementation
### Target file
scripts/eventbus/subscribe_route.py

### Procedure
1. Confirm the new end-to-end tests exist and fail (procedures 02 and 03 run first).
2. Replace the start-bound assignments with the exclusive-bound resolution described in Details.
3. Rewrite the replay loop to use the cursor and the simplified query (with and without the topic filter).
4. Update the live-phase duplicate filter and the cancellation log message to use the cursor.
5. Correct the comment about the resume position.
6. Run format, lint, type, security checks and the EventBus tests.

### Method
Edit the route in place, keeping its structure: same generator, same SSE frame format, same heartbeat and idle-timeout logic, same 412 behavior for a Last-Event-ID above the maximum seq.

### Details
Lower bound: begin with since_seq; when it is zero and a consumer id is present, take the resume helper's value minus one (never below zero) and mark the resume position as used; when still unresolved and a Last-Event-ID is present, use it directly. Loop: emit each row, set the cursor to the row's seq, and continue while the batch was full. The nonlocal rebinding of the old start variable is removed. Comment: describe the resume position as the lowest unacked seq at or below the stored offset, else the stored offset plus one, converted here to an exclusive bound.

## Compatibility considerations
- Public behavior of since_seq is unchanged; reconnecting consumers may now receive an event that was previously skipped (an extra redelivery, allowed by At-Least-Once).
- The replay route and the ACK/NACK paths are not touched.

## Security considerations
- No change to authentication or topic authorization checks.

## Rollback considerations
- Revert the commit; no data or schema change.

## Validation plan
- `uv run ruff format scripts/eventbus/subscribe_route.py`, `uv run ruff check scripts/eventbus/subscribe_route.py`, `uv run mypy --no-namespace-packages scripts/` (tracer-module errors are pre-existing), `uv run bandit scripts/eventbus/subscribe_route.py`, `PYTHONPATH=scripts uv run lint-imports` (one pre-existing violation).
- `uv run pytest tests/eventbus/test_eventbus_subscribe.py tests/eventbus/test_eventbus_restart_resume.py -q --timeout=60`, then the EventBus suite.

## Completion criteria
- The new end-to-end tests pass; a backlog larger than the batch is replayed completely once and in order; no duplicate at the replay-to-live boundary; since_seq semantics unchanged (REQ-001, REQ-002, REQ-004).

## Out of scope
- ACK/NACK/offset writes, the replay route, the resume helper, authentication, deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Resolve one exclusive lower bound for all sources | Completed | 20261008-122614 | 20261008-122614 |  |
| 2 | Rewrite the replay loop and live-phase filter with a cursor | Completed | 20261008-122614 | 20261008-122614 |  |
| 3 | Correct the comment | Completed | 20261008-122614 | 20261008-122614 |  |
| 4 | Run format, lint, type, security checks and the EventBus tests | Completed | 20261008-122614 | 20261008-122614 |  |

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
- **Requirement ID**: REQ-001 (first replayed seq), REQ-002 (multi-batch replay), REQ-004 (comment)
- **Source issue**: issues/20261007-164638_ebresume01_fix-off-by-one-in-eventbus-subscribe-resume-position.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-120658_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-121500
- **Related target files**: scripts/eventbus/subscribe_route.py