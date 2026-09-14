# Define publish durability, recovery, and operational observability

## Priority
Medium

## Summary
Both the JSONL append and the live broker notification happen after the database commit in the publish path, but partial failures in either step after that commit are not currently observable or documented as recoverable, risking silent data/notification loss without changing the documented publish-success criterion.

## Background
N/A: covered by Summary — this is a direct code-level finding in the publish path's post-commit behavior, not derived from a prior design decision document.

## Problem
It is not documented (or verified) whether SQLite or the JSONL file is the canonical event store; if JSONL append fails after a successful database commit, there is currently no metric or health signal surfacing that failure, nor a defined reconciliation/rebuild mechanism if JSONL turns out to be derived data. Similarly, if the live broker notification fails after a successful commit, there is no metric for that failure, and it is not verified that subscribers can still recover the missed notification through SQLite-backed replay.

## Reason for Change
JSONL append and broker notification both occur after database commit. Their failure handling depends on the same canonical-store and recovery decision.

## Implementation Intent
Make post-commit partial failures observable and recoverable without changing the documented publish success criterion (database commit) unintentionally.

## Target Files or Areas
- `scripts/eventbus/publish_route.py`
- `docs/eventbus`
- `tests/eventbus/test_eventbus_publish.py`
- `scripts/eventbus/broker.py`

## Required Changes
- Declare SQLite or JSONL as the canonical event store.
- Add a metric or health signal for JSONL append failures.
- Provide a deterministic reconciliation or rebuild mechanism if JSONL is derived data.
- Document behavior for disk-full and permission failures.
- Add a metric for committed events whose live broker notification failed.
- Verify that subscribers recover missed live notifications through SQLite replay.
- Document why database commit success remains the publish success criterion.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- The canonical store is explicitly documented.
- JSONL write failures are observable without parsing unstructured logs.
- A tested recovery procedure can restore derived JSONL data when required.
- Broker notification failures increment an observable metric.
- A subscriber can recover the committed event through replay.
- Integration tests cover notification failure after a successful insert.

## Testing Expectations
Add or update unit, integration, and regression tests for all affected boundaries (see Acceptance Criteria), including integration tests for notification failure after a successful insert. Run the relevant test suites, static analysis, and type checks.

## Documentation Impact
Update `docs/eventbus`'s publish/durability documentation to state the canonical store and the publish success criterion only after implementation evidence is available.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
N/A: none — this issue is independent of the other issues in this batch.

## Unresolved Questions
Whether SQLite or JSONL is intended as canonical is itself one of this issue's own Required Changes (a decision to make and document during implementation), not a prerequisite to filing it.

## AI Implementation Instruction
Keep changes scoped to publish-path durability/observability; do not rewrite unrelated broker or subscribe logic beyond what the recovery/metric additions require. Confirm that failure paths do not expose credentials, tokens, payloads, or sensitive configuration. Stop and report if declaring the canonical store requires a decision beyond what the current code/tests can confirm, rather than guessing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102458
- **Related target files**: scripts/eventbus/publish_route.py, docs/eventbus, tests/eventbus/test_eventbus_publish.py, scripts/eventbus/broker.py
