# Correct subscription replay boundaries, batching, and reconnect semantics

## Priority
High

## Summary
The EventBus subscription replay path (unfiltered historical replay before switching to live SSE delivery) lacks deterministic ordering/pagination and a consistently defined resume boundary across `since_seq`, consumer offsets, and Last-Event-ID, risking duplicated or lost events across reconnects.

## Background
N/A: covered by Summary — this is a direct code-level finding in `scripts/eventbus/subscribe_route.py`'s replay/reconnect path, not derived from a prior design decision document.

## Problem
An unfiltered subscription's historical replay currently relies on offset-based pagination without a defined deterministic order, so more than one replay batch can emit an event more than once or skip one. Separately, the point at which the replay loop stops and hands off to live broker delivery is not guaranteed to avoid a gap (events published during replay could be missed) or an overlap (events could be delivered twice). Finally, three different resume inputs (`since_seq`, consumer offsets, Last-Event-ID) are not defined against one shared boundary convention, so which sequence a reconnect actually resumes from can differ depending on which input the client used.

## Reason for Change
These tasks share the same replay-position model and subscription loop. Implementing them separately would risk inconsistent sequence semantics and duplicate fixes.

## Implementation Intent
Create one deterministic replay algorithm that terminates, preserves sequence continuity, and transitions safely to live delivery. Centralize resume-position calculation behind one testable function so `since_seq`, consumer offsets, and Last-Event-ID all resolve through the same boundary convention, rather than each being interpreted independently at its call site.

## Target Files or Areas
- `scripts/eventbus/subscribe_route.py`
- `tests/eventbus/test_eventbus_subscribe.py`
- `docs/eventbus`

## Required Changes
- Add deterministic ordering and bounded pagination to the unfiltered replay query.
- Prefer keyset pagination based on the last emitted sequence number instead of offset pagination.
- Capture a replay ceiling at subscription start so events published during replay are handled by the live-delivery path.
- Ensure the replay loop terminates and transitions to live broker delivery.
- Define resume positions consistently as the last successfully processed sequence number.
- Set the Last-Event-ID-derived boundary so the next sequence is included.
- Align `since_seq`, consumer offsets, and Last-Event-ID semantics.
- Define each resume input as either the last processed sequence or the next sequence to read.
- Document the precedence rule.
- Centralize resume-position calculation in a testable function.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- An unfiltered subscription with more than one replay batch emits each historical event at most once.
- The replay loop terminates and switches to live delivery.
- Tests cover zero rows, fewer than one batch, exactly one batch, and multiple batches.
- Tests cover events published while historical replay is in progress.
- When Last-Event-ID is `N`, replay starts with the first available event whose sequence is greater than `N`.
- No event is lost or duplicated across reconnect boundaries.
- Boundary tests cover zero, one, the current maximum sequence, and a value above the current maximum.
- The same boundary convention is used for all resume inputs.
- Conflicting inputs have deterministic documented behavior.
- Tests cover every precedence combination and verify no loss.

## Testing Expectations
Add or update unit, integration, and regression tests for all affected boundaries (see Acceptance Criteria). Run the relevant test suites, static analysis, and type checks.

## Documentation Impact
Update the active EventBus design documents (`docs/eventbus`) to describe the replay boundary/precedence convention once implementation evidence is available; do not update ahead of the code change.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
N/A: none — this issue is independent of the other issues in this batch.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Keep changes scoped to the replay/reconnect boundary logic in `scripts/eventbus/subscribe_route.py` and its resume-position calculation; do not rewrite unrelated route handlers. Preserve existing public request/response shapes unless a boundary fix explicitly requires a change. Confirm that failure paths do not expose credentials, tokens, payloads, or sensitive configuration. Stop and report if any of the resume-input precedence rules turn out to be ambiguous in the current code rather than guessing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102225
- **Related target files**: scripts/eventbus/subscribe_route.py, tests/eventbus/test_eventbus_subscribe.py, docs/eventbus
