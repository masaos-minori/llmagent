# Correct pagination consistency claims and make the DLQ index test fail on a missing index

## Priority
Medium

## Summary
Make the DLQ pagination test state the consistency the API actually provides, and rewrite the DLQ index test so it checks the production schema and the production query without creating the index it is meant to find missing.

## Background
Source: `memo-issue.md` item 04, re-verified against current source on 2026-10-28. The memo's paths (`tests/test_eventbus_*.py`) are stale; the files are under `tests/eventbus/`.

- `dlq_list()` in `scripts/eventbus/dlq_route.py` computes `total` (`count_dlq`) and the page (`fetch_dlq`) inside one `run_with_db_lock` call. Consistency is therefore request-local; two HTTP requests share no cursor, snapshot token or sequence boundary. `Explicit in code`.
- `tests/eventbus/test_eventbus_dlq_pagination.py` says page A (offset 0) and page 2 (offset 2) "must come from one consistent snapshot" and that a torn snapshot "would let pages skip or double-count". The test issues two sequential requests with no concurrent mutation, so it can only show that two disjoint windows do not overlap. `Explicit in code`.
- `tests/eventbus/test_eventbus_dlq_index.py::test_dlq_query_uses_index` runs `CREATE INDEX idx_events_dlq_at` when the index is absent from the test database, so a schema regression that drops the index is repaired by the test. `Explicit in code`.
- The same test explains `SELECT event_id, seq, topic, payload, producer, published_at ... ORDER BY dlq_at DESC`, while `fetch_dlq()` in `scripts/eventbus/event_repo.py` runs `SELECT seq, event_id, topic, producer, published_at, dlq_requeue_count, dlq_at ... WHERE dlq_at IS NOT NULL ORDER BY seq LIMIT ? OFFSET ?`. The plan checked is not the production plan. `Explicit in code`.
- The test publishes with `Bearer test-token`, the shared `auth_token`, which holds only control-plane roles, and ignores the response, so the publish most likely returns 403 and no row exists. `Strongly implied by code` (the response is not asserted).
- The canonical schema defines `idx_events_dlq_at` and `idx_events_dlq_seq` (`scripts/eventbus/schema.sql`). `Explicit in code`.
- Whether `tests/eventbus/test_eventbus_replay_pagination.py` makes a snapshot claim: no such wording was found. `Needs confirmation`.

## Problem
A test names a cross-request guarantee the API does not provide, and the index regression test cannot fail on the regression it exists for and examines a different query from the production one.

## Reason for Change
The pagination wording can lead a client author to rely on snapshot semantics that do not exist, and the index test gives false assurance about the DLQ read path. Neither is an outage; severity is Medium (testability and an ambiguous contract). Nothing makes the change time-sensitive.

## Implementation Intent
Decide the pagination contract explicitly and make the tests and API documentation say exactly that: request-local consistency (what the code does) unless the owner wants cross-page snapshots. For the index, assert the schema shape and the real query plan separately, without mutating the database.

## Target Files or Areas
- `tests/eventbus/test_eventbus_dlq_pagination.py`
- `tests/eventbus/test_eventbus_replay_pagination.py`
- `tests/eventbus/test_eventbus_dlq_index.py`
- `scripts/eventbus/dlq_route.py`, `scripts/eventbus/event_repo.py` (only if a snapshot mechanism is chosen)
- `docs/24_eventbus/eventbus_04_dlq_endpoint.md` and `eventbus_11_replay_endpoint.md` (the pagination wording)

## Required Changes
- Choose the contract: request-local consistency (recommended, matches the code) or a cross-page snapshot (cursor, boundary token, expiry and invalid-token behavior).
- Rename and re-word the pagination test accordingly; add a concurrent-mutation test that matches the chosen contract.
- In the index test: remove `CREATE INDEX`, fail when a required canonical index is absent, run `EXPLAIN QUERY PLAN` on the exact SQL of `fetch_dlq()`, and keep schema-shape assertions separate from plan assertions.
- Remove or fix the ignored publish (use a publisher token and assert success, or drop the publish).
- Check the replay pagination test and docs for the same wording.

## Constraints
- Do not change the DLQ response shape (`total`, `limit`, `offset`, `items`) unless a snapshot contract is chosen.
- Production query text must not be changed to satisfy the test.

## Acceptance Criteria
- No test calls independent requests one snapshot unless a snapshot mechanism exists.
- The API documentation states the consistency boundary.
- The index test fails when `idx_events_dlq_at` or `idx_events_dlq_seq` is removed from the schema it examines, and never creates an index.
- The plan assertion uses the same SQL (or the same function) as the production query.

## Testing Expectations
- Response-local count/item consistency test.
- Concurrent mutation test matching the chosen contract (explicit synchronization, no sleeps).
- Index regression test that drops the index in a throwaway database and asserts failure.
- `uv run pytest tests/eventbus`, ruff and mypy on changed files; `tools/check_docs_consistency.py --domain eventbus` if docs change.

## Documentation Impact
Yes, small: state the pagination consistency boundary (current behavior only) in the DLQ and replay endpoint docs.

## Out of Scope
- Keyset pagination or any new endpoint parameters unless the snapshot option is chosen.
- Changing DLQ ordering.
- Other query-plan tests.

## Dependencies
- Coordinate with the archived `plans/done/20261028-093155_ebdurable003_define-publish-dlq-durability.md` and `plans/done/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md`, whose pending procedures edit other EventBus test files but not these three; no ordering is required.

## Unresolved Questions
- Which pagination contract does the owner want: request-local or cross-page snapshot? `Needs confirmation` (owner decision).
- Does the replay pagination test or doc make the same claim? `Needs confirmation`.
- Does the publish in the index test fail today? `Needs confirmation`: assert the response before deciding.

## AI Implementation Instruction
Change tests and wording first; add a snapshot mechanism only if the owner chooses it. Do not edit the schema or the production query to make a test pass. If the contract choice is unclear, stop and report instead of choosing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261028-122307
- **Related target files**: `tests/eventbus/test_eventbus_dlq_pagination.py`, `tests/eventbus/test_eventbus_replay_pagination.py`, `tests/eventbus/test_eventbus_dlq_index.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/event_repo.py`, `docs/24_eventbus/eventbus_04_dlq_endpoint.md`, `docs/24_eventbus/eventbus_11_replay_endpoint.md`
